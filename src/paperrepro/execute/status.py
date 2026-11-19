"""The five-state reproduction verdict.

Deliberately separate from the viability score: "we could not run it" is not the
same finding as "we ran it and the numbers disagreed", and neither of them is
the same as "the authors did not publish the checkpoint".
"""

from __future__ import annotations

from .compare import ClaimOutcome
from .runner import RunResult

__all__ = ["reproduction_status", "STATUS_LABELS", "BLOCKING_FAILURES"]

STATUS_LABELS: dict[str, str] = {
    "REPRODUCED": "reproduced",
    "PARTIALLY_REPRODUCED": "partially reproduced",
    "NOT_REPRODUCED": "not reproduced",
    "BLOCKED": "blocked by missing external assets",
    "INSUFFICIENT_EVIDENCE": "insufficient evidence",
}

# Failures that no amount of engineering on our side can fix.
BLOCKING_FAILURES = {"MISSING_WEIGHTS", "DATA_UNAVAILABLE", "BACKEND_UNAVAILABLE"}


def reproduction_status(run: RunResult, outcomes: list[ClaimOutcome]) -> tuple[str, str]:
    """Return (status, one-sentence reason)."""
    if run.status != "ok" and run.failure in BLOCKING_FAILURES:
        return (
            "BLOCKED",
            f"the run stopped at {run.failure}: {run.failure_detail or 'see artifacts'}",
        )

    scored = [o for o in outcomes if o.status != "NOT_RUN"]
    if not scored:
        if run.status == "ok":
            return (
                "INSUFFICIENT_EVIDENCE",
                "the run produced metrics but none of them correspond to a claim from the paper",
            )
        if run.failure in BLOCKING_FAILURES:
            return ("BLOCKED", f"no measurement was obtained ({run.failure})")
        # An environment or command failure is our problem to fix, not a verdict
        # on the paper: no evidence either way.
        return (
            "INSUFFICIENT_EVIDENCE",
            f"the run failed before producing a measurement ({run.failure or run.status})",
        )

    matched = [o for o in scored if o.status == "MATCH"]
    if len(matched) == len(scored):
        return ("REPRODUCED", f"all {len(scored)} compared claim(s) match within tolerance")
    if matched:
        return (
            "PARTIALLY_REPRODUCED",
            f"{len(matched)}/{len(scored)} compared claim(s) match; the rest differ or are only close",
        )
    return (
        "NOT_REPRODUCED",
        f"none of the {len(scored)} compared claim(s) match within tolerance",
    )
