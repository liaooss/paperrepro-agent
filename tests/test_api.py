"""End-to-end API and report rendering."""

import json
import tempfile
import unittest
from pathlib import Path

import helpers
from paperrepro.api import assess
from paperrepro.verdict.report import render_console, render_markdown, render_plan


class TestAssessment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = assess(helpers.DEMO_PAPER, helpers.DEMO_REPO, smoke=True, use_llm=False)

    def test_verdict_fields(self):
        sc = self.result.scorecard
        self.assertIn(sc.verdict, {"R0", "R1", "R2", "R3"})
        self.assertGreater(len(sc.claims), 0)
        self.assertTrue(sc.summary)

    def test_markdown_has_sections_and_evidence(self):
        md = self.result.markdown
        self.assertIn("# Reproducibility assessment", md)
        self.assertIn("Verdict:", md)
        self.assertIn("## Claim ledger", md)
        self.assertIn("## Claim detail", md)
        self.assertIn("utils/metrics.py", md)
        for claim in self.result.scorecard.claims:
            self.assertIn(claim.id, md)

    def test_plan_has_checkboxes(self):
        plan = self.result.plan
        self.assertIn("- [ ]", plan)
        self.assertIn("Reproduction plan", plan)

    def test_console_summary(self):
        text = render_console(self.result.scorecard)
        self.assertIn("verdict", text)
        self.assertIn(self.result.scorecard.verdict, text)

    def test_json_roundtrip(self):
        payload = json.loads(self.result.to_json())
        self.assertEqual(payload["schema"], "paperrepro/scorecard/v1")
        self.assertEqual(payload["verdict"], self.result.scorecard.verdict)
        self.assertTrue(payload["claims"])
        self.assertIn("findings", payload)

    def test_write_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.result.write(tmp)
            for key in ("report", "scorecard", "plan"):
                self.assertTrue(paths[key].exists(), key)
                self.assertGreater(paths[key].stat().st_size, 100)
            self.assertIn("schema", paths["scorecard"].read_text(encoding="utf-8"))

    def test_rules_only_mode_is_flagged(self):
        self.assertFalse(self.result.scorecard.llm_used)


class TestReportRendering(unittest.TestCase):
    def test_render_accepts_minimal_scorecard(self):
        result = assess(helpers.DEMO_PAPER, helpers.DEMO_REPO, smoke=False, use_llm=False)
        text = render_markdown(result.scorecard)
        self.assertIn("Limits of this report", text)
        self.assertIn("not run", text.lower())

    def test_plan_lists_assets(self):
        result = assess(helpers.DEMO_PAPER, helpers.DEMO_REPO, smoke=True, use_llm=False)
        plan = render_plan(result.scorecard)
        self.assertIn("## 1. Assets", plan)
        self.assertIn("## 2. Claims to reproduce", plan)


if __name__ == "__main__":
    unittest.main()
