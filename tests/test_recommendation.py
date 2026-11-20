"""The recommendation: use / use with conditions / do not use / cannot assess."""

import unittest

import helpers  # noqa: F401
from paperrepro.audit import ParamCheck
from paperrepro.execute.recommendation import (
    CANNOT_ASSESS,
    DO_NOT_USE,
    USE,
    USE_WITH_CONDITIONS,
    recommend,
)
from paperrepro.execute.viability import Dimension, Viability


def _viability(blockers=None):
    return Viability(
        score=4.0,
        recommendation="USE",
        dimensions=[Dimension("executability", 5.0, "ok")],
        blockers=blockers or [],
    )


def _audit(status="MATCH", param="batch_size"):
    return [ParamCheck(param=param, paper_value="64", code_value="32", status=status, code_ref="config.yaml:3")]


class TestRecommendation(unittest.TestCase):
    def test_clean_reproduction_is_usable(self):
        rec = recommend("REPRODUCED", _viability(), _audit("MATCH"), duration_s=60)
        self.assertEqual(rec.verdict, USE)
        self.assertTrue(rec.conditions)
        self.assertIn("min", rec.cost_note)

    def test_reproduced_but_config_differs_needs_conditions(self):
        rec = recommend("REPRODUCED", _viability(), _audit("MISMATCH"), duration_s=60)
        self.assertEqual(rec.verdict, USE_WITH_CONDITIONS)
        self.assertTrue(any("batch_size" in c for c in rec.conditions))

    def test_partial_is_conditional(self):
        rec = recommend("PARTIALLY_REPRODUCED", _viability(), [], duration_s=120)
        self.assertEqual(rec.verdict, USE_WITH_CONDITIONS)
        self.assertIn("single number", rec.headline)

    def test_not_reproduced_is_do_not_use(self):
        rec = recommend("NOT_REPRODUCED", _viability(), [], duration_s=120)
        self.assertEqual(rec.verdict, DO_NOT_USE)
        self.assertTrue(any("protocol" in c for c in rec.conditions))

    def test_blocked_makes_no_claim(self):
        rec = recommend(
            "BLOCKED",
            _viability(["MISSING_WEIGHTS: ckpt.pt"]),
            [],
            duration_s=0,
        )
        self.assertEqual(rec.verdict, CANNOT_ASSESS)
        self.assertIn("no claim", rec.headline)
        self.assertTrue(any("MISSING_WEIGHTS" in c for c in rec.conditions))

    def test_insufficient_evidence_is_also_cannot_assess(self):
        rec = recommend("INSUFFICIENT_EVIDENCE", _viability(), [], duration_s=0)
        self.assertEqual(rec.verdict, CANNOT_ASSESS)

    def test_unknown_cost_is_stated(self):
        rec = recommend("REPRODUCED", _viability(), [], duration_s=0)
        self.assertIn("unknown", rec.cost_note.lower())

    def test_cost_scales_with_seeds(self):
        short = recommend("REPRODUCED", _viability(), [], seeds=1, duration_s=600)
        long = recommend("REPRODUCED", _viability(), [], seeds=5, duration_s=600)
        self.assertNotEqual(short.cost_note, long.cost_note)


if __name__ == "__main__":
    unittest.main()
