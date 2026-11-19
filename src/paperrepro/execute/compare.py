"""Compare what the paper reports with what the run measured.

Unit handling is the subtle part. Papers print ``91.3`` for accuracy and also
``0.913``; a script may print either. Everything is normalised to "points"
(percentage-style) before a difference is computed, using the paper's own
magnitude as the reference, so 0.913 vs 91.3 is a match and not a 90-point miss.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import Claim
from ..textutil import metric_canonical

__all__ = ["ClaimOutcome", "compare_claims", "to_points"]


@dataclass
class ClaimOutcome:
    claim_id: str
    metric: str
    raw_metric: str
    paper_value: str
    measured: float | None
    delta: float | None
    status: str  # MATCH | CLOSE | MISMATCH | NOT_RUN
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "metric": self.metric,
            "raw_metric": self.raw_metric,
            "paper_value": self.paper_value,
            "measured": self.measured,
            "delta": None if self.delta is None else round(self.delta, 3),
            "status": self.status,
            "note": self.note,
        }


def to_points(value: float, reference: float) -> float:
    """Put ``value`` on the same scale as ``reference`` (fraction vs points)."""
    if abs(reference) <= 1.5 and abs(value) <= 1.5:
        return value * 100.0
    if abs(reference) > 1.5 and abs(value) <= 1.5:
        return value * 100.0
    if abs(reference) <= 1.5 and abs(value) > 1.5:
        return value
    return value


def _canon_metrics(metrics: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in metrics.items():
        canon = metric_canonical(key) or key
        out.setdefault(canon, value)
    return out


def compare_claims(
    claims: list[Claim],
    metrics: dict[str, float],
    tolerance_abs: float = 0.5,
    tolerance_rel: float = 0.01,
) -> list[ClaimOutcome]:
    measured_by_metric = _canon_metrics(metrics)
    single_value = next(iter(metrics.values())) if len(metrics) == 1 else None

    outcomes: list[ClaimOutcome] = []
    for claim in claims:
        if claim.role != "paper":
            continue
        measured = measured_by_metric.get(claim.metric)
        note = ""
        if measured is None and single_value is not None:
            measured = single_value
            note = "matched by position: the run produced a single metric"

        paper_raw = claim.value
        try:
            paper_val = float(str(paper_raw).replace("%", "").strip())
        except ValueError:
            outcomes.append(
                ClaimOutcome(claim.id, claim.metric, claim.raw_metric, paper_raw, measured, None, "NOT_RUN",
                             "the paper value is not numeric")
            )
            continue

        if measured is None:
            outcomes.append(
                ClaimOutcome(claim.id, claim.metric, claim.raw_metric, paper_raw, None, None, "NOT_RUN",
                             "the run did not report this metric")
            )
            continue

        paper_pts = to_points(paper_val, paper_val)
        measured_pts = to_points(measured, paper_val) if paper_val > 1.5 else measured * 100.0
        delta = measured_pts - paper_pts
        abs_delta = abs(delta)
        rel = abs_delta / max(abs(paper_pts), 1e-9)

        if abs_delta <= tolerance_abs or rel <= tolerance_rel:
            status = "MATCH"
        elif abs_delta <= 2 * tolerance_abs:
            status = "CLOSE"
            note = (note + "; " if note else "") + f"within twice the tolerance ({tolerance_abs} points)"
        else:
            status = "MISMATCH"

        outcomes.append(
            ClaimOutcome(
                claim_id=claim.id,
                metric=claim.metric,
                raw_metric=claim.raw_metric,
                paper_value=paper_raw,
                measured=round(measured_pts, 3),
                delta=round(delta, 3),
                status=status,
                note=note,
            )
        )
    return outcomes


def summarise_outcomes(outcomes: list[ClaimOutcome]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for outcome in outcomes:
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
    return counts
