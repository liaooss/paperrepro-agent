"""Repository scanner.

This is deliberately static: reprocheck never executes the target repository
(that is what ``--smoke`` approximates with a compiler check).  Static evidence
is enough to answer the question that matters, "is every element of this claim
present in the code at all", and it cannot damage the user's machine or take
hours downloading weights.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from ..models import CodeFile, RepoScan
from ..textutil import METRIC_SYNONYMS, DATASET_SYNONYMS, find_alias, line_of, snippet
from ..config import Settings

__all__ = ["scan_repo"]

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    "venv",
    ".venv",
    "env",
    ".tox",
    "dist",
    "build",
    "site-packages",
    ".idea",
    ".vscode",
}

LANG_BY_EXT = {
    ".py": "python",
    ".ipynb": "notebook",
    ".r": "r",
    ".jl": "julia",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cu": "cpp",
    ".c": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".js": "javascript",
    ".ts": "javascript",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "shell",
    ".yaml": "config",
    ".yml": "config",
    ".json": "config",
    ".toml": "config",
    ".cfg": "config",
    ".ini": "config",
    ".txt": "text",
    ".md": "docs",
    ".rst": "docs",
    ".tex": "docs",
}

MANIFEST_NAMES = {
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-gpu.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "pipfile",
    "environment.yml",
    "environment.yaml",
    "conda.yml",
    "conda.yaml",
    "dockerfile",
    "makefile",
    "package.json",
    "poetry.lock",
    "pipfile.lock",
    "uv.lock",
}

ENTRY_STEMS = {
    "main",
    "train",
    "run",
    "eval",
    "evaluate",
    "evaluation",
    "finetune",
    "fine_tune",
    "inference",
    "predict",
    "test",
    "demo",
    "app",
    "benchmark",
    "preprocess",
}

_ABS_PATH = re.compile(
    r"""["']((?:[A-Za-z]:\\|/(?:home|root|mnt|data|scratch|hdd|raid|ssd|workspace|content)\b)[^"'\n]{0,120})["']"""
)
_CKPT = re.compile(r"[\w./\\-]+\.(?:pth|pt|ckpt|bin|safetensors|h5|onnx|pkl)\b")
_SEED = re.compile(
    r"(set_seed|manual_seed|random\.seed|np\.random\.seed|numpy\.random\.seed|torch\.manual_seed|tf\.random\.set_seed|seed\s*=\s*\d+|--seed)",
    re.IGNORECASE,
)
_ENTRY = re.compile(
    r"(if\s+__name__\s*==\s*['\"]__main__['\"]|ArgumentParser\s*\(|@click\.command|fire\.Fire\s*\(|typer\.Typer\s*\()"
)
_TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK|NotImplementedError)\b")
_INSTALL_HINT = re.compile(r"(pip install|conda install|python setup\.py|bash .*\.sh|docker run|make )", re.IGNORECASE)


def _line_at(text: str, offset: int, width: int = 160) -> str:
    """The whole source line containing an offset, trimmed for display."""
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return text[start:end].strip()[:width]


def _read_text(path: Path, max_bytes: int) -> tuple[str, str]:
    """Return (text, skip_reason); skip_reason is set when the file was ignored."""
    try:
        size = path.stat().st_size
    except OSError:
        return "", "unreadable"
    if size > max_bytes:
        return "", f"too large ({size} bytes)"
    try:
        data = path.read_bytes()
    except OSError:
        return "", "unreadable"
    if b"\x00" in data[:4096]:
        return "", "binary"
    return data.decode("utf-8", errors="replace"), ""


def _iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(filenames):
            yield Path(dirpath) / name


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _looks_like_repo(root: Path) -> list[str]:
    """Cheap smell test so a wrong path fails loudly instead of silently."""
    signals: list[str] = []
    if (root / ".git").exists():
        signals.append(".git")
    for name in ("README.md", "README.rst", "pyproject.toml", "setup.py", "requirements.txt"):
        if (root / name).exists():
            signals.append(name)
    return signals


def _definition_hit(text: str, aliases: tuple[str, ...]) -> int:
    """Offset of a function/class definition whose name contains an alias.

    A ``def top1_accuracy`` is much stronger evidence than the import that
    mentions the same name, and it is what the report should cite.
    """
    for alias in aliases:
        key = re.sub(r"[^a-z0-9]", "", alias.lower())
        if len(key) < 3:
            continue
        for m in re.finditer(r"(?m)^[ \t]*(?:def|class)[ \t]+([A-Za-z_]\w*)", text):
            if key in re.sub(r"[^a-z0-9]", "", m.group(1).lower()):
                return m.start()
    return -1


def scan_repo(root: str | Path, settings: Settings | None = None) -> RepoScan:
    """Walk a repository and collect the evidence the audit rules need."""
    settings = settings or Settings.from_env()
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root_path}")

    scan = RepoScan(root=str(root_path))
    signals = _looks_like_repo(root_path)
    if not signals:
        scan.warnings.append(
            "This directory has no README, no dependency manifest and no .git; "
            "it may not be the released repository."
        )

    texts: dict[str, str] = {}
    for path in _iter_files(root_path):
        if len(scan.files) >= settings.max_files:
            scan.warnings.append(f"Stopped after {settings.max_files} files; scan is partial.")
            break
        rel = _rel(root_path, path)
        ext = path.suffix.lower()
        lang = LANG_BY_EXT.get(ext, "other")
        text, skip = _read_text(path, settings.max_file_bytes)
        lines = text.count("\n") + 1 if text else 0
        scan.files.append(CodeFile(path=rel, lang=lang, lines=lines, text=text, skipped_reason=skip))
        if text:
            texts[rel] = text

    # Dependency manifests and README.
    for rel, text in texts.items():
        name = rel.rsplit("/", 1)[-1].lower()
        if name in MANIFEST_NAMES:
            scan.manifests[rel] = text
        if name.startswith("readme") and not scan.readme:
            scan.readme = text
            scan.readme_path = rel

    # Per-file analyses.
    for rel, text in texts.items():
        lang = next((f.lang for f in scan.files if f.path == rel), "other")

        if lang in {"python", "r", "julia", "shell", "javascript"}:
            m = _ENTRY.search(text)
            stem = Path(rel).stem.lower()
            if m:
                scan.entry_points.append(f"{rel}:{line_of(text, m.start())}")
            elif stem in ENTRY_STEMS and lang == "python":
                scan.entry_points.append(rel)

            m = _SEED.search(text)
            if m:
                scan.seed_refs.append(f"{rel}:{line_of(text, m.start())}")

        for m in _ABS_PATH.finditer(text):
            scan.absolute_paths.append(
                {
                    "ref": f"{rel}:{line_of(text, m.start())}",
                    "path": m.group(1),
                    "snippet": _line_at(text, m.start()),
                }
            )
        for line_no, line in enumerate(text.splitlines(), start=1):
            if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line):
                scan.todos.append({"ref": f"{rel}:{line_no}", "text": line.strip()[:160]})

        if lang == "config" or Path(rel).name.lower() in {"config.py", "configs.py", "hparams.py"}:
            scan.config_files.append(rel)

    # Checkpoint references vs files actually present.
    present = {f.path.lower() for f in scan.files}
    present_names = {Path(p).name.lower() for p in present}
    for rel, text in texts.items():
        for m in _CKPT.finditer(text):
            ref = m.group(0).replace("\\", "/")
            name = ref.rsplit("/", 1)[-1].lower()
            if name in present_names or ref.lower() in present:
                continue
            scan.checkpoint_refs.append(
                {"ref": f"{rel}:{line_of(text, m.start())}", "path": ref, "snippet": _line_at(text, m.start())}
            )
    # De-duplicate repeated checkpoint mentions.
    seen: set[str] = set()
    unique_ckpt: list[dict[str, str]] = []
    for item in scan.checkpoint_refs:
        key = item["path"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique_ckpt.append(item)
    scan.checkpoint_refs = unique_ckpt

    # Metric and dataset mentions across code.  Source files are searched
    # before docs so that "strongest evidence" points at an implementation and
    # not at the README sentence that merely mentions ImageNet.
    lang_by_path = {f.path: f.lang for f in scan.files}
    code_first = sorted(texts.items(), key=lambda kv: (0 if lang_by_path.get(kv[0]) in {"python", "r", "julia"} else 1, kv[0]))

    for metric in METRIC_SYNONYMS:
        # A definition anywhere in the repo beats an import or a docstring
        # mention, so search for definitions in a first pass.
        defs: list[str] = []
        for rel, text in code_first:
            if len(defs) >= 4:
                break
            hit = _definition_hit(text, METRIC_SYNONYMS[metric])
            if hit >= 0:
                defs.append(f"{rel}:{line_of(text, hit)}")
        if defs:
            scan.metric_refs[metric] = defs
            continue
        refs: list[str] = []
        for rel, text in code_first:
            if len(refs) >= 4:
                break
            hit = -1
            for alias in METRIC_SYNONYMS[metric]:
                hit = find_alias(text, alias)
                if hit >= 0:
                    break
            if hit >= 0:
                refs.append(f"{rel}:{line_of(text, hit)}")
        if refs:
            scan.metric_refs[metric] = refs

    for dataset in DATASET_SYNONYMS:
        refs = []
        for rel, text in code_first:
            if len(refs) >= 4:
                break
            hit = -1
            for alias in DATASET_SYNONYMS[dataset]:
                hit = find_alias(text, alias)
                if hit >= 0:
                    break
            if hit >= 0:
                refs.append(f"{rel}:{line_of(text, hit)}")
        if refs:
            scan.dataset_refs[dataset] = refs

    notebooks = [f for f in scan.files if f.lang == "notebook"]
    py_files = [f for f in scan.files if f.lang == "python"]
    scan.notebook_only = bool(notebooks) and not py_files

    if not scan.manifests:
        scan.warnings.append("No dependency manifest found (requirements.txt, environment.yml, ...).")
    if not scan.entry_points:
        scan.warnings.append("No executable entry point found (no __main__ guard, no CLI parser).")
    if not scan.config_files:
        scan.warnings.append("No configuration file found; hyperparameters are probably hard-coded.")

    return scan


def read_manifest_commands(scan: RepoScan) -> list[str]:
    """Install/run commands the README advertises, used by the smoke check."""
    if not scan.readme:
        return []
    cmds: list[str] = []
    for line in scan.readme.splitlines():
        stripped = line.strip().strip("`").strip()
        if stripped.startswith(("pip install", "conda install", "python ", "bash ", "make ", "docker run")):
            cmds.append(stripped)
    return cmds[:20]


def has_install_hint(scan: RepoScan) -> bool:
    return bool(scan.readme and _INSTALL_HINT.search(scan.readme))
