"""Claim-to-code alignment.

For every claim we look for four independent kinds of evidence:

1. a metric implementation or metric name in the code,
2. the dataset the claim is measured on,
3. the literal number from the paper (rare, but when present it is the
   strongest signal that the authors had a results file for this number),
4. a passing local smoke check.

The level is then decided by what is missing, and every gap is phrased as an
action ("the dataset is never referenced") rather than a vague worry.
"""

from __future__ import annotations

import re

from ..models import Claim, Evidence, RepoScan, SmokeReport
from ..textutil import aliases_for, snippet

__all__ = ["link_claims", "level_counts"]


def _find_literals(scan: RepoScan, value: str, limit: int = 2) -> list[Evidence]:
    """Find the paper's number written in the repository (results files, scripts)."""
    if len(value) < 3:
        return []
    if value in {"0.0", "1.0", "100.0"}:
        return []
    pattern = re.compile(r"(?<![\d.])" + re.escape(value) + r"(?![\d])")
    hits: list[Evidence] = []
    code_texts = [f for f in scan.files if f.text and f.lang in {"python", "r", "julia", "shell", "config", "text", "javascript"}]
    for f in code_texts:
        m = pattern.search(f.text)
        if m:
            line = f.text.count("\n", 0, m.start()) + 1
            hits.append(
                Evidence(
                    kind="code",
                    ref=f"{f.path}:{line}",
                    text=snippet(f.text, m.start()),
                    detail=f"literal '{value}' appears in the repository",
                )
            )
            if len(hits) >= limit:
                break
    return hits


def _first_text(scan: RepoScan, ref: str) -> str:
    """The source line behind a 'path:line' reference, trimmed for display."""
    path, _, line_s = ref.rpartition(":")
    try:
        line_no = int(line_s)
    except ValueError:
        path, line_no = ref, 0
    for f in scan.files:
        if f.path != path or not f.text:
            continue
        lines = f.text.splitlines()
        if line_no and 1 <= line_no <= len(lines):
            return lines[line_no - 1].strip()[:160]
        return lines[0].strip()[:160] if lines else ""
    return ""


def _metric_evidence(scan: RepoScan, claim: Claim, limit: int = 2) -> list[Evidence]:
    out: list[Evidence] = []
    for ref in scan.metric_refs.get(claim.metric, [])[:limit]:
        out.append(
            Evidence(kind="code", ref=ref, text=_first_text(scan, ref), detail=f"{claim.raw_metric} implementation")
        )
    if not out:
        # Fall back to a raw alias scan, which catches one-off metric names.
        for alias in aliases_for(claim.metric)[:2]:
            for ref in scan.metric_refs.get(alias, [])[:1]:  # pragma: no cover - aliases are canonical keys
                out.append(Evidence(kind="code", ref=ref, text=_first_text(scan, ref)))
    return out


def _dataset_evidence(scan: RepoScan, claim: Claim, limit: int = 2) -> list[Evidence]:
    if not claim.dataset:
        return []
    out: list[Evidence] = []
    for ref in scan.dataset_refs.get(claim.dataset, [])[:limit]:
        out.append(
            Evidence(kind="code", ref=ref, text=_first_text(scan, ref), detail=f"dataset '{claim.dataset}'")
        )
    return out


def link_claims(claims: list[Claim], scan: RepoScan, smoke: SmokeReport) -> None:
    """Attach code evidence and an evidence level to each claim, in place."""
    for claim in claims:
        claim.code_evidence = []
        claim.gaps = []

        metric_ev = _metric_evidence(scan, claim)
        dataset_ev = _dataset_evidence(scan, claim)
        literal_ev = _find_literals(scan, claim.value)
        claim.code_evidence.extend(literal_ev)
        claim.code_evidence.extend(metric_ev)
        claim.code_evidence.extend(dataset_ev)

        has_metric = bool(metric_ev)
        has_dataset = bool(dataset_ev)
        has_literal = bool(literal_ev)

        if not has_metric:
            claim.gaps.append(f"no implementation of metric '{claim.metric}' was found in the repository")
        if claim.dataset and not has_dataset:
            claim.gaps.append(f"dataset '{claim.dataset}' is never referenced in the repository")
        if not has_literal:
            claim.gaps.append(f"the reported value {claim.value} appears nowhere in the code or result files")

        if has_metric and has_literal and smoke.passed and (has_dataset or not claim.dataset):
            claim.level = "E1"
        elif has_metric and (has_dataset or has_literal):
            claim.level = "E2"
        elif has_metric or has_literal or has_dataset:
            claim.level = "E3"
            if has_metric:
                claim.gaps.append("the link between this implementation and the reported number is indirect")
        else:
            claim.level = "X"

        # A claim whose dataset is required but absent cannot be trusted even
        # when the metric exists.
        if claim.level == "E2" and claim.dataset and not has_dataset:
            claim.level = "E3"


def level_counts(claims: list[Claim]) -> dict[str, int]:
    counts = {"E1": 0, "E2": 0, "E3": 0, "X": 0}
    for c in claims:
        counts[c.level] = counts.get(c.level, 0) + 1
    return counts
