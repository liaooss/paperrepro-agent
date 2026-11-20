"""The actual question a user has: can I use this paper as a baseline?

Everything else in the report is evidence. This module turns the evidence into a
recommendation with conditions attached, and it refuses to recommend anything it
cannot back.

The four outcomes are deliberately blunt:

- ``USE`` - reproduced, consistent, and cheap enough to re-run
- ``USE_WITH_CONDITIONS`` - usable, but say which configuration you used
- ``DO_NOT_USE`` - the numbers do not reproduce
- ``CANNOT_ASSESS`` - we could not obtain a measurement, so we say nothing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["Recommendation", "recommend"]

USE = "USE"
USE_WITH_CONDITIONS = "USE_WITH_CONDITIONS"
DO_NOT_USE = "DO_NOT_USE"
CANNOT_ASSESS = "CANNOT_ASSESS"

_LABELS = {
    USE: "use as a baseline",
    USE_WITH_CONDITIONS: "usable with conditions",
    DO_NOT_USE: "do not use as a baseline",
    CANNOT_ASSESS: "cannot be assessed",
}


@dataclass
class Recommendation:
    verdict: str
    headline: str
    conditions: list[str] = field(default_factory=list)
    cost_note: str = ""

    @property
    def label(self) -> str:
        return _LABELS.get(self.verdict, self.verdict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "label": self.label,
            "headline": self.headline,
            "conditions": list(self.conditions),
            "cost_note": self.cost_note,
        }


def _cost_note(duration_s: float, seeds: int) -> str:
    """Wall-clock cost of keeping this in a comparison table."""
    per_run_min = duration_s / 60.0
    runs = max(seeds, 1)
    total_h = per_run_min * runs / 60.0
    if per_run_min <= 0:
        return "cost unknown: the run produced no timing"
    return (
        f"about {per_run_min:.0f} min per run; a {runs}-seed comparison costs "
        f"~{total_h:.1f} machine-hours, plus your own data preparation"
    )


def recommend(
    status: str,
    viability,
    audit: list | None = None,
    seeds: int = 3,
    duration_s: float = 0.0,
) -> Recommendation:
    """Turn the evidence into a recommendation, never into a score alone."""
    audit = audit or []
    mismatches = [c for c in audit if getattr(c, "status", "") == "MISMATCH"]
    cost = _cost_note(duration_s, seeds)

    if status == "REPRODUCED":
        if mismatches:
            names = ", ".join(c.param for c in mismatches[:3])
            return Recommendation(
                verdict=USE_WITH_CONDITIONS,
                headline=(
                    "The reported number reproduces, but the released configuration does not match "
                    f"the paper on {names}."
                ),
                conditions=[
                    f"state in your paper which setting you used for {names}: the released code's or the paper's",
                    "or re-run the evaluation with the paper's setting and report both numbers",
                ],
                cost_note=cost,
            )
        return Recommendation(
            verdict=USE,
            headline="The reported number reproduces within tolerance and the configuration is consistent.",
            conditions=[
                "cite the measured value, not the paper's, when you compare against it",
                "keep the recipe with your results so the comparison can be re-run",
            ],
            cost_note=cost,
        )

    if status == "PARTIALLY_REPRODUCED":
        return Recommendation(
            verdict=USE_WITH_CONDITIONS,
            headline="Some claims reproduce and some do not; the paper cannot be cited as a single number.",
            conditions=[
                "compare only against the claim that reproduced, and say which one",
                "do not quote the paper's headline number as if you had matched it",
            ],
            cost_note=cost,
        )

    if status == "NOT_REPRODUCED":
        return Recommendation(
            verdict=DO_NOT_USE,
            headline="The reported numbers did not reproduce under the conditions we could run.",
            conditions=[
                "before discarding it, check the protocol: split, preprocessing and metric definition",
                "if the gap survives that check, treat the paper's numbers as unreliable for comparison",
            ],
            cost_note=cost,
        )

    # BLOCKED or INSUFFICIENT_EVIDENCE
    reasons = []
    if viability is not None and getattr(viability, "blockers", None):
        reasons.extend(viability.blockers[:2])
    return Recommendation(
        verdict=CANNOT_ASSESS,
        headline=(
            "We could not obtain a measurement, so this report makes no claim about the paper's "
            "reproducibility."
        ),
        conditions=[f"unblock: {r}" for r in reasons] or ["obtain the missing environment or assets"],
        cost_note=cost,
    )
