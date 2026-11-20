"""Bounded repair: fix the environment, never the science.

Research releases fail for mundane reasons: a dependency pinned to a version that
no longer has wheels, a directory the script expects to exist. Those are worth a
bounded, recorded attempt. Changing a model, a loss or a hyperparameter is not -
that would no longer be the paper's method.

Every attempt is a separate run with its own artifacts and its own status, and
every source edit is kept as a patch next to the run, so a repaired run can
never be mistaken for the original.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .recipe import Recipe
from .runner import RunResult, execute_recipe

__all__ = ["RepairAction", "RepairPolicy", "plan_repair", "run_with_repair", "MAX_ATTEMPTS"]

MAX_ATTEMPTS = 2

# Only failures that are about the environment or a missing directory.
_REPAIRABLE = {"ENV_CONFLICT", "COMMAND_FAILED"}

_NO_MATCHING = re.compile(r"No matching distribution found for ([A-Za-z0-9_.\-]+)==([^\s;]+)")
_MISSING_PATH = re.compile(
    r"(?:No such file or directory|FileNotFoundError)[^\n]{0,40}?['\"]([^'\"]+)['\"]"
)


@dataclass
class RepairPolicy:
    """What may be changed, and how many times."""

    enabled: bool = True
    max_attempts: int = MAX_ATTEMPTS
    allow_unpin: bool = True
    allow_mkdir: bool = True


@dataclass
class RepairAction:
    attempt: int
    failure: str
    strategy: str
    detail: str
    patch_path: str = ""
    backup_path: str = ""
    ok: bool = False

    def to_dict(self) -> dict:
        return {
            "attempt": self.attempt,
            "failure": self.failure,
            "strategy": self.strategy,
            "detail": self.detail,
            "patch_path": self.patch_path,
            "backup_path": self.backup_path,
            "ok": self.ok,
        }


def _requirements_files(workdir: Path) -> list[Path]:
    return sorted(p for p in workdir.glob("**/requirements*.txt") if ".paperrepro" not in str(p))


def _unpin(workdir: Path, package: str, version: str, patch_dir: Path) -> RepairAction | None:
    """Drop a `==version` pin that no longer resolves, keeping the old line as a patch."""
    target_line = f"{package}=={version}"
    for path in _requirements_files(workdir):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.replace(" ", "") != target_line:
                continue
            new_text = text.replace(line, f"{package}", 1)
            patch_dir.mkdir(parents=True, exist_ok=True)
            rel = path.relative_to(workdir).as_posix()
            patch = patch_dir / f"unpin-{package.lower()}.diff"
            backup = patch_dir / "backup" / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(text, encoding="utf-8")
            patch.write_text(
                f"--- a/{rel}\n+++ b/{rel}\n-{line}\n+{package}\n", encoding="utf-8"
            )
            path.write_text(new_text, encoding="utf-8")
            return RepairAction(
                attempt=0,
                failure="ENV_CONFLICT",
                strategy="unpin",
                detail=f"{rel}: '{target_line}' -> '{package}' (the pinned wheel no longer exists)",
                patch_path=str(patch),
                backup_path=str(backup),
            )
    return None


def _mkdir(workdir: Path, missing: str, patch_dir: Path) -> RepairAction | None:
    """Create a directory the script expects, but only inside the checkout.

    The error usually names a file inside a directory that does not exist
    (``results/out.txt``), so the directory to create is the parent when the
    path carries a suffix.
    """
    candidate = Path(missing)
    if not candidate.is_absolute():
        candidate = workdir / candidate
    target = candidate.parent if candidate.suffix else candidate
    try:
        resolved = target.resolve()
        resolved.relative_to(workdir.resolve())
    except (ValueError, OSError):
        return None  # outside the checkout: never touch it
    if resolved.exists():
        return None
    try:
        resolved.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return RepairAction(
        attempt=0,
        failure="COMMAND_FAILED",
        strategy="mkdir",
        detail=f"created {resolved.relative_to(workdir.resolve())} (expected by the release)",
    )


def plan_repair(run: RunResult, workdir: Path, policy: RepairPolicy, patch_dir: Path) -> RepairAction | None:
    """Decide the single next repair, or ``None`` when nothing safe applies."""
    if not policy.enabled or run.status == "ok":
        return None
    if run.failure not in _REPAIRABLE:
        return None

    text = "\n".join(c.tail(8000) for c in run.commands)

    if run.failure == "ENV_CONFLICT" and policy.allow_unpin:
        match = _NO_MATCHING.search(text)
        if match:
            return _unpin(workdir, match.group(1), match.group(2), patch_dir)

    if policy.allow_mkdir:
        for match in _MISSING_PATH.finditer(text):
            action = _mkdir(workdir, match.group(1), patch_dir)
            if action:
                return action
    return None


def restore(actions: list[RepairAction], workdir: Path) -> None:
    """Put the checkout back the way the authors left it.

    A repair is evidence, not a new release: the repository must not gain an
    untracked edit just because we tried something.
    """
    for action in actions:
        if not action.backup_path:
            continue
        backup = Path(action.backup_path)
        if not backup.exists():
            continue
        # backups mirror the repository under <out>/repairs/backup/
        root = backup.parents[1] / "backup"
        try:
            rel = backup.relative_to(root)
        except ValueError:
            continue
        target = workdir / rel
        try:
            target.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError:
            continue


def run_with_repair(
    recipe: Recipe,
    workdir: Path,
    out_dir: Path,
    backend_name: str = "local",
    limit_minutes: int | None = None,
    gpu: bool = False,
    policy: RepairPolicy | None = None,
) -> tuple[RunResult, list[RepairAction], RunResult | None]:
    """Run, then attempt bounded repairs. Returns (final, actions, original)."""
    policy = policy or RepairPolicy()
    original = execute_recipe(
        recipe,
        workdir=workdir,
        out_dir=out_dir / "attempt-1",
        backend_name=backend_name,
        limit_minutes=limit_minutes,
        gpu=gpu,
    )
    if original.status == "ok" or not policy.enabled:
        return original, [], None

    actions: list[RepairAction] = []
    current = original
    try:
        for attempt in range(1, policy.max_attempts + 1):
            if attempt > 1 and current.status != "ok" and current.failure not in _REPAIRABLE:
                break
            action = plan_repair(current, workdir, policy, out_dir / "repairs")
            if action is None:
                break
            action.attempt = attempt
            actions.append(action)

            current = execute_recipe(
                recipe,
                workdir=workdir,
                out_dir=out_dir / f"attempt-{attempt + 1}",
                backend_name=backend_name,
                limit_minutes=limit_minutes,
                gpu=gpu,
            )
            action.ok = current.status == "ok"
            if current.status == "ok":
                break
    finally:
        restore(actions, workdir)

    return current, actions, original
