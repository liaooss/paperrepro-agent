"""Planning: inferring a runnable recipe from a repository."""

import unittest

import helpers
from paperrepro.ingest.paper import load_paper
from paperrepro.ingest.repo import scan_repo
from paperrepro.plan import PlanError, infer_recipe

PAPER = """# A Paper

## 4 Experiments

We report 91.3 accuracy on SST-2.
"""


class TestInference(unittest.TestCase):
    def _repo(self, files):
        return helpers.make_repo(files)

    def test_readme_command_is_used(self):
        repo = self._repo(
            {
                "README.md": "# demo\n\n```bash\npip install -e .\npython evaluate.py --split test\n```\n",
                "pyproject.toml": "[project]\nname = 'x'\n",
                "evaluate.py": "import argparse\n\nif __name__ == '__main__':\n    pass\n",
            }
        )
        try:
            doc = load_paper(helpers._write_paper(PAPER))
            recipe = infer_recipe(doc, scan_repo(repo))
            self.assertIn("evaluate.py", recipe.eval_cmd)
            self.assertEqual(recipe.source, "inferred")
            self.assertIn("install -e .", recipe.install[0])
        finally:
            helpers.cleanup(repo)

    def test_setup_lines_are_rejected(self):
        repo = self._repo(
            {
                "README.md": "# demo\n```bash\npython -m venv .venv\npython -m pytest tests\n```\n",
                "requirements.txt": "torch==2.1.0\n",
            }
        )
        try:
            doc = load_paper(helpers._write_paper(PAPER))
            with self.assertRaises(PlanError):
                infer_recipe(doc, scan_repo(repo))
        finally:
            helpers.cleanup(repo)

    def test_config_driven_entry_point(self):
        repo = self._repo(
            {
                "README.md": "# demo\n",
                "requirements.txt": "torch==2.1.0\n",
                "train.py": (
                    "import argparse\n"
                    "p = argparse.ArgumentParser()\n"
                    'p.add_argument("--config", default="configs/base.yaml")\n'
                    "if __name__ == '__main__':\n    pass\n"
                ),
                "configs/base.yaml": "lr: 0.1\n",
            }
        )
        try:
            doc = load_paper(helpers._write_paper(PAPER))
            recipe = infer_recipe(doc, scan_repo(repo))
            self.assertIn("--config", recipe.eval_cmd)
            self.assertIn("configs/base.yaml", recipe.eval_cmd)
        finally:
            helpers.cleanup(repo)

    def test_converter_scripts_are_not_experiments(self):
        repo = self._repo(
            {
                "README.md": "# demo\n",
                "requirements.txt": "torch==2.1.0\n",
                "convert_weights.py": "if __name__ == '__main__':\n    pass\n",
                "check_repo.py": "if __name__ == '__main__':\n    pass\n",
            }
        )
        try:
            doc = load_paper(helpers._write_paper(PAPER))
            with self.assertRaises(PlanError):
                infer_recipe(doc, scan_repo(repo))
        finally:
            helpers.cleanup(repo)

    def test_metric_comes_from_the_paper(self):
        repo = self._repo(
            {
                "README.md": "# demo\n```bash\npython eval.py\n```\n",
                "requirements.txt": "torch==2.1.0\n",
                "eval.py": "if __name__ == '__main__':\n    pass\n",
            }
        )
        try:
            doc = load_paper(helpers._write_paper(PAPER))
            recipe = infer_recipe(doc, scan_repo(repo))
            self.assertEqual(recipe.metric, "accuracy")
        finally:
            helpers.cleanup(repo)


if __name__ == "__main__":
    unittest.main()
