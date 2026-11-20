"""Repeat an evaluation across seeds and report the spread.

A single number that matches the paper is weak evidence: the paper itself is one
sample from a distribution. Running the evaluation under several seeds turns
"91.06 vs 91.3" into "91.06 ± 0.04 vs 91.3", which is a claim a reviewer can
argue with.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .recipe import Recipe
from .runner import RunResult, execute_recipe

__all__ = ["SeedSummary", "run_seeds", "seed_command"]


@dataclass
class SeedSummary:
    seeds: list[int] = field(default_factory=list)
    per_seed: dict[int, dict[str, float]] = field(default_factory=dict)
    mean: dict[str, float] = field(default_factory=dict)
    std: dict[str, float] = field(default_factory=dict)
    ok: int = 0
    total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "seeds": list(self.seeds),
            "per_seed": {str(k): v for k, v in self.per_seed.items()},
            "mean": {k: round(v, 4) for k, v in self.mean.items()},
            "std": {k: round(v, 4) for k, v in self.std.items()},
            "ok": self.ok,
            "total": self.total,
        }


def seed_command(recipe: Recipe, seed: int) -> str:
    """Append the seed flag to the evaluation command."""
    flag = recipe.seed_flag or "--seed"
    if "{seed}" in recipe.eval_cmd:
        return recipe.eval_cmd.replace("{seed}", str(seed))
    return f"{recipe.eval_cmd} {flag} {seed}"


def run_seeds(
    recipe: Recipe,
    workdir: Path,
    out_dir: Path,
    seeds: list[int],
    backend_name: str = "local",
    limit_minutes: int | None = None,
    gpu: bool = False,
) -> tuple[RunResult, SeedSummary]:
    """Run the recipe once per seed; return a combined result and the spread."""
    runs: list[tuple[int, RunResult]] = []
    for seed in seeds:
        seeded = Recipe(**{**recipe.__dict__, "eval_cmd": seed_command(recipe, seed)})
        run = execute_recipe(
            seeded,
            workdir=workdir,
            out_dir=out_dir / f"seed-{seed}",
            backend_name=backend_name,
            limit_minutes=limit_minutes,
            gpu=gpu,
        )
        runs.append((seed, run))

    ok_runs = [(seed, run) for seed, run in runs if run.status == "ok" and run.metrics]
    summary = SeedSummary(seeds=list(seeds), total=len(seeds), ok=len(ok_runs))
    for seed, run in ok_runs:
        summary.per_seed[seed] = dict(run.metrics)

    metric_names = sorted({name for _, m in summary.per_seed.items() for name in m})
    for name in metric_names:
        values = [m[name] for m in summary.per_seed.values() if name in m]
        if not values:
            continue
        summary.mean[name] = statistics.fmean(values)
        summary.std[name] = statistics.pstdev(values) if len(values) > 1 else 0.0

    if ok_runs:
        combined = RunResult(
            recipe=recipe.name,
            backend=backend_name,
            status="ok",
            metrics=summary.mean,
            duration_s=sum(run.duration_s for _, run in runs),
            disk_gb=max(run.disk_gb for _, run in runs),
            artifacts=str(out_dir),
            workdir=str(workdir),
        )
        combined.commands = [cmd for _, run in runs for cmd in run.commands]
    else:
        combined = runs[-1][1] if runs else RunResult(recipe=recipe.name, backend=backend_name)

    return combined, summary
