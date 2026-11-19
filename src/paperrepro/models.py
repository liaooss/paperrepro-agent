"""Data structures shared by every stage of the pipeline.

The design rule for this module: a claim or a finding may never carry a bare
sentence. It carries :class:`Evidence` objects, and each one points at either a
paper location ("Table 2, row TinyCLIP") or a code location ("evaluate.py:41").
Downstream code and the final report only ever print those pointers, which is
what keeps the output auditable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Claim evidence levels, strongest first.
LEVELS: tuple[str, ...] = ("E1", "E2", "E3", "X")

LEVEL_LABELS: dict[str, str] = {
    "E1": "executable evidence",
    "E2": "strong static evidence",
    "E3": "weak static evidence",
    "X": "no correspondence found",
}

LEVEL_MEANING: dict[str, str] = {
    "E1": "Implementation, data path, configuration and a passing local smoke check are all present.",
    "E2": "Implementation and inputs are present, but nothing was executed.",
    "E3": "Only a name-level match exists; the link to the reported number is indirect.",
    "X": "Nothing in the repository corresponds to this claim.",
}

SEVERITIES: tuple[str, ...] = ("blocker", "major", "minor", "info")

VERDICTS: tuple[str, ...] = ("R0", "R1", "R2", "R3")

VERDICT_LABELS: dict[str, str] = {
    "R3": "directly reproducible",
    "R2": "reproducible after engineering work",
    "R1": "needs author-supplied assets",
    "R0": "not reproducible from what was released",
}


@dataclass
class Evidence:
    """A pointer to a place in the paper or in the code that supports a statement."""

    kind: str  # "paper" | "code"
    ref: str  # "Table 2 (row: TinyCLIP)" | "evaluate.py:41"
    text: str = ""  # short quoted snippet, never a paraphrase
    detail: str = ""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.ref

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PaperTable:
    id: str  # "Table 1"
    caption: str = ""
    header: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    section: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PaperDoc:
    path: str
    format: str  # "tex" | "markdown" | "html" | "pdf" | "text"
    title: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    tables: list[PaperTable] = field(default_factory=list)
    text: str = ""
    warnings: list[str] = field(default_factory=list)

    def section_text(self, *names: str) -> str:
        """Return the concatenated text of sections whose heading contains a name."""
        needles = [n.lower() for n in names if n]
        chunks: list[str] = []
        for heading, body in self.sections.items():
            low = heading.lower()
            if any(n in low for n in needles):
                chunks.append(body)
        return "\n".join(chunks)

    def results_text(self) -> str:
        joined = self.section_text("result", "experiment", "evaluation", "benchmark", "main")
        return joined or self.text

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "format": self.format,
            "title": self.title,
            "sections": list(self.sections),
            "tables": [t.to_dict() for t in self.tables],
            "warnings": self.warnings,
        }


@dataclass
class CodeFile:
    path: str  # posix, repository-relative
    lang: str
    lines: int
    text: str = ""  # may be empty when the file was skipped
    skipped_reason: str = ""

    def ref(self, line: int | None = None) -> str:
        return f"{self.path}:{line}" if line else self.path

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "lang": self.lang,
            "lines": self.lines,
            "skipped_reason": self.skipped_reason,
        }


@dataclass
class RepoScan:
    root: str
    files: list[CodeFile] = field(default_factory=list)
    manifests: dict[str, str] = field(default_factory=dict)
    readme: str = ""
    readme_path: str = ""
    entry_points: list[str] = field(default_factory=list)
    seed_refs: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    metric_refs: dict[str, list[str]] = field(default_factory=dict)
    dataset_refs: dict[str, list[str]] = field(default_factory=dict)
    absolute_paths: list[dict[str, str]] = field(default_factory=list)
    checkpoint_refs: list[dict[str, str]] = field(default_factory=list)
    todos: list[dict[str, str]] = field(default_factory=list)
    notebook_only: bool = False
    warnings: list[str] = field(default_factory=list)

    def lang_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.files:
            counts[f.lang] = counts.get(f.lang, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    def code_files(self) -> list[CodeFile]:
        return [f for f in self.files if f.lang in {"python", "r", "julia", "shell"}]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "file_count": len(self.files),
            "languages": self.lang_counts(),
            "manifests": sorted(self.manifests),
            "entry_points": self.entry_points,
            "config_files": self.config_files,
            "readme_path": self.readme_path,
            "warnings": self.warnings,
        }


@dataclass
class Claim:
    """One quantitative statement in the paper that reproduction would have to match."""

    id: str
    metric: str  # canonical metric name, e.g. "accuracy"
    raw_metric: str  # as written, e.g. "ImageNet Top-1"
    value: str  # as written, e.g. "72.3"
    row_label: str = ""  # which row of the table, e.g. "TinyCLIP (ours)"
    dataset: str = ""
    split: str = ""
    role: str = "paper"  # "paper" | "reference"
    evidence: list[Evidence] = field(default_factory=list)
    code_evidence: list[Evidence] = field(default_factory=list)
    level: str = "X"
    gaps: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "metric": self.metric,
            "raw_metric": self.raw_metric,
            "value": self.value,
            "row_label": self.row_label,
            "dataset": self.dataset,
            "split": self.split,
            "role": self.role,
            "level": self.level,
            "gaps": list(self.gaps),
            "notes": self.notes,
            "evidence": [e.to_dict() for e in self.evidence],
            "code_evidence": [e.to_dict() for e in self.code_evidence],
        }


@dataclass
class Finding:
    """A deterministic risk rule hit."""

    rule_id: str
    title: str
    severity: str  # blocker | major | minor | info
    detail: str
    evidence: list[Evidence] = field(default_factory=list)
    author_dependent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity,
            "detail": self.detail,
            "author_dependent": self.author_dependent,
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class SmokeReport:
    """Result of the lightweight local checks (no data, no training)."""

    enabled: bool = False
    syntax_ok: bool = True
    entry_ok: bool = False
    manifest_ok: bool = False
    checked: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.enabled and self.syntax_ok and self.entry_ok and self.manifest_ok)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Scorecard:
    paper: str
    repo: str
    generated_at: str
    paperrepro_version: str
    verdict: str
    confidence: float
    summary: str
    claims: list[Claim] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    smoke: SmokeReport = field(default_factory=SmokeReport)
    paper_meta: dict[str, Any] = field(default_factory=dict)
    repo_meta: dict[str, Any] = field(default_factory=dict)
    next_actions: list[str] = field(default_factory=list)
    llm_used: bool = False
    llm_model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperrepro/scorecard/v1",
            "paper": self.paper,
            "repo": self.repo,
            "generated_at": self.generated_at,
            "paperrepro_version": self.paperrepro_version,
            "verdict": self.verdict,
            "verdict_label": VERDICT_LABELS.get(self.verdict, ""),
            "confidence": round(self.confidence, 3),
            "summary": self.summary,
            "llm": {"used": self.llm_used, "model": self.llm_model},
            "smoke": self.smoke.to_dict(),
            "paper_meta": self.paper_meta,
            "repo_meta": self.repo_meta,
            "claims": [c.to_dict() for c in self.claims],
            "findings": [f.to_dict() for f in self.findings],
            "next_actions": list(self.next_actions),
        }


def claim_level_label(level: str) -> str:
    return LEVEL_LABELS.get(level, level)
