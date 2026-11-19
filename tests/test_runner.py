"""Execution runner: command recording and failure classification."""

import tempfile
import unittest
from pathlib import Path

import helpers
from paperrepro.execute.recipe import Recipe
from paperrepro.execute.runner import classify_failure, execute_recipe


class TestClassification(unittest.TestCase):
    CASES = {
        "ENV_CONFLICT": 'ERROR: Could not find a version that satisfies the requirement torch==9.9',
        "MISSING_WEIGHTS": "FileNotFoundError: [Errno 2] No such file or directory: 'ckpt/model.pt'",
        "DATA_UNAVAILABLE": "requests.exceptions.HTTPError: 404 Client Error: Not Found for url",
        "OOM": "RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB",
        "NETWORK": "ConnectionError: Max retries exceeded with url",
    }

    def test_known_kinds(self):
        for expected, text in self.CASES.items():
            kind, line = classify_failure(text)
            self.assertEqual(kind, expected, text)
            self.assertTrue(line)

    def test_unknown_kind(self):
        kind, line = classify_failure("Segmentation fault (core dumped)")
        self.assertEqual(kind, "COMMAND_FAILED")
        self.assertEqual(line, "")


class TestExecute(unittest.TestCase):
    def _workdir(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_metric_is_parsed_and_logged(self):
        work = self._workdir()
        out = work / "out"
        recipe = Recipe.from_dict(
            {
                "name": "smoke",
                "eval_cmd": '{python} -c "print(\'accuracy: 0.9130\')"',
                "metric": "accuracy",
                "metric_regex": r"accuracy:\s*(?P<value>\d+\.\d+)",
                "timeout_minutes": 5,
            }
        )
        run = execute_recipe(recipe, work, out, backend_name="local")
        self.assertEqual(run.status, "ok", run.failure_detail)
        self.assertAlmostEqual(run.metrics["accuracy"], 0.913)
        self.assertTrue((out / "run.json").exists())
        self.assertTrue((out / "commands.jsonl").exists())
        self.assertTrue(Path(run.commands[-1].log_path).exists())

    def test_failure_is_classified_and_recorded(self):
        work = self._workdir()
        recipe = Recipe.from_dict(
            {
                "name": "fails",
                "eval_cmd": '{python} -c "import sys; print(\'boom\'); sys.exit(4)"',
                "timeout_minutes": 5,
            }
        )
        run = execute_recipe(recipe, work, work / "out", backend_name="local")
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.failure, "COMMAND_FAILED")
        self.assertEqual(run.commands[-1].exit_code, 4)

    def test_no_metric_is_a_failure_not_a_pass(self):
        work = self._workdir()
        recipe = Recipe.from_dict(
            {"name": "silent", "eval_cmd": '{python} -c "print(\'done\')"', "timeout_minutes": 5}
        )
        run = execute_recipe(recipe, work, work / "out", backend_name="local")
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.failure, "NO_METRIC_PARSED")

    def test_unknown_backend(self):
        work = self._workdir()
        recipe = Recipe.from_dict({"name": "x", "eval_cmd": "true"})
        run = execute_recipe(recipe, work, work / "out", backend_name="kubernetes")
        self.assertEqual(run.status, "error")
        self.assertEqual(run.failure, "BACKEND_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
