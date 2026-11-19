"""Verdict decisions."""

import unittest

import helpers  # noqa: F401
from paperrepro.models import Claim, Evidence, Finding, SmokeReport
from paperrepro.verdict.score import decide

GOOD_SMOKE = SmokeReport(enabled=True, syntax_ok=True, entry_ok=True, manifest_ok=True)
NO_SMOKE = SmokeReport(enabled=False)


def _claim(level, cid="C01", role="paper", metric="accuracy"):
    return Claim(
        id=cid,
        metric=metric,
        raw_metric=metric,
        value="90.0",
        role=role,
        level=level,
        evidence=[Evidence(kind="paper", ref="Table 1")],
    )


def _finding(rule_id="RC02", severity="major", author_dependent=False):
    return Finding(
        rule_id=rule_id,
        title="Something",
        severity=severity,
        detail="detail",
        author_dependent=author_dependent,
    )


class TestDecide(unittest.TestCase):
    def test_all_executable_is_r3(self):
        verdict, confidence, _ = decide([_claim("E1")], [], GOOD_SMOKE)
        self.assertEqual(verdict, "R3")
        self.assertGreater(confidence, 0.5)

    def test_mostly_unmatched_is_r0(self):
        claims = [_claim("X", "C01"), _claim("X", "C02"), _claim("E3", "C03")]
        verdict, _, reasons = decide(claims, [], NO_SMOKE)
        self.assertEqual(verdict, "R0")
        self.assertTrue(any("counterpart" in r or "no counterpart" in r for r in reasons))

    def test_author_blocker_is_r1(self):
        verdict, _, _ = decide(
            [_claim("E2")], [_finding("RC04", "blocker", author_dependent=True)], NO_SMOKE
        )
        self.assertEqual(verdict, "R1")

    def test_engineering_gaps_are_r2(self):
        verdict, _, _ = decide(
            [_claim("E2"), _claim("E3", "C02")], [_finding("RC02", "major")], NO_SMOKE
        )
        self.assertEqual(verdict, "R2")

    def test_no_claims_is_r1(self):
        verdict, confidence, reasons = decide([], [], NO_SMOKE)
        self.assertEqual(verdict, "R1")
        self.assertLess(confidence, 0.3)
        self.assertTrue(reasons)

    def test_reference_claims_do_not_drive_verdict(self):
        claims = [_claim("E2"), _claim("X", "C02", role="reference")]
        verdict, _, _ = decide(claims, [], NO_SMOKE)
        self.assertEqual(verdict, "R2")

    def test_smoke_absence_caps_confidence(self):
        _, without, _ = decide([_claim("E2")], [], NO_SMOKE)
        _, with_smoke, _ = decide([_claim("E2")], [], GOOD_SMOKE)
        self.assertLess(without, with_smoke)

    def test_confidence_is_bounded(self):
        for claims in ([_claim("E1")], [_claim("X")], []):
            _, confidence, _ = decide(claims, [], GOOD_SMOKE)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
