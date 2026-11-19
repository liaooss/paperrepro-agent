"""Render the result of an executed run."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .compare import ClaimOutcome, summarise_outcomes
from .status import STATUS_LABELS
from .viability import Viability
from .runner import RunResult

if TYPE_CHECKING:  # pragma: no cover
    from .case import RunAssessment

__all__ = ["render_run_markdown", "render_run_console"]

_STATUS_GLYPH = {"MATCH": "match", "CLOSE": "close", "MISMATCH": "MISMATCH", "NOT_RUN": "not run"}


def _cell(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _evidence_line(run: RunResult, metric: str) -> tuple[str, str]:
    """Find the log line that produced the measurement."""
    for command in reversed(run.commands):
        if not command.log_path:
            continue
        path = Path(command.log_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            low = line.lower()
            if metric.lower() in low and any(ch.isdigit() for ch in line):
                return line.strip()[:200], str(path)
    return "", ""


def render_run_markdown(assessment: "RunAssessment") -> str:
    run = assessment.run
    outcomes = assessment.outcomes
    viability = assessment.viability
    counts = summarise_outcomes(outcomes)
    lines: list[str] = []
    add = lines.append

    add(f"# Reproduction run — {assessment.name}")
    add("")
    status = getattr(assessment, "status", "") or "INSUFFICIENT_EVIDENCE"
    add(f"> **Status: {status}** — {STATUS_LABELS.get(status, '')}.  ")
    add(f"> {assessment.status_reason or ''}  ")
    add(f"> Recommendation: **{viability.label}** · viability {viability.score:.1f}/5")
    add("")
    if outcomes:
        counts_text = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        add(f"Claims compared: {counts_text} (tolerance {assessment.recipe.tolerance_abs} points).")
        add("")

    if outcomes:
        add("## Claim comparison")
        add("")
        add("| Claim | Metric | Paper | Measured | Delta (points) | Status |")
        add("|-------|--------|-------|----------|----------------|--------|")
        for o in outcomes:
            measured = "—" if o.measured is None else f"{o.measured:.2f}"
            delta = "—" if o.delta is None else f"{o.delta:+.2f}"
            add(
                f"| {o.claim_id} | {_cell(o.raw_metric)} | {_cell(o.paper_value)} | {measured} | "
                f"{delta} | {_STATUS_GLYPH.get(o.status, o.status)} |"
            )
        add("")

    audit = getattr(assessment, "audit", []) or []
    if audit:
        add("## Consistency audit — paper versus code")
        add("")
        add("| Parameter | Paper says | Code says | Result | Evidence |")
        add("|-----------|------------|-----------|--------|----------|")
        for check in audit:
            evidence = check.code_ref or check.paper_ref or ""
            add(
                f"| {_cell(check.param)} | {_cell(check.paper_value) or '—'} | "
                f"{_cell(check.code_value) or '—'} | {check.status} | `{_cell(evidence)}` |"
            )
        add("")
        mismatched = [c for c in audit if c.status == "MISMATCH"]
        if mismatched:
            add(
                "A mismatch is a question for the authors, not a verdict: it can be a stale README, "
                "a different experiment in the same repository, or a real discrepancy."
            )
        else:
            add("Every parameter the paper states agrees with the code.")
        add("")
    else:
        add("## Consistency audit — paper versus code")
        add("")
        add(
            "No comparable configuration was found: the repository has no config file or "
            "config-like module that states these hyperparameters, so the paper's settings "
            "cannot be attributed to this code with evidence."
        )
        add("")

    add("## What was run")
    add("")
    add("| | |")
    add("|---|---|")
    add(f"| Paper | `{assessment.paper}` |")
    commit_file = Path(assessment.repo) / ".paperrepro-commit"
    commit = commit_file.read_text(encoding="utf-8").strip() if commit_file.exists() else ""
    add(f"| Repository | `{assessment.repo}`" + (f" @ `{commit[:12]}`" if commit else "") + " |")
    add(f"| Backend | {run.backend} |")
    add(f"| Commands | {len(run.commands)} (failed: {sum(1 for c in run.commands if not c.ok)}) |")
    add(f"| Wall clock | {run.duration_s / 60:.1f} min |")
    add(f"| Local disk | {run.disk_gb:.1f} GB |")
    add(f"| Recipe source | {assessment.recipe.source} |")
    add(f"| Level | L2 evaluation (released weights, no training) |")
    add("")

    if run.status != "ok":
        add("## Why it failed")
        add("")
        add(f"- **Kind:** `{run.failure}`")
        if run.failure_detail:
            add(f"- **Evidence:** {run.failure_detail}")
        add("")
        add("Failure kinds map to different remedies:")
        add("")
        add("- `MISSING_WEIGHTS` / `DATA_UNAVAILABLE` — only the authors can fix this; ask them.")
        add("- `ENV_CONFLICT` — try `--backend docker` or pin the versions the release expects.")
        add("- `OOM` — reduce batch size or resolution; the claim may still be checkable.")
        add("- `TIMEOUT` — raise `--limit-minutes` or reduce the evaluation split.")
        add("")

    metric = assessment.recipe.metric
    evidence, evidence_path = _evidence_line(run, metric)
    if evidence:
        add("## Evidence")
        add("")
        add(f"- `{_cell(evidence)}`")
        add(f"- from `{evidence_path}`")
        add("")

    if run.commands:
        add("## Command log")
        add("")
        add("| # | Command | Exit | Time | Log |")
        add("|---|---------|------|------|-----|")
        for idx, cmd in enumerate(run.commands, start=1):
            log_name = Path(cmd.log_path).name if cmd.log_path else ""
            add(f"| {idx} | `{_cell(cmd.cmd)[:120]}` | {cmd.exit_code} | {cmd.duration_s:.0f}s | {log_name} |")
        add("")

    plan = getattr(assessment, "plan", "") or ""
    if plan:
        add("## Plan that was executed")
        add("")
        add("```")
        add(plan)
        add("```")
        add("")

    add("## Viability")
    add("")
    add("| Dimension | Score | Note |")
    add("|-----------|-------|------|")
    for dim in viability.dimensions:
        add(f"| {dim.name} | {dim.score:.1f}/5 | {_cell(dim.note)} |")
    add("")
    add(f"**Overall {viability.score:.1f}/5 → {viability.label}.**")
    add("")
    if viability.blockers:
        add("Blockers:")
        add("")
        for blocker in viability.blockers:
            add(f"- {blocker}")
        add("")

    add("## Limits of this run")
    add("")
    add("- One environment, one seed, one machine. A match here is evidence, not proof.")
    add("- The comparison covers only claims whose metric the run actually printed.")
    add("- Protocol differences (split, preprocessing, metric definition) are not detected automatically; "
        "check them before quoting these numbers in a paper.")
    add("")
    return "\n".join(lines)


def render_run_console(assessment: "RunAssessment") -> str:
    run = assessment.run
    counts = summarise_outcomes(assessment.outcomes)
    lines = [
        f"status    {getattr(assessment, 'status', '?')}  {getattr(assessment, 'status_reason', '')}".rstrip(),
        f"run       {run.status}" + (f"  ({run.failure})" if run.failure else ""),
        f"metrics   {', '.join(f'{k}={v:.4f}' for k, v in run.metrics.items()) or 'none'}",
        f"claims    " + (", ".join(f"{k}:{v}" for k, v in counts.items()) or "none compared"),
        f"viability {assessment.viability.score:.1f}/5  {assessment.viability.label}",
        f"time      {run.duration_s / 60:.1f} min   disk {run.disk_gb:.1f} GB",
    ]
    audit = getattr(assessment, "audit", []) or []
    if audit:
        mismatched = [c for c in audit if c.status == "MISMATCH"]
        lines.append(f"audit     {len(audit)} parameter(s) checked, {len(mismatched)} mismatch(es)")
    return "\n".join(lines)
