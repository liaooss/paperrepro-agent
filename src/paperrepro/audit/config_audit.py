"""Consistency audit: does the code do what the paper says it does?

Deterministic and evidence-first: every row quotes the paper sentence and the
code line. Numbers are compared with a relative tolerance because "1e-4" and
"0.0001" are the same hyperparameter.

A mismatch is not an accusation. It is a question to ask the authors, and the
report phrases it that way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..models import PaperDoc, RepoScan

__all__ = ["ParamCheck", "audit_parameters", "AUDITABLE"]


@dataclass
class ParamCheck:
    param: str
    paper_value: str
    code_value: str
    status: str  # MATCH | MISMATCH | PAPER_ONLY | CODE_ONLY
    paper_ref: str = ""
    code_ref: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "param": self.param,
            "paper_value": self.paper_value,
            "code_value": self.code_value,
            "status": self.status,
            "paper_ref": self.paper_ref,
            "code_ref": self.code_ref,
            "note": self.note,
        }


_NUM = r"(\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"

# Only files that actually configure an experiment are worth comparing. A
# documentation page mentioning "batch size 20" is not the released setting, and
# neither is a generic trainer utility that happens to contain the word "train".
_CODE_FILE_HINT = re.compile(r"(^|/)(config|configs|conf|hparams|hyperparams|args|settings)[^/]*\.py$", re.IGNORECASE)
_SKIP_PATH = re.compile(r"(^|/)(docs?|tests?|benchmarks?|examples?|tests?)/", re.IGNORECASE)

# Values outside these ranges are almost certainly a different quantity that
# happens to share the name. Applied to both sides.
_PLAUSIBLE: dict[str, tuple[float, float]] = {
    "learning_rate": (1e-8, 10.0),
    "batch_size": (2.0, 65536.0),
    "epochs": (1.0, 100000.0),
    "weight_decay": (0.0, 1.0),
    "dropout": (0.0, 1.0),
}

# name -> (paper pattern, code pattern, kind)
AUDITABLE: dict[str, tuple[str, str, str]] = {
    "learning_rate": (
        r"(?:learning\s+rate|\blr\b)\D{0,25}?" + _NUM,
        r"(?:learning_rate|\blr\b|\bLR\b)\s*[:=]\s*" + _NUM,
        "number",
    ),
    "batch_size": (
        r"batch\s*size\D{0,15}?" + _NUM,
        r"batch_size\s*[:=]\s*" + _NUM,
        "number",
    ),
    "epochs": (
        r"(?:epochs?|training\s+steps)\D{0,12}?" + _NUM,
        r"epochs?\s*[:=]\s*" + _NUM,
        "number",
    ),
    "weight_decay": (
        r"weight\s+decay\D{0,15}?" + _NUM,
        r"weight_decay\s*[:=]\s*" + _NUM,
        "number",
    ),
    "dropout": (
        r"dropout\D{0,15}?" + _NUM,
        r"dropout(?:_rate)?\s*[:=]\s*" + _NUM,
        "number",
    ),
    "optimizer": (
        r"\b(AdamW|Adam|SGD|RMSprop|Adagrad|LAMB)\b",
        r"optimizer\s*[:=]\s*['\"]?(\w+)",
        "name",
    ),
}


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _paper_hits(doc: PaperDoc) -> dict[str, tuple[str, str]]:
    hits: dict[str, tuple[str, str]] = {}
    for heading, body in doc.sections.items():
        for param, (pattern, _code_pattern, _kind) in AUDITABLE.items():
            if param in hits:
                continue
            for match in re.finditer(pattern, body, re.IGNORECASE):
                raw = match.group(1).strip()
                if param == "learning_rate" and not re.search(r"[.eE]", raw):
                    # 'learning rate and beta 1' is not a learning rate of 1.
                    continue
                bounds = _PLAUSIBLE.get(param)
                if bounds is not None:
                    try:
                        value = float(raw)
                    except ValueError:
                        continue
                    if not (bounds[0] <= value <= bounds[1]):
                        continue
                hits[param] = (raw, f"{heading}: \"{match.group(0)[:90]}\"")
                break
    return hits


def _config_like(f) -> bool:
    if _SKIP_PATH.search(f.path):
        return False
    if f.lang == "config":
        return True
    if f.lang != "python":
        return False
    return bool(_CODE_FILE_HINT.search(f.path))


def _code_hits(scan: RepoScan) -> dict[str, tuple[str, str]]:
    hits: dict[str, tuple[str, str]] = {}
    ordered = sorted(
        (f for f in scan.files if f.text and _config_like(f)),
        key=lambda f: (0 if f.lang == "config" else 1, f.path),
    )
    for f in ordered:
        for param, (_paper_pattern, pattern, _kind) in AUDITABLE.items():
            if param in hits:
                continue
            for match in re.finditer(pattern, f.text, re.IGNORECASE):
                raw = match.group(1).strip()
                if param == "learning_rate" and not re.search(r"[.eE]", raw):
                    # 'learning rate and beta 1' is not a learning rate of 1.
                    continue
                bounds = _PLAUSIBLE.get(param)
                if bounds is not None:
                    try:
                        value = float(raw)
                    except ValueError:
                        continue
                    if not (bounds[0] <= value <= bounds[1]):
                        continue
                hits[param] = (raw, f"{f.path}:{_line_of(f.text, match.start())}")
                break
    return hits


def _same_number(a: str, b: str) -> bool:
    try:
        left, right = float(a), float(b)
    except ValueError:
        return a.strip().lower() == b.strip().lower()
    if left == right:
        return True
    scale = max(abs(left), abs(right), 1e-12)
    return abs(left - right) / scale <= 0.01


def audit_parameters(doc: PaperDoc, scan: RepoScan) -> list[ParamCheck]:
    """Compare every auditable hyperparameter the paper states with the code."""
    paper = _paper_hits(doc)
    code = _code_hits(scan)

    checks: list[ParamCheck] = []
    for param in AUDITABLE:
        kind = AUDITABLE[param][2]
        p_val, p_ref = paper.get(param, ("", ""))
        c_val, c_ref = code.get(param, ("", ""))
        if not p_val and not c_val:
            continue
        if p_val and not c_val:
            status, note = "PAPER_ONLY", "the paper states it but no config value was found"
        elif c_val and not p_val:
            status, note = "CODE_ONLY", "the code sets it but the paper never states it"
        elif kind == "number":
            status = "MATCH" if _same_number(p_val, c_val) else "MISMATCH"
            note = "" if status == "MATCH" else "the paper and the code disagree"
        else:
            status = "MATCH" if p_val.strip().lower() == c_val.strip().lower() else "MISMATCH"
            note = "" if status == "MATCH" else "different optimiser family"
        checks.append(
            ParamCheck(
                param=param,
                paper_value=p_val,
                code_value=c_val,
                status=status,
                paper_ref=p_ref,
                code_ref=c_ref,
                note=note,
            )
        )
    return checks
