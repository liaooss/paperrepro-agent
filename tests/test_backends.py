"""Backend selection, and what happens when the requested isolation is unavailable.

The Docker *success* path cannot be exercised on a machine without a running
engine, but the *failure* path can - and it is the one a user hits first, so it
must produce an actionable message rather than a traceback.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
from paperrepro.execute.backends import BackendError, DockerBackend, LocalBackend, get_backend
from paperrepro.execute.recipe import Recipe
from paperrepro.execute.runner import execute_recipe


def _recipe():
    return Recipe.from_dict({"name": "t", "eval_cmd": "true", "timeout_minutes": 5})


class TestSelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.artifacts = self.work / "artifacts"

    def test_local_backend(self):
        backend = get_backend("local", self.work, _recipe(), self.artifacts)
        self.assertIsInstance(backend, LocalBackend)

    def test_unknown_backend(self):
        with self.assertRaises(BackendError):
            get_backend("kubernetes", self.work, _recipe(), self.artifacts)

    def test_missing_docker_cli_is_actionable(self):
        backend = get_backend("docker", self.work, _recipe(), self.artifacts)
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(BackendError) as ctx:
                backend.prepare()
        message = str(ctx.exception)
        self.assertIn("Docker Desktop", message)
        self.assertIn("--backend local", message)

    def test_stopped_docker_daemon_is_actionable(self):
        backend = DockerBackend(self.work, _recipe(), self.artifacts)
        failed = mock.Mock(ok=False, tail=lambda _n=0: "Cannot connect to the Docker daemon")
        with mock.patch("shutil.which", return_value="docker"), mock.patch.object(
            backend, "_spawn", return_value=failed
        ):
            with self.assertRaises(BackendError) as ctx:
                backend.prepare()
        self.assertIn("daemon is not reachable", str(ctx.exception))


class TestRunnerReportsBackendFailure(unittest.TestCase):
    def test_docker_unavailable_becomes_a_clean_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            run = execute_recipe(_recipe(), work, work / "out", backend_name="docker")
        self.assertEqual(run.status, "error")
        self.assertEqual(run.failure, "BACKEND_UNAVAILABLE")
        self.assertIn("docker", run.failure_detail.lower())


if __name__ == "__main__":
    unittest.main()
