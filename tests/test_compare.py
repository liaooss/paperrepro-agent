"""Comparison of paper values with measured values."""

import unittest

import helpers  # noqa: F401
from paperrepro.execute.compare import compare_claims, to_points
from paperrepro.models import Claim, Evidence


def _claim(value="91.3", metric="accuracy", role="paper", cid="C01"):
    return Claim(
        id=cid,
        metric=metric,
        raw_metric=metric,
        value=value,
        role=role,
        evidence=[Evidence(kind="paper", ref="Table 2")],
    )


class TestScale(unittest.TestCase):
    def test_fraction_matches_points(self):
        self.assertAlmostEqual(to_points(0.913, 91.3), 91.3)
        self.assertAlmostEqual(to_points(0.913, 0.913), 91.3)


class TestCompare(unittest.TestCase):
    def test_match(self):
        outcomes = compare_claims([_claim()], {"accuracy": 0.9130}, tolerance_abs=0.5)
        self.assertEqual(outcomes[0].status, "MATCH")
        self.assertAlmostEqual(outcomes[0].delta, 0.0, places=2)

    def test_close(self):
        outcomes = compare_claims(
            [_claim()], {"accuracy": 0.910}, tolerance_abs=0.2, tolerance_rel=0.0
        )
        self.assertEqual(outcomes[0].status, "CLOSE")

    def test_mismatch(self):
        outcomes = compare_claims([_claim()], {"accuracy": 0.850}, tolerance_abs=0.5)
        self.assertEqual(outcomes[0].status, "MISMATCH")
        self.assertLess(outcomes[0].delta, 0)

    def test_not_run(self):
        outcomes = compare_claims([_claim()], {}, tolerance_abs=0.5)
        self.assertEqual(outcomes[0].status, "NOT_RUN")
        self.assertIsNone(outcomes[0].measured)

    def test_alias_metric_name(self):
        outcomes = compare_claims([_claim(metric="f1")], {"macro-f1": 91.0}, tolerance_abs=0.5)
        self.assertEqual(outcomes[0].status, "MATCH")

    def test_single_metric_fallback(self):
        outcomes = compare_claims([_claim(value="0.41", metric="map")], {"score": 0.41}, tolerance_abs=0.5)
        self.assertEqual(outcomes[0].status, "MATCH")
        self.assertIn("position", outcomes[0].note)

    def test_baseline_claims_are_skipped(self):
        outcomes = compare_claims([_claim(role="reference")], {"accuracy": 0.9})
        self.assertEqual(outcomes, [])

    def test_non_numeric_paper_value(self):
        outcomes = compare_claims([_claim(value="n/a")], {"accuracy": 0.9})
        self.assertEqual(outcomes[0].status, "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
