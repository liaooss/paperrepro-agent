"""Command line behaviour, exercised as a real process."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import helpers

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(helpers.SRC)
ENV["PYTHONIOENCODING"] = "utf-8"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "reprocheck", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=ENV,
        cwd=str(helpers.ROOT),
        timeout=180,
    )


class TestAssessCommand(unittest.TestCase):
    def test_writes_three_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli(
                "assess",
                str(helpers.DEMO_PAPER),
                "--repo",
                str(helpers.DEMO_REPO),
                "--smoke",
                "--out",
                tmp,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            for name in ("report.md", "scorecard.json", "reproduction_plan.md"):
                self.assertTrue((Path(tmp) / name).exists(), name)
            self.assertIn("verdict", proc.stdout.lower())

    def test_json_output_is_parseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli(
                "assess",
                str(helpers.DEMO_PAPER),
                "--repo",
                str(helpers.DEMO_REPO),
                "--out",
                tmp,
                "--json",
                "--no-llm",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["schema"], "reprocheck/scorecard/v1")

    def test_quiet_suppresses_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli(
                "assess",
                str(helpers.DEMO_PAPER),
                "--repo",
                str(helpers.DEMO_REPO),
                "--out",
                tmp,
                "--quiet",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(), "")

    def test_fail_on_trips_for_weak_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli(
                "assess",
                str(helpers.DEMO_PAPER),
                "--repo",
                str(helpers.DEMO_REPO),
                "--out",
                tmp,
                "--fail-on",
                "R3",
            )
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_missing_paper_is_a_clean_error(self):
        proc = run_cli("assess", "nope.tex", "--repo", str(helpers.DEMO_REPO))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("error", proc.stderr.lower())

    def test_bad_repo_path_is_a_clean_error(self):
        proc = run_cli("assess", str(helpers.DEMO_PAPER), "--repo", "does/not/exist")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("error", proc.stderr.lower())


class TestOtherCommands(unittest.TestCase):
    def test_rules_lists_catalogue(self):
        proc = run_cli("rules")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("RC01", proc.stdout)
        self.assertIn("RC17", proc.stdout)

    def test_version(self):
        proc = run_cli("version")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("reprocheck", proc.stdout)

    def test_help_without_args(self):
        proc = run_cli()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("assess", proc.stdout)


if __name__ == "__main__":
    unittest.main()
