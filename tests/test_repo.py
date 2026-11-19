"""Repository scanning."""

import unittest

import helpers
from reprocheck.ingest.repo import scan_repo


class TestDemoRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scan = scan_repo(helpers.DEMO_REPO)

    def test_core_files_present(self):
        paths = {f.path for f in self.scan.files}
        self.assertIn("train.py", paths)
        self.assertIn("evaluate.py", paths)
        self.assertIn("configs/tinyclip.yaml", paths)
        self.assertNotIn("__pycache__", " ".join(paths))

    def test_readme_and_manifest(self):
        self.assertEqual(self.scan.readme_path, "README.md")
        self.assertIn("requirements.txt", self.scan.manifests)

    def test_entry_points(self):
        self.assertTrue(any(p.startswith("train.py") for p in self.scan.entry_points))

    def test_seed_control_detected(self):
        self.assertTrue(any("train.py" in ref for ref in self.scan.seed_refs))

    def test_absolute_paths_detected(self):
        paths = {item["path"] for item in self.scan.absolute_paths}
        self.assertIn("/data/imagenet", paths)

    def test_config_files(self):
        self.assertIn("configs/tinyclip.yaml", self.scan.config_files)

    def test_metric_definition_preferred_over_import(self):
        refs = self.scan.metric_refs.get("accuracy", [])
        self.assertTrue(refs)
        self.assertTrue(refs[0].startswith("utils/metrics.py"), refs[0])

    def test_language_counts(self):
        counts = self.scan.lang_counts()
        self.assertGreaterEqual(counts.get("python", 0), 5)


class TestSyntheticRepo(unittest.TestCase):
    def test_checkpoint_reference_detected_when_absent(self):
        repo = helpers.make_repo(
            {
                "main.py": "import torch\nckpt = 'checkpoints/model.pt'\n",
                "README.md": "# demo\npip install -r requirements.txt\n",
                "requirements.txt": "torch==2.1.0\n",
            }
        )
        try:
            scan = scan_repo(repo)
            self.assertEqual(len(scan.checkpoint_refs), 1)
            self.assertIn("model.pt", scan.checkpoint_refs[0]["path"])
        finally:
            helpers.cleanup(repo)

    def test_checkpoint_reference_ignored_when_present(self):
        repo = helpers.make_repo(
            {
                "main.py": "ckpt = 'checkpoints/model.pt'\n",
                "checkpoints/model.pt": "not really a checkpoint",
                "README.md": "# demo\npip install -r requirements.txt\n",
            }
        )
        try:
            scan = scan_repo(repo)
            self.assertEqual(scan.checkpoint_refs, [])
        finally:
            helpers.cleanup(repo)

    def test_notebook_only_detection(self):
        repo = helpers.make_repo({"analysis.ipynb": '{"cells": []}'})
        try:
            scan = scan_repo(repo)
            self.assertTrue(scan.notebook_only)
        finally:
            helpers.cleanup(repo)

    def test_missing_repo_raises(self):
        with self.assertRaises(NotADirectoryError):
            scan_repo("does/not/exist")


if __name__ == "__main__":
    unittest.main()
