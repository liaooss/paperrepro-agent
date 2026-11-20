"""Execute a recipe and keep every artifact needed to argue about the result."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .backends import BackendError, CommandResult, get_backend
from .parse import extract_metrics
from .recipe import Recipe

__all__ = ["RunResult", "execute_recipe", "classify_failure", "FAILURE_KINDS"]

# Failure taxonomy. The point is that each kind maps to a different remedy, so
# "it crashed" is never the conclusion.
FAILURE_KINDS: dict[str, list[str]] = {
    "ENV_CONFLICT": [
        r"No matching distribution",
        r"Could not find a version that satisfies",
        r"ResolutionImpossible",
        r"unsatisfiable",
        r"ERROR: pip's dependency resolver",
        r"has requirement .* but you have",
        r"PackagesNotFoundError",
    ],
    "MISSING_WEIGHTS": [
        r"No such file or directory[^\n]*\.(?:pt|pth|ckpt|bin|safetensors|h5|onnx)",
        r"state_dict",
        r"checkpoint[^\n]{0,40}not found",
        r"Error\(s\) in loading state_dict",
    ],
    "DATA_UNAVAILABLE": [
        r"404 Client Error",
        r"HTTP Error 403",
        r"Dataset .{0,40}not found",
        r"PermissionError",
        r"AccessDenied",
        r"Permission denied",
    ],
    "OOM": [r"CUDA out of memory", r"OutOfMemoryError", r"DefaultCPUAllocator", r"Killed"],
    "NETWORK": [
        r"Temporary failure in name resolution",
        r"ConnectionError",
        r"Max retries exceeded",
        r"ProxyError",
        r"SSLError",
    ],
}


@dataclass
class RunResult:
    recipe: str
    backend: str
    status: str = "failed"  # ok | failed | timeout | error
    failure: str = ""
    failure_detail: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    commands: list[CommandResult] = field(default_factory=list)
    duration_s: float = 0.0
    disk_gb: float = 0.0
    artifacts: str = ""
    workdir: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok" and bool(self.metrics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe": self.recipe,
            "backend": self.backend,
            "status": self.status,
            "failure": self.failure,
            "failure_detail": self.failure_detail,
            "metrics": self.metrics,
            "duration_s": round(self.duration_s, 1),
            "disk_gb": round(self.disk_gb, 2),
            "artifacts": self.artifacts,
            "workdir": self.workdir,
            "commands": [c.to_dict() for c in self.commands],
        }


def classify_failure(text: str) -> tuple[str, str]:
    """Map a log tail to (kind, first concrete line that proves it)."""
    for kind, patterns in FAILURE_KINDS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = max(0, text.rfind("\n", 0, match.start()) + 1)
                end = text.find("\n", match.end())
                line = text[start : end if end != -1 else len(text)].strip()
                return kind, line[:300]
    return "COMMAND_FAILED", ""


def _disk_usage_gb(path: Path) -> float:
    total = 0
    seen = 0
    for p in path.rglob("*"):
        seen += 1
        if seen > 200_000:
            break
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            continue
    return total / (1024 ** 3)


def execute_recipe(
    recipe: Recipe,
    workdir: str | Path,
    out_dir: str | Path,
    backend_name: str = "local",
    limit_minutes: int | None = None,
    gpu: bool = False,
) -> RunResult:
    """Run ``recipe`` inside ``workdir`` and return measured metrics."""
    started = time.time()
    work = Path(workdir).resolve()
    out = Path(out_dir).resolve()
    artifacts = out / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    total_minutes = recipe.timeout_minutes
    if limit_minutes:
        total_minutes = min(total_minutes, limit_minutes)
    deadline = started + total_minutes * 60

    result = RunResult(
        recipe=recipe.name,
        backend=backend_name,
        artifacts=str(artifacts),
        workdir=str(work),
    )

    try:
        backend = get_backend(backend_name, work, recipe, artifacts, gpu=gpu)
    except BackendError as exc:
        result.status = "error"
        result.failure = "BACKEND_UNAVAILABLE"
        result.failure_detail = str(exc)
        return result

    def remaining() -> int:
        return max(1, int(deadline - time.time()))

    harness = recipe.harness_dir or "."

    def expand(cmd: str) -> str:
        return cmd.replace("{harness}", harness.replace("\\", "/"))

    def step(cmd: str, label: str, env: dict[str, str] | None = None) -> CommandResult:
        if time.time() >= deadline:
            return CommandResult(cmd=cmd, exit_code=124, duration_s=0.0, timed_out=True)
        r = backend.run(expand(cmd), remaining(), label, env=env)
        result.commands.append(r)
        return r

    try:
        for r in backend.prepare():
            result.commands.append(r)

        for idx, cmd in enumerate(recipe.data, start=1):
            r = step(cmd, f"{idx:02d}-data")
            if not r.ok:
                break
        else:
            for idx, cmd in enumerate(recipe.install, start=1):
                r = step(cmd, f"{idx:02d}-install")
                if not r.ok:
                    break
            else:
                r = step(recipe.eval_cmd, "99-eval", env=recipe.env or None)
    except BackendError as exc:
        # Preparation can fail after construction (no daemon, no interpreter).
        # That is a status, not a traceback.
        result.status = "error"
        result.failure = "BACKEND_UNAVAILABLE"
        result.failure_detail = str(exc)
        result.duration_s = time.time() - started
        (out / "run.json").write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        _write_commands(out, result.commands)
        return result
    finally:
        backend.close()

    result.duration_s = time.time() - started
    try:
        result.disk_gb = _disk_usage_gb(work)
    except OSError:
        result.disk_gb = 0.0

    failed = [c for c in result.commands if not c.ok]
    if failed:
        first = failed[0]
        kind, line = classify_failure(first.tail(6000))
        if first.timed_out:
            kind = "TIMEOUT"
            line = f"stopped after {total_minutes} min (limit)"
        result.status = "timeout" if first.timed_out else "failed"
        result.failure = kind
        result.failure_detail = line or first.tail(600)
    else:
        eval_result = result.commands[-1] if result.commands else None
        text = eval_result.tail(200_000) if eval_result else ""
        result.metrics = extract_metrics(text, recipe)
        result.status = "ok" if result.metrics else "failed"
        if not result.metrics:
            result.failure = "NO_METRIC_PARSED"
            result.failure_detail = "the evaluation ran but printed no value matching the recipe"

    (out / "run.json").write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    _write_commands(out, result.commands)
    return result


def _write_commands(out: Path, commands: list[CommandResult]) -> None:
    path = out / "commands.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for c in commands:
            fh.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")


def recipe_hash(recipe: Recipe) -> str:
    payload = json.dumps(recipe.to_dict(), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]
