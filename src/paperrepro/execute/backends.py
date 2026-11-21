"""Execution backends: where the release's commands actually run.

Isolation matters because research code is written for one machine and one
moment. A recipe that installs into the analyst's global environment can break
their machine, and can never be audited afterwards. Every backend therefore
builds a disposable environment and records every command it runs.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .recipe import Recipe

__all__ = [
    "Backend",
    "BackendError",
    "CommandResult",
    "LocalBackend",
    "CondaBackend",
    "DockerBackend",
    "get_backend",
    "substitute",
]


class BackendError(RuntimeError):
    """Raised when the requested isolation cannot be provided."""


@dataclass
class CommandResult:
    cmd: str
    exit_code: int
    duration_s: float
    stdout: str = ""
    stderr: str = ""
    log_path: str = ""
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def tail(self, limit: int = 2000) -> str:
        text = (self.stdout or "") + ("\n" + self.stderr if self.stderr else "")
        return text[-limit:]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cmd": self.cmd,
            "exit_code": self.exit_code,
            "duration_s": round(self.duration_s, 2),
            "timed_out": self.timed_out,
            "log_path": self.log_path,
        }


def substitute(cmd: str, python_exe: str) -> str:
    """Expand ``{python}`` and ``{pip}`` with the audited interpreter."""
    quoted = f'"{python_exe}"'
    return cmd.replace("{python}", quoted).replace("{pip}", f"{quoted} -m pip")


class Backend:
    name = "base"
    isolation = "none"

    def __init__(self, workdir: Path, recipe: Recipe, artifacts: Path) -> None:
        self.workdir = Path(workdir)
        self.recipe = recipe
        self.artifacts = Path(artifacts)
        self._python = sys.executable
        self.prepared = False

    # -- interface -------------------------------------------------------- #
    def prepare(self) -> list[CommandResult]:
        raise NotImplementedError

    def python_exe(self) -> str:
        return self._python

    def run(self, cmd: str, timeout_s: int, log_name: str, env: dict[str, str] | None = None) -> CommandResult:
        raise NotImplementedError

    def close(self) -> None:
        return None

    # -- helpers ---------------------------------------------------------- #
    def _base_env(self) -> dict[str, str]:
        """Caches live inside the run directory.

        Two reasons: the analyst's home is often read-only to the sandbox, and a
        shared cache makes "it worked yesterday" impossible to audit.
        """
        return {
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HOME": str(self.workdir / ".hf-cache"),
            "HF_HUB_CACHE": str(self.workdir / ".hf-cache" / "hub"),
            "TORCH_HOME": str(self.workdir / ".torch-cache"),
            "MPLCONFIGDIR": str(self.workdir / ".mpl-cache"),
            "TRANSFORMERS_CACHE": str(self.workdir / ".hf-cache" / "hub"),
        }

    def _record(self, result: CommandResult, log_name: str) -> CommandResult:
        self.artifacts.mkdir(parents=True, exist_ok=True)
        path = self.artifacts / f"{log_name}.log"
        body = [
            f"$ {result.cmd}",
            f"exit={result.exit_code} duration={result.duration_s:.1f}s timed_out={result.timed_out}",
            "",
            result.stdout or "",
            ("[stderr]\n" + result.stderr) if result.stderr else "",
        ]
        path.write_text("\n".join(body), encoding="utf-8")
        result.log_path = str(path)
        return result

    @staticmethod
    def _spawn(cmd: str, cwd: Path, timeout_s: int, env: dict[str, str] | None) -> CommandResult:
        started = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(1, timeout_s),
                env=env,
            )
            return CommandResult(
                cmd=cmd,
                exit_code=proc.returncode,
                duration_s=time.time() - started,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
            )
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout or ""
            err = exc.stderr or ""
            if isinstance(out, bytes):
                out = out.decode("utf-8", "replace")
            if isinstance(err, bytes):
                err = err.decode("utf-8", "replace")
            return CommandResult(
                cmd=cmd,
                exit_code=124,
                duration_s=time.time() - started,
                stdout=out,
                stderr=err,
                timed_out=True,
            )


class LocalBackend(Backend):
    """A virtualenv under the run directory. No containers, no network tricks."""

    name = "local"
    isolation = "venv"

    def prepare(self) -> list[CommandResult]:
        venv_dir = self.workdir / ".paperrepro-venv"
        if not venv_dir.exists():
            result = self._spawn(
                f'"{sys.executable}" -m venv "{venv_dir}"',
                self.workdir,
                600,
                os.environ.copy(),
            )
            self._record(result, "00-create-venv")
            if not result.ok:
                raise BackendError(f"could not create a virtualenv: {result.tail(400)}")
        self._python = self._venv_python(venv_dir)
        if not Path(self._python).exists():
            raise BackendError(f"virtualenv has no interpreter at {self._python}")
        self.prepared = True
        return []

    @staticmethod
    def _venv_python(venv_dir: Path) -> str:
        if os.name == "nt":
            return str(venv_dir / "Scripts" / "python.exe")
        return str(venv_dir / "bin" / "python")

    def run(self, cmd: str, timeout_s: int, log_name: str, env: dict[str, str] | None = None) -> CommandResult:
        merged = os.environ.copy()
        merged.update(self._base_env())
        if env:
            merged.update(env)
        result = self._spawn(substitute(cmd, self._python), self.workdir, timeout_s, merged)
        return self._record(result, log_name)


class CondaBackend(Backend):
    """A conda environment at a fixed prefix. Useful for pinned Python versions."""

    name = "conda"
    isolation = "conda"

    def _conda(self) -> str:
        for candidate in (os.environ.get("CONDA_EXE"), shutil.which("conda"), shutil.which("conda.bat")):
            if candidate and Path(candidate).exists():
                return str(candidate)
        default = Path(sys.prefix) / "Scripts" / "conda.exe"
        if default.exists():
            return str(default)
        raise BackendError("conda not found; use --backend local or --backend docker")

    def prepare(self) -> list[CommandResult]:
        conda = self._conda()
        env_dir = self.workdir / ".paperrepro-conda"
        if not env_dir.exists():
            result = self._spawn(
                f'"{conda}" create -p "{env_dir}" "python={self.recipe.python}" -y',
                self.workdir,
                1800,
                os.environ.copy(),
            )
            self._record(result, "00-create-conda-env")
            if not result.ok:
                raise BackendError(f"conda could not create the environment: {result.tail(600)}")
        self._python = str(env_dir / ("python.exe" if os.name == "nt" else "bin/python"))
        if not Path(self._python).exists():
            raise BackendError(f"conda environment has no interpreter at {self._python}")
        self.prepared = True
        return []

    def run(self, cmd: str, timeout_s: int, log_name: str, env: dict[str, str] | None = None) -> CommandResult:
        merged = os.environ.copy()
        merged.update(self._base_env())
        if env:
            merged.update(env)
        result = self._spawn(substitute(cmd, self._python), self.workdir, timeout_s, merged)
        return self._record(result, log_name)


class DockerBackend(Backend):
    """A per-recipe image built from the release's own directory.

    The image is built once per recipe (``docker build``), so ``pip install`` in
    the recipe becomes part of the image and later commands reuse it.
    """

    name = "docker"
    isolation = "container"

    def _docker(self) -> str:
        exe = shutil.which("docker")
        if not exe:
            raise BackendError(
                "docker not found. Install Docker Desktop (needs administrator) and make sure "
                "`docker info` succeeds, or use --backend local."
            )
        probe = self._spawn(f'"{exe}" info --format "{{{{.ServerVersion}}}}"', self.workdir, 60, os.environ.copy())
        if not probe.ok:
            raise BackendError(
                "the Docker daemon is not reachable. Start Docker Desktop, then retry; "
                f"probe said: {probe.tail(300)}"
            )
        return exe

    def __init__(self, workdir: Path, recipe: Recipe, artifacts: Path, gpu: bool = False) -> None:
        super().__init__(workdir, recipe, artifacts)
        self.gpu = gpu
        # Deterministic name: Python's str hash is salted per process, which
        # would rebuild the image on every run.
        digest = hashlib.sha1(recipe.name.encode("utf-8")).hexdigest()[:8]
        self.image = f"paperrepro-{digest}"

    def prepare(self) -> list[CommandResult]:
        docker = self._docker()
        # Recipe commands use {python}/{pip} placeholders; inside an image both
        # resolve to the image's own interpreter.
        steps = "\n".join(f"RUN {substitute(cmd, 'python')}" for cmd in self.recipe.install)
        dockerfile = (
            f"FROM python:{self.recipe.python}-slim\n"
            "ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends git curl \\\n"
            "    && rm -rf /var/lib/apt/lists/*\n"
            "WORKDIR /work\n"
            f"COPY . /work\n"
            f"{steps}\n"
        )
        (self.workdir / "Dockerfile.paperrepro").write_text(dockerfile, encoding="utf-8")

        # Keep the build context sane: a transformed checkout can carry a venv,
        # a git history and model caches, none of which belong in an image.
        ignore = self.workdir / ".dockerignore"
        ignore.write_text(
            "\n".join(
                [
                    ".git",
                    ".paperrepro-venv",
                    ".paperrepro-harness",
                    ".paperrepro-conda",
                    ".hf-cache",
                    ".torch-cache",
                    ".mpl-cache",
                    "data",
                    "__pycache__",
                    "*.pyc",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        build = self._build(docker, os.environ.copy())
        build = self._record(build, "00-docker-build")
        if not build.ok and _is_registry_failure(build.tail(4000)):
            # BuildKit resolves the base image over its own network stack; on
            # some networks that path fails while `docker pull` works. The
            # legacy builder uses the local image store, so retry once there.
            legacy_env = os.environ.copy()
            legacy_env["DOCKER_BUILDKIT"] = "0"
            build = self._record(self._build(docker, legacy_env), "00-docker-build-legacy")
        if not build.ok:
            raise BackendError(f"docker build failed: {build.tail(800)}")
        self._python = "python"
        self.prepared = True
        return [build]

    def _build(self, docker: str, env: dict[str, str]) -> CommandResult:
        dockerfile = (self.workdir / "Dockerfile.paperrepro").as_posix()
        context = self.workdir.as_posix()
        return self._spawn(
            f'"{docker}" build -f "{dockerfile}" -t {self.image} "{context}"',
            self.workdir,
            3600,
            env,
        )

    def run(self, cmd: str, timeout_s: int, log_name: str, env: dict[str, str] | None = None) -> CommandResult:
        docker = shutil.which("docker") or "docker"
        gpu = "--gpus all " if self.gpu else ""
        extra = {
            "HF_HOME": "/work/.hf-cache",
            "HF_HUB_CACHE": "/work/.hf-cache/hub",
            "TORCH_HOME": "/work/.torch-cache",
            "PYTHONUNBUFFERED": "1",
        }
        extra.update(env or {})
        env_flags = " ".join(f'-e {k}="{v}"' for k, v in extra.items())
        inner = substitute(cmd, "python")
        mount = self.workdir.as_posix()
        full = (
            f'"{docker}" run --rm {gpu}-v "{mount}:/work" -w /work {env_flags} '
            f'{self.image} bash -lc "{inner}"'
        )
        result = self._spawn(full, self.workdir, timeout_s, os.environ.copy())
        return self._record(result, log_name)


def _is_registry_failure(text: str) -> bool:
    """A base-image fetch failure, as opposed to a build that actually broke."""
    lowered = (text or "").lower()
    markers = (
        "failed to fetch oauth token",
        "failed to resolve source metadata",
        "failed to solve",
        "no such host",
        "dial tcp",
        "tls handshake timeout",
    )
    return any(marker in lowered for marker in markers)


def get_backend(name: str, workdir: Path, recipe: Recipe, artifacts: Path, gpu: bool = False) -> Backend:
    name = (name or "local").lower()
    if name == "local":
        return LocalBackend(workdir, recipe, artifacts)
    if name == "conda":
        return CondaBackend(workdir, recipe, artifacts)
    if name == "docker":
        return DockerBackend(workdir, recipe, artifacts, gpu=gpu)
    raise BackendError(f"unknown backend '{name}' (choose local, conda or docker)")
