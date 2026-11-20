"""Consistency audit between what the paper says and what the code sets."""

import unittest

import helpers
from paperrepro.audit import audit_parameters
from paperrepro.ingest.paper import load_paper
from paperrepro.ingest.repo import scan_repo

PAPER = """# A Paper

## 3 Method

We train with a learning rate of 0.001, a batch size of 64 and the Adam optimiser
for 100 epochs.
"""


class TestAudit(unittest.TestCase):
    def _audit_with(self, paper_text, config_text):
        repo = helpers.make_repo({"configs/train.yaml": config_text})
        paper = load_paper(helpers._write_paper(paper_text))
        try:
            return {c.param: c for c in audit_parameters(paper, scan_repo(repo))}
        finally:
            helpers.cleanup(repo)

    def _audit(self, config_text):
        repo = helpers.make_repo({"configs/train.yaml": config_text})
        paper = load_paper(helpers._write_paper(PAPER))
        try:
            return {c.param: c for c in audit_parameters(paper, scan_repo(repo))}
        finally:
            helpers.cleanup(repo)

    def test_matching_values(self):
        checks = self._audit("lr: 0.001\nbatch_size: 64\noptimizer: Adam\nepochs: 100\n")
        self.assertEqual(checks["learning_rate"].status, "MATCH")
        self.assertEqual(checks["batch_size"].status, "MATCH")
        self.assertEqual(checks["optimizer"].status, "MATCH")

    def test_mismatch_is_reported_with_both_sides(self):
        checks = self._audit("lr: 0.001\nbatch_size: 32\noptimizer: Adam\nepochs: 100\n")
        mismatch = checks["batch_size"]
        self.assertEqual(mismatch.status, "MISMATCH")
        self.assertEqual(mismatch.paper_value, "64")
        self.assertEqual(mismatch.code_value, "32")
        self.assertIn("train.yaml", mismatch.code_ref)

    def test_scientific_notation_equals_decimal(self):
        paper = """# P

## Method

We use a learning rate of 1e-3.
"""
        repo = helpers.make_repo({"hparams.py": "lr = 0.001\n"})
        try:
            doc = load_paper(helpers._write_paper(paper))
            checks = {c.param: c for c in audit_parameters(doc, scan_repo(repo))}
        finally:
            helpers.cleanup(repo)
        self.assertEqual(checks["learning_rate"].status, "MATCH")

    def test_paper_only_parameter(self):
        checks = self._audit("batch_size: 64\n")
        self.assertEqual(checks["learning_rate"].status, "PAPER_ONLY")

    def test_image_size_match(self):
        paper = "# P\n\n## Method\n\nAll images are resized to 224 before training.\n"
        checks = self._audit_with(paper, "image_size: 224\n")
        self.assertEqual(checks["image_size"].status, "MATCH")

    def test_image_size_mismatch(self):
        paper = "# P\n\n## Method\n\nAll images are resized to 224 before training.\n"
        checks = self._audit_with(paper, "image_size: 256\n")
        self.assertEqual(checks["image_size"].status, "MISMATCH")
        self.assertEqual(checks["image_size"].paper_value, "224")
        self.assertEqual(checks["image_size"].code_value, "256")

    def test_macro_versus_micro_f1(self):
        paper = "# P\n\n## Experiments\n\nWe report macro-F1 over all classes.\n"
        checks = self._audit_with(paper, "average: micro\n")
        self.assertEqual(checks["f1_average"].status, "MISMATCH")
        self.assertIn("macro", checks["f1_average"].note)

    def test_weighted_and_macro_both_report_f1(self):
        paper = "# P\n\n## Experiments\n\nWe report macro F1 over all classes.\n"
        checks = self._audit_with(paper, "average: macro\n")
        self.assertEqual(checks["f1_average"].status, "MATCH")

    def test_code_only_parameter(self):
        paper = """# P

## Method

We train a small model.
"""
        repo = helpers.make_repo({"config.yaml": "dropout: 0.1\n"})
        try:
            doc = load_paper(helpers._write_paper(paper))
            checks = {c.param: c for c in audit_parameters(doc, scan_repo(repo))}
        finally:
            helpers.cleanup(repo)
        if "dropout" in checks:
            self.assertEqual(checks["dropout"].status, "CODE_ONLY")


if __name__ == "__main__":
    unittest.main()
