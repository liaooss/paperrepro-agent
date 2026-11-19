"""Viability scoring: the 'should I use this as a baseline' decision."""

import unittest

import helpers  # noqa: F401
from reprocheck.execute.compare import ClaimOutcome
from reprocheck.execute.runner import RunResult
from reprocheck.execute.viability import assess_viability
from reprocheck.models import Finding


def _run(status="ok", failure="", duration=600.0, disk=1.0):
    return RunResult(
        recipe="t",
        backend="local",
        status=status,
        failure=failure,
        duration_s=duration,
        disk_gb=disk,
    )


def _outcome(status="MATCH", delta=0.0):
    return ClaimOutcome("C01", "accuracy", "Accuracy", "91.3", 91.3, delta, status)


class TestViability(unittest.TestCase):
    def test_good_run_is_usable(self):
        viability = assess_viability(_run(), [_outcome()])
        self.assertEqual(viability.recommendation, "USE")
        self.assertGreaterEqual(viability.score, 4.0)

    def test_mismatch_lowers_fidelity(self):
        viability = assess_viability(_run(), [_outcome("MISMATCH", -6.3)])
        fidelity = next(d for d in viability.dimensions if d.name == "fidelity")
        self.assertLessEqual(fidelity.score, 1.0)
        self.assertNotEqual(viability.recommendation, "USE")

    def test_missing_weights_is_blocked(self):
        viability = assess_viability(_run(status="failed", failure="MISSING_WEIGHTS"), [])
        self.assertEqual(viability.recommendation, "AVOID")
        self.assertTrue(any("MISSING_WEIGHTS" in b for b in viability.blockers))

    def test_no_licence_lowers_openness(self):
        findings = [Finding(rule_id="RC15", title="No licence", severity="info", detail="")]
        viability = assess_viability(_run(), [_outcome()], findings)
        openness = next(d for d in viability.dimensions if d.name == "openness")
        self.assertLess(openness.score, 5.0)

    def test_expensive_run_lowers_cost_score(self):
        viability = assess_viability(_run(duration=60 * 60 * 6, disk=40.0), [_outcome()])
        cost = next(d for d in viability.dimensions if d.name == "cost")
        self.assertLessEqual(cost.score, 2.0)

    def test_dimensions_are_complete(self):
        viability = assess_viability(_run(), [_outcome()])
        names = {d.name for d in viability.dimensions}
        self.assertEqual(
            names, {"executability", "fidelity", "cost", "comparability", "openness"}
        )


if __name__ == "__main__":
    unittest.main()
