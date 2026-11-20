"""Multi-seed execution: spread, not a single number."""

import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from paperrepro.execute.recipe import Recipe
from paperrepro.execute.seeds import run_seeds, seed_command


def _recipe(seeds=None):
    return Recipe.from_dict(
        {
            "name": "seed-demo",
            "eval_cmd": "{python} -c \"print(f'accuracy: {0.90 + {seed}/1000:.3f}')\"",
            "metric": "accuracy",
            "metric_regex": r"accuracy:\s*(?P<value>\d+\.\d+)",
            "timeout_minutes": 5,
            "seeds": seeds or [],
        }
    )


class TestSeedCommand(unittest.TestCase):
    def test_placeholder_replaced(self):
        self.assertIn("42", seed_command(_recipe(), 42))

    def test_flag_appended_when_no_placeholder(self):
        recipe = Recipe.from_dict({"name": "x", "eval_cmd": "{python} run.py"})
        self.assertEqual(seed_command(recipe, 7), "{python} run.py --seed 7")

    def test_custom_flag(self):
        recipe = Recipe.from_dict({"name": "x", "eval_cmd": "{python} run.py", "seed_flag": "--random-seed"})
        self.assertIn("--random-seed 9", seed_command(recipe, 9))


class TestRunSeeds(unittest.TestCase):
    def test_mean_and_std(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            run, summary = run_seeds(_recipe(), work, work / "out", [10, 14], backend_name="local")
        self.assertEqual(run.status, "ok", run.failure_detail)
        self.assertEqual(summary.ok, 2)
        self.assertAlmostEqual(summary.mean["accuracy"], 0.912, places=3)
        self.assertAlmostEqual(summary.std["accuracy"], 0.002, places=3)
        self.assertAlmostEqual(run.metrics["accuracy"], 0.912, places=3)
        self.assertEqual(sorted(summary.per_seed), [10, 14])

    def test_failed_seed_does_not_poison_the_rest(self):
        recipe = Recipe.from_dict(
            {
                "name": "partial",
                "eval_cmd": "{python} -c \"import sys; print('accuracy: 0.8'); sys.exit(0 if {seed} != 99 else 1)\"",
                "metric": "accuracy",
                "metric_regex": r"accuracy:\s*(?P<value>\d+\.\d+)",
                "timeout_minutes": 5,
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            run, summary = run_seeds(recipe, work, work / "out", [1, 99], backend_name="local")
        self.assertEqual(summary.ok, 1)
        self.assertEqual(summary.total, 2)
        self.assertEqual(run.status, "ok")

    def test_all_failed_is_a_failure(self):
        recipe = Recipe.from_dict(
            {"name": "bad", "eval_cmd": '{python} -c "import sys; sys.exit(2)"', "timeout_minutes": 5}
        )
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            run, summary = run_seeds(recipe, work, work / "out", [1, 2], backend_name="local")
        self.assertEqual(summary.ok, 0)
        self.assertEqual(run.status, "failed")


if __name__ == "__main__":
    unittest.main()
