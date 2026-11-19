"""The execution recipe: the only thing paperrepro will run.

A recipe is a small, reviewable document:

    {
      "name": "distilbert-sst2",
      "python": "3.11",
      "install": ["{pip} install -r requirements.txt"],
      "data": ["{python} prepare_data.py"],
      "eval_cmd": "{python} evaluate.py --split dev",
      "metric": "accuracy",
      "tolerance_abs": 0.5,
      "timeout_minutes": 60,
      "budget_gb": 5.0
    }

Recipes are either curated (shipped with paperrepro, or written by a human after
looking at the release) or inferred (drafted from the README). Inferred recipes
carry ``source: "inferred"`` and the CLI refuses to execute them without
``--yes``, because "run whatever the README says" is exactly the unsafe step.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["Recipe", "RecipeError", "load_recipe"]


class RecipeError(ValueError):
    """Raised when a recipe file cannot be read or is unusable."""


@dataclass
class Recipe:
    name: str
    eval_cmd: str
    install: list[str] = field(default_factory=list)
    data: list[str] = field(default_factory=list)
    python: str = "3.11"
    metric: str = "accuracy"
    metric_regex: str = ""
    tolerance_abs: float = 0.5
    tolerance_rel: float = 0.01
    timeout_minutes: int = 120
    budget_gb: float = 5.0
    source: str = "curated"  # "curated" | "inferred"
    notes: str = ""
    claim_ids: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    harness_dir: str = ""
    # The value being checked, when the paper's table cannot be parsed
    # automatically. Always carries the paper location it came from.
    target: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recipe":
        if not isinstance(data, dict):
            raise RecipeError("recipe must be a JSON/YAML object")
        name = str(data.get("name") or "").strip()
        eval_cmd = str(data.get("eval_cmd") or data.get("eval") or "").strip()
        if not name or not eval_cmd:
            raise RecipeError("recipe needs at least 'name' and 'eval_cmd'")

        def _list(key: str) -> list[str]:
            raw = data.get(key) or []
            if isinstance(raw, str):
                return [raw]
            return [str(x) for x in raw]

        return cls(
            name=name,
            eval_cmd=eval_cmd,
            install=_list("install"),
            data=_list("data"),
            python=str(data.get("python") or "3.11"),
            metric=str(data.get("metric") or "accuracy"),
            metric_regex=str(data.get("metric_regex") or ""),
            tolerance_abs=float(data.get("tolerance_abs", 0.5)),
            tolerance_rel=float(data.get("tolerance_rel", 0.01)),
            timeout_minutes=int(data.get("timeout_minutes", 120)),
            budget_gb=float(data.get("budget_gb", 5.0)),
            source=str(data.get("source") or "curated"),
            notes=str(data.get("notes") or ""),
            claim_ids=_list("claim_ids"),
            env={str(k): str(v) for k, v in (data.get("env") or {}).items()},
            harness_dir=str(data.get("harness_dir") or ""),
            target=dict(data.get("target") or {}),
        )


def load_recipe(path: str | Path) -> Recipe:
    p = Path(path)
    if not p.exists():
        raise RecipeError(f"recipe not found: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # optional
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RecipeError(
                "YAML recipes need PyYAML; use JSON instead (pip install pyyaml)"
            ) from exc
        try:
            data = yaml.safe_load(text)
        except Exception as exc:
            raise RecipeError(f"invalid YAML in {p}: {exc}") from exc
    else:
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise RecipeError(f"invalid JSON in {p}: {exc}") from exc
    return Recipe.from_dict(data)
