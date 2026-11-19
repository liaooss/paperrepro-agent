"""Should this paper be used as a baseline?

Reproducing a number is necessary but not sufficient. A baseline is something
you re-run, cite and defend in front of reviewers, so the decision needs five
independent dimensions, each scored 0-5 and each carrying the reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import Finding
from .compare import ClaimOutcome

__all__ = ["Viability", "Dimension", "assess_viability"]

RECOMMENDATIONS = {
    "USE": "use as a baseline",
    "USE_WITH_CARE": "usable with conditions",
    "AVOID": "do not use as a baseline yet",
}


@dataclass
class Dimension:
    name: str
    score: float
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "score": round(self.score, 1), "note": self.note}


@dataclass
class Viability:
    score: float
    recommendation: str
    dimensions: list[Dimension] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return RECOMMENDATIONS.get(self.recommendation, self.recommendation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "recommendation": self.recommendation,
            "label": self.label,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "blockers": list(self.blockers),
        }


_EXECUTABILITY = {
    "ok": 5.0,
    "timeout": 2.5,
    "failed": 2.0,
    "error": 0.5,
}

_FAILURE_CAP = {
    "ENV_CONFLICT": 2.5,
    "MISSING_WEIGHTS": 1.0,
    "DATA_UNAVAILABLE": 1.0,
    "OOM": 2.0,
    "NETWORK": 2.0,
    "TIMEOUT": 2.5,
    "NO_METRIC_PARSED": 3.0,
    "COMMAND_FAILED": 2.0,
    "BACKEND_UNAVAILABLE": 0.5,
}


def assess_viability(run, outcomes: list[ClaimOutcome], findings: list[Finding] | None = None) -> Viability:
    findings = findings or []
    blockers: list[str] = []
    dims: list[Dimension] = []

    # 1. Can it run at all?
    execution = _EXECUTABILITY.get(run.status, 1.0)
    if run.failure:
        execution = min(execution, _FAILURE_CAP.get(run.failure, execution))
        blockers.append(f"{run.failure}: {run.failure_detail or 'see artifacts'}")
    dims.append(
        Dimension(
            "executability",
            execution,
            f"run status {run.status}" + (f" ({run.failure})" if run.failure else ""),
        )
    )

    # 2. Do the numbers agree?
    scored = [o for o in outcomes if o.status != "NOT_RUN"]
    if scored:
        points = sum(1.0 for o in scored if o.status == "MATCH") + sum(0.5 for o in scored if o.status == "CLOSE")
        fidelity = 5.0 * points / len(scored)
        note = f"{sum(1 for o in scored if o.status == 'MATCH')}/{len(scored)} claims match"
        mismatched = [o for o in scored if o.status == "MISMATCH"]
        if mismatched:
            worst = max(mismatched, key=lambda o: abs(o.delta or 0))
            note += f"; worst miss {worst.claim_id} {worst.delta:+.2f} points"
            blockers.append(f"{worst.claim_id} differs by {worst.delta:+.2f} points")
    else:
        fidelity = 0.0
        note = "no claim could be compared"
        blockers.append("no measured value to compare against the paper")
    dims.append(Dimension("fidelity", fidelity, note))

    # 3. What does it cost to keep re-running?
    minutes = run.duration_s / 60.0
    if minutes <= 30 and run.disk_gb <= 5:
        cost = 5.0
    elif minutes <= 120 and run.disk_gb <= 20:
        cost = 3.5
    else:
        cost = 2.0
    cost_note = f"{minutes:.0f} min, {run.disk_gb:.1f} GB on disk"
    if run.status != "ok":
        # A run that never produced numbers tells us nothing about steady-state
        # cost, so it must not score like a cheap, repeatable one.
        cost = min(cost, 2.5)
        cost_note += " (run did not complete; cost is a lower bound)"
    dims.append(Dimension("cost", cost, cost_note))

    # 4. Are the numbers comparable to a number you would report?
    splits = {o.claim_id for o in outcomes}
    comparability = 3.0
    note = "protocol must be checked by hand: split, preprocessing and metric definition"
    if not splits:
        comparability = 1.5
    dims.append(Dimension("comparability", comparability, note))

    # 5. Can this be reused legally and technically?
    rule_ids = {f.rule_id for f in findings}
    openness = 5.0 - (1.5 if "RC15" in rule_ids else 0.0) - (1.5 if "RC04" in rule_ids else 0.0)
    openness = max(0.0, openness)
    dims.append(
        Dimension(
            "openness",
            openness,
            "licence present" if "RC15" not in rule_ids else "no licence file",
        )
    )

    total = sum(d.score for d in dims) / len(dims)
    if total >= 4.0:
        recommendation = "USE"
    elif total >= 2.5:
        recommendation = "USE_WITH_CARE"
    else:
        recommendation = "AVOID"

    # A run that produced no measurement cannot be recommended, whatever the
    # arithmetic says: cost and openness are not evidence about the paper.
    if not scored and run.status != "ok":
        recommendation = "AVOID"

    return Viability(score=total, recommendation=recommendation, dimensions=dims, blockers=blockers)
