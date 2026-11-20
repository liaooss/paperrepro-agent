"""Shared helpers for the test suite."""

from __future__ import annotations

import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
IS_WINDOWS = sys.platform.startswith("win")
DEMO_PAPER = ROOT / "examples" / "demo" / "paper.md"
DEMO_REPO = ROOT / "examples" / "demo" / "code"
TEX_PAPER = Path(__file__).resolve().parent / "fixtures" / "sample.tex"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def make_repo(files: dict[str, str]) -> Path:
    """Create a throw-away repository whose keys are relative posix paths."""
    tmp = Path(tempfile.mkdtemp(prefix="paperrepro-test-"))
    for rel, content in files.items():
        target = tmp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    return tmp


def cleanup(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


def _write_paper(text: str, suffix: str = ".md") -> Path:
    """Write a paper body to a throw-away file (name kept short for readability)."""
    tmp = Path(tempfile.mkdtemp(prefix="paperrepro-paper-"))
    path = tmp / ("paper" + suffix)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path
