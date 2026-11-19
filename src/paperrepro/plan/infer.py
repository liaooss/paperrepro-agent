"""Draft an execution recipe from a repository, without a human writing it.

This is the difference between "a runner" and "a planner": the recipe is
*derived* from the release's own README, entry points and manifests, and every
derivation is recorded so the analyst can see why a command was chosen.

Inference is deliberately conservative. When the evidence does not add up the
planner raises :class:`PlanError` naming what is missing, instead of inventing a
command that will fail ten minutes later.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from ..extract.claims import extract_claims
from ..ingest.repo import read_manifest_commands
from ..models import PaperDoc, RepoScan
from ..textutil import METRIC_SYNONYMS
from ..execute.recipe import Recipe

__all__ = ["infer_recipe", "PlanError"]

_EVAL_STEMS = ("evaluate", "eval", "test", "inference", "infer", "predict", "benchmark", "score")
_TRAIN_STEMS = ("train", "finetune", "fit")
_RUN_STEMS = ("main", "run", "demo", "app")

# Repository chores that happen to have a `__main__` guard.
_EXCLUDE_STEM = re.compile(
    r"^(convert|check|update|add|create|push|deprecate|extract|notify|release|sort|split|"
    r"process|format|aggregate|analyze|generate|fix|sync|merge|clean|install|download)_"
)

_PYTHON_CMD = re.compile(r"^\s*python3?\s+(?P<rest>.+)$")


class PlanError(RuntimeError):
    """Raised when no defensible plan can be derived from the repository."""


def _has_manifest(scan: RepoScan, *names: str) -> bool:
    lowered = {Path(path).name.lower() for path in scan.manifests}
    return any(name.lower() in lowered for name in names)


def _install_steps(scan: RepoScan, notes: list[str]) -> list[str]:
    # The package declaring its own metadata is a stronger signal than a
    # requirements file, which is often the development/test environment.
    if _has_manifest(scan, "pyproject.toml", "setup.py", "setup.cfg"):
        return ["{pip} install -e ."]
    if _has_manifest(scan, "requirements.txt"):
        notes.append("install: requirements.txt found")
        return ["{pip} install -r requirements.txt"]
    notes.append("install: no dependency manifest found; environment may be incomplete")
    return []


_SETUP_ONLY = (
    "-m venv",
    "-m pip",
    "-m pytest",
    "-m unittest",
    "-m build",
    "-m install",
    "-c ",
    "setup.py",
)


def _referenced_file(rest: str, scan: RepoScan) -> str:
    """First token of a command line that names a file in the repository."""
    for token in rest.split():
        if token.startswith("-"):
            continue
        candidate = token.strip("'\"")
        if any(f.path == candidate or f.path.endswith("/" + candidate) for f in scan.files):
            return candidate
    return ""


def _as_module(rest: str) -> str:
    match = re.match(r"-m\s+([A-Za-z_][\w.]*)", rest)
    return match.group(1) if match else ""


def _module_exists(module: str, scan: RepoScan) -> bool:
    rel = module.replace(".", "/")
    wanted = {f"{rel}.py", f"{rel}/__init__.py"}
    return any(f.path in wanted for f in scan.files)


def _candidate_commands(scan: RepoScan) -> list[tuple[str, str, str]]:
    """(command, referenced target, source) candidates, best first.

    Setup lines are rejected on purpose: a README is full of `python -m venv`
    and `python -m pytest`, and neither is "the experiment".
    """
    found: list[tuple[str, str, str]] = []

    for cmd in read_manifest_commands(scan):
        match = _PYTHON_CMD.match(cmd)
        if not match:
            continue
        rest = match.group("rest").strip()
        low = rest.lower()
        if low.startswith(_SETUP_ONLY):
            continue
        target = _referenced_file(rest, scan)
        if target:
            found.append((f"{{python}} {rest}", target, "README"))
            continue
        module = _as_module(rest)
        if module and _module_exists(module, scan):
            found.append((f"{{python}} {rest}", module, "README (module)"))

    for ref in scan.entry_points:
        path = ref.split(":")[0]
        if _EXCLUDE_STEM.match(Path(path).stem.lower()):
            continue
        found.append((f"{{python}} {path}", path, "entry point"))

    def rank(item: tuple[str, str, str]) -> tuple[int, int, int]:
        stem = Path(item[1]).stem.lower()
        for idx, group in enumerate((_EVAL_STEMS, _RUN_STEMS, _TRAIN_STEMS)):
            if stem in group:
                return (idx, 0 if item[2] == "README" else 1, len(item[1]))
        # Deeper paths are usually concrete scripts rather than package roots.
        return (9, 1, -item[1].count("/"))

    return sorted(found, key=rank)


def _dominant_metric(doc: PaperDoc) -> str:
    claims = extract_claims(doc)
    if not claims:
        return ""
    counts = Counter(claim.metric for claim in claims if claim.role == "paper")
    if not counts:
        return ""
    return counts.most_common(1)[0][0]


def infer_recipe(doc: PaperDoc, scan: RepoScan, name: str = "inferred") -> Recipe:
    """Derive a runnable recipe, or fail loudly with the reason."""
    notes: list[str] = []
    candidates = _candidate_commands(scan)
    if not candidates:
        raise PlanError(
            "no runnable entry point found: the README contains no `python ...` command and no "
            "script with a __main__ guard exists. Write a recipe by hand (--recipe)."
        )

    eval_cmd, target, source = candidates[0]
    stem = Path(target).stem.lower()
    looks_like_experiment = stem in _EVAL_STEMS + _RUN_STEMS + _TRAIN_STEMS
    if not looks_like_experiment and source == "entry point":
        raise PlanError(
            f"the best candidate `{target}` does not look like a train/eval entry point. "
            "Automatic planning stops here rather than running an arbitrary script; "
            "write a recipe with --recipe."
        )
    notes.append(f"eval: `{target}` chosen from {source}")

    metric = _dominant_metric(doc)
    if metric:
        notes.append(f"metric: '{metric}' is the most frequent metric in the paper")
    else:
        metric = "accuracy"
        notes.append("metric: no claim extracted from the paper; defaulting to accuracy")

    install = _install_steps(scan, notes)

    recipe = Recipe(
        name=name,
        eval_cmd=eval_cmd,
        install=install,
        data=[],
        metric=metric,
        source="inferred",
        notes="; ".join(notes),
        timeout_minutes=60,
        budget_gb=10.0,
    )
    return recipe


def describe(recipe: Recipe) -> str:
    """Human-readable plan, printed before anything is executed."""
    lines = [f"plan: {recipe.name} (source: {recipe.source})"]
    for idx, cmd in enumerate(recipe.install, start=1):
        lines.append(f"  install {idx}: {cmd}")
    for idx, cmd in enumerate(recipe.data, start=1):
        lines.append(f"  data    {idx}: {cmd}")
    lines.append(f"  eval      : {recipe.eval_cmd}")
    if recipe.notes:
        lines.append(f"  notes     : {recipe.notes}")
    return "\n".join(lines)
