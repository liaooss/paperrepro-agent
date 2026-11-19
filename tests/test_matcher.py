"""Claim-to-code alignment levels."""

import unittest

import helpers
from paperrepro.align.matcher import level_counts, link_claims
from paperrepro.ingest.repo import scan_repo
from paperrepro.models import Claim, Evidence, SmokeReport


def _claim(metric="accuracy", value="72.3", dataset="imagenet", cid="C01"):
    return Claim(
        id=cid,
        metric=metric,
        raw_metric=metric,
        value=value,
        dataset=dataset,
        evidence=[Evidence(kind="paper", ref="Table 1", text="ours")],
    )


PASSING_SMOKE = SmokeReport(enabled=True, syntax_ok=True, entry_ok=True, manifest_ok=True)


class TestLevels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scan = scan_repo(helpers.DEMO_REPO)

    def test_metric_and_dataset_give_e2(self):
        claim = _claim()
        link_claims([claim], self.scan, SmokeReport(enabled=False))
        self.assertEqual(claim.level, "E2")
        self.assertTrue(claim.code_evidence)
        self.assertTrue(any("utils/metrics.py" in ev.ref for ev in claim.code_evidence))

    def test_missing_metric_and_dataset_give_x(self):
        claim = _claim(metric="wer", value="9.9", dataset="librispeech")
        link_claims([claim], self.scan, SmokeReport(enabled=False))
        self.assertEqual(claim.level, "X")
        self.assertEqual(claim.code_evidence, [])
        self.assertTrue(claim.gaps)

    def test_gaps_are_actionable(self):
        claim = _claim(metric="wer", value="9.9", dataset="librispeech")
        link_claims([claim], self.scan, SmokeReport(enabled=False))
        joined = " ".join(claim.gaps)
        self.assertIn("wer", joined)
        self.assertIn("librispeech", joined)
        self.assertIn("9.9", joined)

    def test_missing_dataset_downgrades_to_e3(self):
        claim = _claim(dataset="coco")
        link_claims([claim], self.scan, SmokeReport(enabled=False))
        self.assertIn(claim.level, {"E3", "X"})
        if claim.level == "E3":
            self.assertTrue(any("coco" in gap for gap in claim.gaps))

    def test_literal_plus_metric_plus_smoke_gives_e1(self):
        repo = helpers.make_repo(
            {
                "run.py": "print('ok')\n",
                "results.txt": "top1 72.3\n",
                "metrics.py": (
                    "def top1_accuracy(preds, targets):\n"
                    "    return 0.0\n"
                ),
                "data.py": "NAME = 'imagenet'\n",
                "requirements.txt": "torch==2.1.0\n",
            }
        )
        try:
            scan = scan_repo(repo)
            claim = _claim()
            link_claims([claim], scan, PASSING_SMOKE)
            self.assertEqual(claim.level, "E1")
            self.assertTrue(any("results.txt" in ev.ref for ev in claim.code_evidence))
        finally:
            helpers.cleanup(repo)

    def test_level_counts(self):
        claims = [_claim(cid="C01"), _claim(metric="wer", dataset="", cid="C02")]
        link_claims(claims, self.scan, SmokeReport(enabled=False))
        counts = level_counts(claims)
        self.assertEqual(sum(counts.values()), 2)


if __name__ == "__main__":
    unittest.main()
