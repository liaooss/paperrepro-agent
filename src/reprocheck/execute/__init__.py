"""Execution layer: actually run a release and measure whether it reproduces.

The static half of reprocheck answers "is there evidence you *could* reproduce
this". This package answers the harder question: "we ran it - do the numbers
match?".

Three rules keep it honest:

1. Only a :class:`Recipe` is executed. Nothing is inferred at run time and
   passed straight to a shell.
2. Every command's exit code, duration and full output is written to disk before
   it can influence a conclusion.
3. A failure is classified, not summarised: "dependency resolution failed" and
   "the dataset is behind a login" lead to different next steps.
"""

from __future__ import annotations

from .backends import DockerBackend, LocalBackend, CondaBackend, get_backend
from .recipe import Recipe, RecipeError
from .runner import CommandResult, RunResult, execute_recipe

__all__ = [
    "Recipe",
    "RecipeError",
    "CommandResult",
    "RunResult",
    "execute_recipe",
    "get_backend",
    "LocalBackend",
    "CondaBackend",
    "DockerBackend",
]
