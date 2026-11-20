"""Bounded repair: what it fixes, what it refuses to touch, and that it restores."""

import unittest
from pathlib import Path

import helpers
from paperrepro.execute.recipe import Recipe
from paperrepro.execute.repair import (
    RepairPolicy,
    plan_repair,
    restore,
    run_with_repair,
)
from paperrepro.execute.runner import CommandResult, RunResult


def _failed(kind: str, text: str = "") -> RunResult:
    run = RunResult(recipe="t", backend="local", status="failed", failure=kind)
    run.commands = [CommandResult(cmd="x", exit_code=1, duration_s=1.0, stdout=text)]
    return run


class TestPlan(unittest.TestCase):
    def setUp(self):
        self.repo = helpers.make_repo({"requirements.txt": "numpy==1.16.5\ntqdm\n"})
        self.addCleanup(helpers.cleanup, self.repo)

    def test_no_repair_for_successful_run(self):
        run = RunResult(recipe="t", backend="local", status="ok")
        self.assertIsNone(plan_repair(run, self.repo, RepairPolicy(), self.repo / "p"))

    def test_dead_pin_is_unpinned(self):
        run = _failed("ENV_CONFLICT", "ERROR: No matching distribution found for numpy==1.16.5")
        action = plan_repair(run, self.repo, RepairPolicy(), self.repo / "repairs")
        self.assertIsNotNone(action)
        self.assertEqual(action.strategy, "unpin")
        self.assertIn("numpy", (self.repo / "requirements.txt").read_text(encoding="utf-8"))
        self.assertNotIn("numpy==1.16.5", (self.repo / "requirements.txt").read_text(encoding="utf-8"))
        self.assertTrue(Path(action.patch_path).exists())
        self.assertTrue(Path(action.backup_path).exists())

    def test_restore_puts_the_file_back(self):
        run = _failed("ENV_CONFLICT", "No matching distribution found for numpy==1.16.5")
        action = plan_repair(run, self.repo, RepairPolicy(), self.repo / "repairs")
        restore([action], self.repo)
        self.assertIn("numpy==1.16.5", (self.repo / "requirements.txt").read_text(encoding="utf-8"))

    def test_missing_directory_inside_checkout_is_created(self):
        run = _failed("COMMAND_FAILED", "FileNotFoundError: [Errno 2] No such file or directory: 'out/results'")
        action = plan_repair(run, self.repo, RepairPolicy(), self.repo / "repairs")
        self.assertIsNotNone(action)
        self.assertEqual(action.strategy, "mkdir")
        self.assertTrue((self.repo / "out" / "results").exists())

    @unittest.skipIf(helpers.IS_WINDOWS is False, "path escaping differs per platform")
    def test_directory_outside_checkout_is_never_created(self):
        run = _failed("COMMAND_FAILED", "FileNotFoundError: 'C:/Windows/system32/repro-test'")
        self.assertIsNone(plan_repair(run, self.repo, RepairPolicy(), self.repo / "repairs"))

    def test_missing_weights_is_not_repaired(self):
        run = _failed("MISSING_WEIGHTS", "state_dict not found")
        self.assertIsNone(plan_repair(run, self.repo, RepairPolicy(), self.repo / "repairs"))

    def test_policy_can_disable_unpin(self):
        run = _failed("ENV_CONFLICT", "No matching distribution found for numpy==1.16.5")
        policy = RepairPolicy(allow_unpin=False)
        self.assertIsNone(plan_repair(run, self.repo, policy, self.repo / "repairs"))


class TestLoop(unittest.TestCase):
    def test_missing_directory_is_repaired_and_measured(self):
        work = helpers.make_repo({"main.py": "print('unused')\n"})
        self.addCleanup(helpers.cleanup, work)
        recipe = Recipe.from_dict(
            {
                "name": "repair-me",
                "eval_cmd": (
                    '{python} -c "open(\'results/out.txt\',\'w\').write(\'1\'); '
                    "print('accuracy: 0.75')\""
                ),
                "metric": "accuracy",
                "timeout_minutes": 5,
            }
        )
        final, actions, original = run_with_repair(
            recipe, work, work / "out", backend_name="local", policy=RepairPolicy(max_attempts=2)
        )
        self.assertEqual(original.status, "failed")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].strategy, "mkdir")
        self.assertTrue(actions[0].ok)
        self.assertEqual(final.status, "ok", final.failure_detail)
        self.assertAlmostEqual(final.metrics["accuracy"], 0.75)

    def test_repair_disabled_returns_the_original_failure(self):
        work = helpers.make_repo({"main.py": "print('unused')\n"})
        self.addCleanup(helpers.cleanup, work)
        recipe = Recipe.from_dict(
            {
                "name": "no-repair",
                "eval_cmd": '{python} -c "open(\'gone/x.txt\',\'w\').write(\'1\')"',
                "timeout_minutes": 5,
            }
        )
        final, actions, original = run_with_repair(
            recipe, work, work / "out", backend_name="local", policy=RepairPolicy(enabled=False)
        )
        self.assertEqual(actions, [])
        self.assertIsNone(original)
        self.assertEqual(final.status, "failed")


if __name__ == "__main__":
    unittest.main()
