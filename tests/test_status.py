"""The five-state reproduction verdict."""

import unittest

import helpers  # noqa: F401
from paperrepro.execute.compare import ClaimOutcome
from paperrepro.execute.runner import RunResult
from paperrepro.execute.status import reproduction_status


def _run(status="ok", failure=""):
    return RunResult(recipe="t", backend="local", status=status, failure=failure)


def _outcome(status):
    return ClaimOutcome("C01", "accuracy", "Accuracy", "91.3", 91.3, 0.0, status)


class TestStatus(unittest.TestCase):
    def test_all_match_is_reproduced(self):
        status, reason = reproduction_status(_run(), [_outcome("MATCH")])
        self.assertEqual(status, "REPRODUCED")
        self.assertTrue(reason)

    def test_mixed_is_partial(self):
        status, _ = reproduction_status(_run(), [_outcome("MATCH"), _outcome("MISMATCH")])
        self.assertEqual(status, "PARTIALLY_REPRODUCED")

    def test_all_mismatch_is_not_reproduced(self):
        status, _ = reproduction_status(_run(), [_outcome("MISMATCH")])
        self.assertEqual(status, "NOT_REPRODUCED")

    def test_missing_weights_is_blocked(self):
        status, reason = reproduction_status(_run("failed", "MISSING_WEIGHTS"), [])
        self.assertEqual(status, "BLOCKED")
        self.assertIn("MISSING_WEIGHTS", reason)

    def test_env_conflict_is_not_blocked(self):
        status, _ = reproduction_status(_run("failed", "ENV_CONFLICT"), [])
        self.assertNotEqual(status, "BLOCKED")

    def test_no_comparable_claim_is_insufficient(self):
        status, _ = reproduction_status(_run(), [_outcome("NOT_RUN")])
        self.assertEqual(status, "INSUFFICIENT_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
