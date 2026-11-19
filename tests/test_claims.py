"""Claim extraction from tables and prose."""

import unittest

import helpers
from paperrepro.extract.claims import extract_claims
from paperrepro.ingest.paper import load_paper


class TestLatexClaims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claims = extract_claims(load_paper(helpers.TEX_PAPER))

    def test_ids_are_unique(self):
        ids = [c.id for c in self.claims]
        self.assertEqual(len(ids), len(set(ids)))

    def test_table_rows_become_claims(self):
        values = {c.value for c in self.claims}
        self.assertIn("95.3", values)  # ours
        self.assertIn("94.1", values)  # baseline

    def test_roles_split_paper_and_reference(self):
        paper = [c for c in self.claims if c.role == "paper"]
        reference = [c for c in self.claims if c.role == "reference"]
        self.assertTrue(any(c.value == "95.3" for c in paper))
        self.assertTrue(any(c.value == "94.1" for c in reference))

    def test_dataset_from_caption(self):
        table_claims = [c for c in self.claims if c.row_label in ("Ours", "ResNet-18")]
        self.assertTrue(table_claims)
        for claim in table_claims:
            self.assertEqual(claim.dataset, "cifar10")

    def test_every_claim_has_paper_evidence(self):
        for claim in self.claims:
            self.assertTrue(claim.evidence, claim.id)
            self.assertEqual(claim.evidence[0].kind, "paper")


class TestMarkdownClaims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claims = extract_claims(load_paper(helpers.DEMO_PAPER))

    def test_table_claims(self):
        pairs = {(c.metric, c.value) for c in self.claims}
        self.assertIn(("accuracy", "72.3"), pairs)
        self.assertIn(("zero_shot_accuracy", "45.1"), pairs)

    def test_prose_claim_is_extracted(self):
        map_claims = [c for c in self.claims if c.metric == "map"]
        self.assertEqual(len(map_claims), 1)
        self.assertEqual(map_claims[0].value, "0.41")
        self.assertEqual(map_claims[0].dataset, "coco")

    def test_no_duplicates(self):
        keys = [(c.metric, c.value, c.dataset) for c in self.claims]
        self.assertEqual(len(keys), len(set(keys)))

    def test_baseline_rows_are_context_only(self):
        reference = [c for c in self.claims if c.role == "reference"]
        self.assertEqual(len(reference), 2)
        self.assertTrue(all(c.value in {"68.3", "43.3"} for c in reference))


if __name__ == "__main__":
    unittest.main()
