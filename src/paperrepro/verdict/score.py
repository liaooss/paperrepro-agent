"""Turning evidence levels and rule hits into a single graded verdict.

The mapping is intentionally conservative and explainable:

* all claims executable            -> R3
* most claims unmatched            -> R0
* something only the authors can supply -> R1
* everything else                  -> R2
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from ..version import __version__
from ..models import Claim, Finding, PaperDoc, RepoScan, Scorecard, SmokeReport, VERDICT_LABELS
from ..textutil import human_list

__all__ = ["decide", "build_scorecard"]

LEVEL_SCORE = {"E1": 0.95, "E2": 0.78, "E3": 0.45, "X": 0.08}


def decide(
    claims: list[Claim], findings: list[Finding], smoke: SmokeReport
) -> tuple[str, float, list[str]]:
    """Return (verdict, confidence, reasons-in-plain-English)."""
    paper_claims = [c for c in claims if c.role == "paper"]
    self_claims = paper_claims or claims
    if not self_claims:
        return (
            "R1",
            0.15,
            [
                "No quantitative claim could be extracted from the paper, so there is nothing to anchor a verdict on. "
                "Pass the LaTeX source or a paper with a results table."
            ],
        )

    n = len(self_claims)
    counts = Counter(c.level for c in self_claims)
    reasons: list[str] = []

    author_blockers = [f for f in findings if f.severity == "blocker" and f.author_dependent]
    other_blockers = [f for f in findings if f.severity == "blocker" and not f.author_dependent]

    x_ratio = counts.get("X", 0) / n
    if counts.get("E1", 0) == n:
        verdict = "R3"
        reasons.append(f"All {n} paper claims reached executable evidence.")
    elif x_ratio > 0.5:
        verdict = "R0"
        reasons.append(
            f"{counts.get('X', 0)} of {n} paper claims have no counterpart in the repository, "
            "so the release does not implement what the paper reports."
        )
    elif author_blockers:
        verdict = "R1"
        reasons.append(
            "Missing assets that only the authors can supply: "
            + human_list([f"{f.rule_id} {f.title.lower()}" for f in author_blockers], 3)
        )
    else:
        verdict = "R2"
        missing = n - counts.get("E1", 0)
        tail = ""
        if counts.get("X"):
            tail = f" {counts['X']} claim(s) have no counterpart in the code at all."
        reasons.append(
            f"{missing} of {n} claim(s) still lack executable evidence, but no asset was found "
            f"that only the authors could supply.{tail}"
        )

    if counts.get("E2"):
        reasons.append(
            f"{counts['E2']} claim(s) have strong static evidence (implementation and inputs found, nothing executed)."
        )
    if counts.get("E3"):
        reasons.append(f"{counts['E3']} claim(s) rest on name-level matches only.")
    if counts.get("X"):
        reasons.append(f"{counts['X']} claim(s) could not be matched to any code, dataset or number.")
    if other_blockers:
        reasons.append(
            "Structural blockers: " + human_list([f"{f.rule_id} {f.title.lower()}" for f in other_blockers], 3)
        )
    if smoke.enabled:
        reasons.append(
            "Smoke check ran: "
            + ("all Python files compile and an entry point exists." if smoke.passed else "it did not pass.")
        )
    else:
        reasons.append("Smoke check was not run (--smoke), so no claim can reach E1.")

    base = sum(LEVEL_SCORE.get(c.level, 0.08) for c in self_claims) / n
    penalty = 1.0
    if not smoke.enabled:
        penalty *= 0.85
    if counts.get("X"):
        penalty *= 1.0 - 0.15 * counts["X"] / n
    confidence = max(0.05, min(0.95, base * penalty))
    return verdict, confidence, reasons


def _summary(verdict: str, claims: list[Claim], findings: list[Finding], reasons: list[str]) -> str:
    self_claims = [c for c in claims if c.role == "paper"] or claims
    n = len(self_claims)
    label = VERDICT_LABELS.get(verdict, verdict)
    blockers = [f for f in findings if f.severity == "blocker"]
    if not self_claims:
        return (
            f"Verdict {verdict} ({label}): no quantitative claim could be extracted, so this release "
            "cannot be graded on reproducibility. " + (reasons[0] if reasons else "")
        )
    parts = [f"Verdict {verdict} ({label}): {n} quantitative claim(s) from the paper were checked against the code."]
    if blockers:
        parts.append(f"Top blocker: {blockers[0].rule_id} {blockers[0].title.lower()}.")
    majors = [f for f in findings if f.severity == "major"]
    if majors:
        parts.append(
            f"{len(majors)} major issue(s) remain, starting with {majors[0].rule_id} {majors[0].title.lower()}."
        )
    unexecutable = [c for c in self_claims if c.level != "E1"]
    if unexecutable:
        parts.append(
            f"{len(unexecutable)} claim(s) still need execution before any number can be called reproduced."
        )
    return " ".join(parts)


def build_scorecard(
    doc: PaperDoc,
    scan: RepoScan,
    claims: list[Claim],
    findings: list[Finding],
    smoke: SmokeReport,
    llm_used: bool = False,
    llm_model: str = "",
    llm_summary: str = "",
) -> Scorecard:
    verdict, confidence, reasons = decide(claims, findings, smoke)
    summary = llm_summary.strip() or _summary(verdict, claims, findings, reasons)

    actions: list[str] = []
    for f in findings:
        if f.severity in {"blocker", "major"} and len(actions) < 6:
            where = f.evidence[0].ref if f.evidence else ""
            actions.append(f"[{f.rule_id}] {f.title}" + (f" — {where}" if where else ""))
    self_claims = [c for c in claims if c.role == "paper"] or claims
    for c in self_claims:
        if c.level == "X" and len(actions) < 9:
            actions.append(
                f"[{c.id}] Find or implement '{c.raw_metric}' for {c.dataset or 'the claimed setting'} "
                f"(paper reports {c.value})."
            )
    if not smoke.enabled:
        actions.append("Run again with --smoke to compile-check the code and allow claims to reach E1.")
    if not self_claims:
        actions.append("Supply the LaTeX source (or a paper with a results table) so claims can be extracted.")

    return Scorecard(
        paper=doc.path,
        repo=scan.root,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        paperrepro_version=__version__,
        verdict=verdict,
        confidence=confidence,
        summary=summary,
        claims=claims,
        findings=findings,
        smoke=smoke,
        paper_meta=doc.to_dict(),
        repo_meta=scan.to_dict(),
        next_actions=actions,
        llm_used=llm_used,
        llm_model=llm_model,
        # reasons are re-derived by the report; keep the API surface small
    )
