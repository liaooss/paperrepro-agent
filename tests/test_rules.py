"""Deterministic risk rules."""

import unittest

import helpers
from reprocheck.extract.claims import extract_claims
from reprocheck.ingest.paper import load_paper
from reprocheck.ingest.repo import scan_repo
from reprocheck.risk.rules import RULES, run_rules


def _ids(findings):
    return {f.rule_id for f in findings}


class TestRulesOnDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scan = scan_repo(helpers.DEMO_REPO)
        cls.doc = load_paper(helpers.DEMO_PAPER)
        cls.claims = extract_claims(cls.doc)
        for claim in cls.claims:
            claim.level = "E2" if claim.metric != "map" else "X"
        cls.findings = run_rules(cls.scan, cls.doc, cls.claims)

    def test_unpinned_dependencies(self):
        self.assertIn("RC02", _ids(self.findings))

    def test_absolute_paths(self):
        self.assertIn("RC03", _ids(self.findings))

    def test_undeclared_import(self):
        self.assertIn("RC13", _ids(self.findings))

    def test_no_false_blockers(self):
        blockers = [f for f in self.findings if f.severity == "blocker"]
        self.assertEqual(blockers, [])

    def test_present_assets_do_not_raise_rules(self):
        ids = _ids(self.findings)
        # The demo repo has a README, a config, seeds and entry points.
        self.assertNotIn("RC01", ids)
        self.assertNotIn("RC06", ids)
        self.assertNotIn("RC07", ids)
        self.assertNotIn("RC09", ids)

    def test_unmatched_claims_raise_rc17(self):
        self.assertIn("RC17", _ids(self.findings))

    def test_findings_sorted_by_severity(self):
        order = {"blocker": 0, "major": 1, "minor": 2, "info": 3}
        severities = [order[f.severity] for f in self.findings]
        self.assertEqual(severities, sorted(severities))


class TestRuleCatalog(unittest.TestCase):
    def test_ids_unique_and_documented(self):
        ids = [r[0] for r in RULES]
        self.assertEqual(len(ids), len(set(ids)))
        for rule_id, title, severity in RULES:
            self.assertRegex(rule_id, r"^RC\d{2}$")
            self.assertIn(severity, {"blocker", "major", "minor", "info"})
            self.assertTrue(title)


class TestIndividualRules(unittest.TestCase):
    def _scan_with(self, files):
        return scan_repo(helpers.make_repo(files))

    def test_missing_manifest(self):
        repo = helpers.make_repo({"main.py": "print('hi')\n"})
        try:
            scan = scan_repo(repo)
            doc = load_paper(helpers.DEMO_PAPER)
            ids = _ids(run_rules(scan, doc, []))
            self.assertIn("RC01", ids)
            self.assertIn("RC16", ids)  # no README either
        finally:
            helpers.cleanup(repo)

    def test_restricted_data_is_author_blocker(self):
        repo = helpers.make_repo(
            {
                "README.md": "# demo\nPlease request access to the dataset by email.\n",
                "requirements.txt": "torch==2.1.0\n",
                "main.py": "print('hi')\n",
            }
        )
        try:
            scan = scan_repo(repo)
            doc = load_paper(helpers.DEMO_PAPER)
            findings = run_rules(scan, doc, [])
            rc05 = [f for f in findings if f.rule_id == "RC05"]
            self.assertEqual(len(rc05), 1)
            self.assertTrue(rc05[0].author_dependent)
            self.assertEqual(rc05[0].severity, "blocker")
        finally:
            helpers.cleanup(repo)

    def test_missing_checkpoint_is_author_blocker(self):
        repo = helpers.make_repo(
            {
                "README.md": "# demo\npip install -r requirements.txt\n",
                "requirements.txt": "torch==2.1.0\n",
                "eval.py": "ckpt = 'weights/best.pt'\nprint(ckpt)\n",
            }
        )
        try:
            scan = scan_repo(repo)
            findings = run_rules(scan, load_paper(helpers.DEMO_PAPER), [])
            rc04 = [f for f in findings if f.rule_id == "RC04"]
            self.assertEqual(len(rc04), 1)
            self.assertTrue(rc04[0].author_dependent)
        finally:
            helpers.cleanup(repo)

    def test_notebook_only_rule(self):
        repo = helpers.make_repo(
            {
                "README.md": "# demo\nopen the notebook\n",
                "analysis.ipynb": '{"cells": []}',
            }
        )
        try:
            scan = scan_repo(repo)
            ids = _ids(run_rules(scan, load_paper(helpers.DEMO_PAPER), []))
            self.assertIn("RC14", ids)
        finally:
            helpers.cleanup(repo)


if __name__ == "__main__":
    unittest.main()
