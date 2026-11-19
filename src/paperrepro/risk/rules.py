"""Deterministic risk rules.

Every rule is a pure function of the scan result: no LLM, no network, no
heuristics that change run to run.  That is what makes two runs comparable and
lets a reviewer argue with a specific rule instead of with "the AI".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ..models import Claim, Evidence, Finding, PaperDoc, RepoScan

__all__ = ["run_rules", "RULES", "AUTHOR_BLOCKER_RULES"]

# Rules whose fix requires the authors, not the reader.  These drive verdict R1.
AUTHOR_BLOCKER_RULES = {"RC04", "RC05"}

RULES: list[tuple[str, str, str]] = [
    ("RC01", "No dependency manifest", "major"),
    ("RC02", "Dependencies are not version-pinned", "major"),
    ("RC03", "Absolute filesystem paths in source", "major"),
    ("RC04", "Checkpoints referenced but not released", "blocker"),
    ("RC05", "Dataset requires manual or restricted acquisition", "blocker"),
    ("RC06", "No random-seed control", "minor"),
    ("RC07", "No executable entry point", "major"),
    ("RC08", "README does not say how to install or run", "minor"),
    ("RC09", "No configuration file; hyperparameters are hard-coded", "minor"),
    ("RC10", "No tests", "info"),
    ("RC11", "Incomplete code markers on the execution path", "minor"),
    ("RC12", "GPU requirement undocumented", "minor"),
    ("RC13", "Imports not declared in any manifest", "major"),
    ("RC14", "Pipeline exists only as notebooks", "major"),
    ("RC15", "No licence file", "info"),
    ("RC16", "No README", "major"),
    ("RC17", "Paper claims with no code counterpart", "major"),
]

_MANUAL_DATA = re.compile(
    r"(google\s*drive|drive\.google|baidu|pan\.baidu|onedrive|dropbox|"
    r"request\s+access|upon\s+request|contact\s+the\s+authors|send\s+an\s+email|"
    r"registration|sign\s+the\s+form|fill\s+(in|out)\s+the\s+form)",
    re.IGNORECASE,
)
_IMPORT = re.compile(r"^[ \t]*(?:from[ \t]+([A-Za-z_]\w*)|import[ \t]+([A-Za-z_]\w*(?:[ \t]*,[ \t]*[A-Za-z_]\w*)*))", re.MULTILINE)
_GPU_USE = re.compile(r"(cuda|\.to\(\s*device|torch\.device|nvidia-smi|DataParallel|DistributedDataParallel)")
_GPU_DOC = re.compile(r"\b(gpu|cuda|a100|v100|h100|rtx|nvidia)\b", re.IGNORECASE)
_UNPINNED = re.compile(r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?\s*$")

# Import name -> distribution name, for the cases where they differ.
_IMPORT_ALIASES = {
    "yaml": "pyyaml",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "pil": "pillow",
    "bs4": "beautifulsoup4",
    "crypto": "pycryptodome",
    "attr": "attrs",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "torch": "torch",
    "torchvision": "torchvision",
    "jax": "jax",
    "flash_attn": "flash-attn",
}


def _ev(kind: str, ref: str, text: str = "", detail: str = "") -> Evidence:
    return Evidence(kind=kind, ref=ref, text=text, detail=detail)


def _finding(rule_id: str, title: str, severity: str, detail: str, evidence: list[Evidence], author_dependent: bool = False) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=title,
        severity=severity,
        detail=detail,
        evidence=evidence,
        author_dependent=author_dependent,
    )


def _rc01(scan: RepoScan) -> list[Finding]:
    if scan.manifests:
        return []
    return [
        _finding(
            "RC01",
            "No dependency manifest",
            "major",
            "No requirements.txt, environment.yml, pyproject.toml or Dockerfile. The environment "
            "cannot be rebuilt from the release, so version drift is guaranteed.",
            [_ev("code", scan.readme_path or "repository root")],
        )
    ]


def _line_text(scan: RepoScan, ref: str) -> str:
    """Source line behind a 'path:line' reference, for quoting in a finding."""
    path, _, line_s = ref.rpartition(":")
    try:
        line_no = int(line_s)
    except ValueError:
        return ""
    for f in scan.files:
        if f.path == path and f.text:
            lines = f.text.splitlines()
            if 1 <= line_no <= len(lines):
                return lines[line_no - 1].strip()[:160]
    return ""


def _rc02(scan: RepoScan) -> list[Finding]:
    unpinned: list[tuple[str, str]] = []
    for name, text in scan.manifests.items():
        if not name.lower().endswith(("requirements.txt", ".txt")):
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "-", "git+", "http")):
                continue
            m = _UNPINNED.match(line)
            if m:
                unpinned.append((name, line))
    if not unpinned:
        return []
    return [
        _finding(
            "RC02",
            "Dependencies are not version-pinned",
            "major",
            f"{len(unpinned)} requirement(s) carry no version constraint, so a fresh install can "
            "resolve to versions the authors never tested."
            + (f" Example: {unpinned[0][1]}" if unpinned else ""),
            [_ev("code", name, line, "unpinned requirement") for name, line in unpinned[:4]],
        )
    ]


def _rc03(scan: RepoScan) -> list[Finding]:
    if not scan.absolute_paths:
        return []
    seen: set[str] = set()
    evidence: list[Evidence] = []
    for item in scan.absolute_paths:
        key = item["path"]
        if key in seen:
            continue
        seen.add(key)
        evidence.append(_ev("code", item["ref"], item["snippet"], f"absolute path {key}"))
        if len(evidence) >= 4:
            break
    return [
        _finding(
            "RC03",
            "Absolute filesystem paths in source",
            "major",
            f"{len(scan.absolute_paths)} hard-coded path(s) such as '{scan.absolute_paths[0]['path']}' "
            "point at the authors' machine. Any other checkout has to be patched before it runs.",
            evidence,
        )
    ]


def _rc04(scan: RepoScan) -> list[Finding]:
    if not scan.checkpoint_refs:
        return []
    evidence = [
        _ev("code", c["ref"], c["snippet"], f"missing checkpoint {c['path']}")
        for c in scan.checkpoint_refs[:4]
    ]
    names = ", ".join(sorted({c["path"].rsplit('/', 1)[-1] for c in scan.checkpoint_refs})[:3])
    return [
        _finding(
            "RC04",
            "Checkpoints referenced but not released",
            "blocker",
            f"{len(scan.checkpoint_refs)} checkpoint file(s) are referenced by path but none exist in the "
            f"repository ({names}). Evaluation cannot start without them, and only the authors can publish them.",
            evidence,
            author_dependent=True,
        )
    ]


def _rc05(scan: RepoScan) -> list[Finding]:
    if not scan.readme:
        return []
    m = _MANUAL_DATA.search(scan.readme)
    if not m:
        return []
    line_no = scan.readme.count("\n", 0, m.start()) + 1
    snippet = scan.readme.splitlines()[line_no - 1].strip()[:180]
    return [
        _finding(
            "RC05",
            "Dataset requires manual or restricted acquisition",
            "blocker",
            f"The README mentions '{m.group(0)}'. Data that must be requested, registered for or "
            "downloaded by hand cannot be part of an automated reproduction, and may not be redistributable.",
            [_ev("code", f"{scan.readme_path}:{line_no}", snippet)],
            author_dependent=True,
        )
    ]


def _rc06(scan: RepoScan) -> list[Finding]:
    if scan.seed_refs:
        return []
    return [
        _finding(
            "RC06",
            "No random-seed control",
            "minor",
            "Nothing in the repository fixes random, numpy or framework seeds, so a re-run samples a "
            "different point in the training distribution and the reported number cannot be reproduced exactly.",
            [_ev("code", "repository-wide scan")],
        )
    ]


def _rc07(scan: RepoScan) -> list[Finding]:
    if scan.entry_points:
        return []
    return [
        _finding(
            "RC07",
            "No executable entry point",
            "major",
            "No __main__ guard, CLI parser or conventional entry script (train.py, eval.py, ...). "
            "There is nothing obvious to run.",
            [_ev("code", "repository-wide scan")],
        )
    ]


def _rc08(scan: RepoScan) -> list[Finding]:
    from ..ingest.repo import has_install_hint

    if scan.readme and has_install_hint(scan):
        return []
    return [
        _finding(
            "RC08",
            "README does not say how to install or run",
            "minor",
            "No pip/conda/make invocation was found in the README, so the intended environment and "
            "command are left to the reader to guess.",
            [_ev("code", scan.readme_path or "README (missing)")],
        )
    ]


def _rc09(scan: RepoScan) -> list[Finding]:
    if scan.config_files:
        return []
    return [
        _finding(
            "RC09",
            "No configuration file; hyperparameters are hard-coded",
            "minor",
            "No YAML/JSON/TOML config or hparams module was found, so the paper's hyperparameters "
            "have to be reverse-engineered from source code edits.",
            [_ev("code", "repository-wide scan")],
        )
    ]


def _rc10(scan: RepoScan) -> list[Finding]:
    if any(Path(f.path).name.startswith("test") or "/tests/" in f"/{f.path}" for f in scan.files):
        return []
    return [
        _finding(
            "RC10",
            "No tests",
            "info",
            "Nothing verifies the implementation against known-good behaviour, so a silent bug in the "
            "pipeline looks exactly like a reproduction failure.",
            [_ev("code", "repository-wide scan")],
        )
    ]


def _rc11(scan: RepoScan) -> list[Finding]:
    if not scan.todos:
        return []
    return [
        _finding(
            "RC11",
            "Incomplete code markers on the execution path",
            "minor",
            f"{len(scan.todos)} TODO/FIXME/NotImplementedError marker(s) remain in the code; "
            "any of them may sit on the path that produces the reported numbers.",
            [_ev("code", t["ref"], t["text"]) for t in scan.todos[:4]],
        )
    ]


def _rc12(scan: RepoScan) -> list[Finding]:
    uses_gpu = any(f.text and _GPU_USE.search(f.text) for f in scan.files)
    if not uses_gpu:
        return []
    documented = bool(scan.readme and _GPU_DOC.search(scan.readme))
    if documented:
        return []
    return [
        _finding(
            "RC12",
            "GPU requirement undocumented",
            "minor",
            "The code moves tensors to CUDA but no GPU model, memory size or driver version is stated, "
            "so the compute budget of a reproduction is unbounded.",
            [_ev("code", "repository-wide scan")],
        )
    ]


def _declared_dependency_names(scan: RepoScan) -> set[str]:
    names: set[str] = set()
    for text in scan.manifests.values():
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_.\-]*", text):
            names.add(token.lower().replace("-", "_").replace(".", "_"))
    return names


def _rc13(scan: RepoScan) -> list[Finding]:
    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    local = {Path(f.path).stem for f in scan.files if f.lang == "python"}
    local |= {
        p.name for p in Path(scan.root).iterdir() if p.is_dir() and (p / "__init__.py").exists()
    }
    declared = _declared_dependency_names(scan)

    missing: dict[str, str] = {}
    for f in scan.files:
        if f.lang != "python" or not f.text:
            continue
        for m in _IMPORT.finditer(f.text):
            raw = m.group(1) or m.group(2) or ""
            for module in [x.strip() for x in raw.split(",") if x.strip()]:
                root = module.split(".")[0]
                if not root or root in stdlib or root in local:
                    continue
                distribution = _IMPORT_ALIASES.get(root, root).lower().replace("-", "_").replace(".", "_")
                if root.lower() in declared or distribution in declared:
                    continue
                if root in {"__future__", "typing_extensions"}:
                    continue
                missing.setdefault(root, f"{f.path}:{f.text.count(chr(10), 0, m.start()) + 1}")
    if not missing:
        return []
    evidence = [
        _ev("code", ref, _line_text(scan, ref), detail=f"import {name}")
        for name, ref in list(missing.items())[:4]
    ]
    return [
        _finding(
            "RC13",
            "Imports not declared in any manifest",
            "major",
            f"{len(missing)} module(s) are imported but absent from every dependency file "
            f"({', '.join(sorted(missing)[:5])}). A clean environment will fail at import time.",
            evidence,
        )
    ]


def _rc14(scan: RepoScan) -> list[Finding]:
    if not scan.notebook_only:
        return []
    refs = [f.path for f in scan.files if f.lang == "notebook"][:3]
    return [
        _finding(
            "RC14",
            "Pipeline exists only as notebooks",
            "major",
            "There is no importable Python package, only notebooks: cell order, hidden state and "
            "absolute paths make the results non-reproducible from a clean checkout.",
            [_ev("code", r) for r in refs],
        )
    ]


def _rc15(scan: RepoScan) -> list[Finding]:
    has_licence = any(
        Path(f.path).name.upper().startswith(("LICENSE", "LICENCE", "COPYING")) for f in scan.files
    )
    if has_licence:
        return []
    return [
        _finding(
            "RC15",
            "No licence file",
            "info",
            "Without an explicit licence the code is all-rights-reserved by default, which blocks "
            "reuse and redistribution even when it runs.",
            [_ev("code", "repository root")],
        )
    ]


def _rc16(scan: RepoScan) -> list[Finding]:
    if scan.readme:
        return []
    return [
        _finding(
            "RC16",
            "No README",
            "major",
            "There is no README, so the mapping from paper sections to commands is undocumented.",
            [_ev("code", "repository root")],
        )
    ]


def _rc17(claims: list[Claim]) -> list[Finding]:
    unmatched = [c for c in claims if c.level == "X"]
    if not unmatched:
        return []
    listed = ", ".join(c.id for c in unmatched[:6])
    return [
        _finding(
            "RC17",
            "Paper claims with no code counterpart",
            "major",
            f"{len(unmatched)} claim(s) have no implementation, dataset or value in the repository ({listed}). "
            "These results cannot be reproduced from this release.",
            [_ev("paper", c.evidence[0].ref if c.evidence else c.id, c.raw_metric) for c in unmatched[:4]],
        )
    ]


def run_rules(scan: RepoScan, doc: PaperDoc, claims: list[Claim]) -> list[Finding]:
    """Run every rule and return findings ordered by severity."""
    findings: list[Finding] = []
    findings.extend(_rc01(scan))
    findings.extend(_rc02(scan))
    findings.extend(_rc03(scan))
    findings.extend(_rc04(scan))
    findings.extend(_rc05(scan))
    findings.extend(_rc06(scan))
    findings.extend(_rc07(scan))
    findings.extend(_rc08(scan))
    findings.extend(_rc09(scan))
    findings.extend(_rc10(scan))
    findings.extend(_rc11(scan))
    findings.extend(_rc12(scan))
    findings.extend(_rc13(scan))
    findings.extend(_rc14(scan))
    findings.extend(_rc15(scan))
    findings.extend(_rc16(scan))
    findings.extend(_rc17(claims))

    order = {"blocker": 0, "major": 1, "minor": 2, "info": 3}
    findings.sort(key=lambda f: (order.get(f.severity, 9), f.rule_id))
    return findings
