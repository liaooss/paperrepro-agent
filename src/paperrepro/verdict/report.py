"""Markdown rendering: a human report and an executable reproduction plan."""

from __future__ import annotations

from ..models import LEVEL_LABELS, VERDICT_LABELS, Claim, Scorecard
from .score import decide

__all__ = ["render_markdown", "render_plan", "render_console"]

_SEVERITY_TITLES = {
    "blocker": "Blockers",
    "major": "Major issues",
    "minor": "Minor issues",
    "info": "Notes",
}


def _cell(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _quote(text: str) -> str:
    """Inline code rendering for a snippet, safe for pipes and backticks."""
    return "`" + (text or "").replace("`", "'").replace("\n", " ").strip() + "`"


def _badge(level: str) -> str:
    return f"**{level}** {LEVEL_LABELS.get(level, '')}"


def _claim_line(claim: Claim) -> str:
    target = claim.dataset or "unspecified dataset"
    return f"{claim.raw_metric} = **{claim.value}** on `{target}`"


def render_markdown(sc: Scorecard) -> str:
    verdict, confidence, reasons = decide(sc.claims, sc.findings, sc.smoke)
    paper_claims = [c for c in sc.claims if c.role == "paper"]
    context_claims = [c for c in sc.claims if c.role != "paper"]

    lines: list[str] = []
    add = lines.append

    title = sc.paper_meta.get("title") or "paper"
    add(f"# Reproducibility assessment — {title}")
    add("")
    add(
        f"> **Verdict: {sc.verdict} — {VERDICT_LABELS.get(sc.verdict, '')}**  "
        f"\n> Confidence: {sc.confidence:.2f} · claims examined: {len(paper_claims)}"
        + (f" (+{len(context_claims)} baseline numbers)" if context_claims else "")
    )
    add("")
    add(sc.summary)
    add("")
    add("| | |")
    add("|---|---|")
    add(f"| Paper | `{_cell(sc.paper)}` ({sc.paper_meta.get('format', '?')}, "
        f"{len(sc.paper_meta.get('tables', []))} table(s)) |")
    add(f"| Repository | `{_cell(sc.repo)}` — {sc.repo_meta.get('file_count', 0)} files, "
        f"{_cell(', '.join(f'{k}:{v}' for k, v in list(sc.repo_meta.get('languages', {}).items())[:4]))} |")
    add(f"| Generated | {sc.generated_at} |")
    add(f"| Tool | paperrepro {sc.paperrepro_version} · "
        + (f"LLM: `{sc.llm_model}`" if sc.llm_used else "rules-only (no LLM)") + " |")
    add("")

    add("## Why this verdict")
    add("")
    for reason in reasons:
        add(f"- {reason}")
    add("")

    if sc.claims:
        add("## Claim ledger")
        add("")
        add("| ID | Claim | Reported | Dataset | Evidence | Strongest code evidence |")
        add("|----|-------|----------|---------|----------|-------------------------|")
        for claim in sc.claims:
            code = claim.code_evidence[0].ref if claim.code_evidence else "—"
            role = "" if claim.role == "paper" else " _(baseline)_"
            add(
                f"| {claim.id} | {_cell(claim.raw_metric)}{role} | {_cell(claim.value)} | "
                f"{_cell(claim.dataset) or '—'} | {claim.level} | `{_cell(code)}` |"
            )
        add("")

    if sc.claims:
        add("## Claim detail")
        add("")
        for claim in sc.claims:
            add(f"### {claim.id} · {_cell(claim.raw_metric)} = {_cell(claim.value)} · `{claim.level}`")
            add("")
            for ev in claim.evidence:
                add(f"- **Paper:** `{ev.ref}`" + (f" — \"{_cell(ev.text)}\"" if ev.text else ""))
            if claim.code_evidence:
                add("- **Code:**")
                for ev in claim.code_evidence[:4]:
                    detail = f" — {_quote(ev.text)}" if ev.text else ""
                    add(f"  - `{ev.ref}`{detail}")
            else:
                add("- **Code:** nothing found")
            if claim.gaps:
                add("- **Gaps:**")
                for gap in claim.gaps:
                    add(f"  - {gap}")
            if claim.notes:
                add(f"- **Note:** {claim.notes}")
            add("")

    if sc.findings:
        add("## Risk findings")
        add("")
        for severity in ("blocker", "major", "minor", "info"):
            group = [f for f in sc.findings if f.severity == severity]
            if not group:
                continue
            add(f"### {_SEVERITY_TITLES[severity]} ({len(group)})")
            add("")
            for f in group:
                add(f"#### {f.rule_id} · {f.title}")
                add("")
                add(f.detail)
                if f.author_dependent:
                    add("")
                    add("_Only the authors can resolve this._")
                for ev in f.evidence[:4]:
                    detail = f" — {_quote(ev.text)}" if ev.text else ""
                    add(f"- `{ev.ref}`{detail}")
                add("")

    if sc.next_actions:
        add("## What to do next")
        add("")
        for idx, action in enumerate(sc.next_actions, start=1):
            add(f"{idx}. {action}")
        add("")

    add("## Reproduce this assessment")
    add("")
    add("```bash")
    add(f"paperrepro assess {_sh(sc.paper)} --repo {_sh(sc.repo)}" + ("" if not sc.smoke.enabled else " --smoke"))
    add("```")
    add("")
    add("## Limits of this report")
    add("")
    add(
        "- The analysis is static: no dependency was installed, no dataset downloaded, no model trained. "
        "E1 requires `--smoke`; without it the ceiling is E2."
    )
    add(
        "- Claim extraction reads tables and results prose. A number stated only in a figure is invisible to it."
    )
    add(
        "- A reproduced number can still differ for statistical reasons (seeds, hardware); this report "
        "judges whether the *evidence to attempt* a reproduction exists, not whether a re-run will land within 0.1."
    )
    add("")
    return "\n".join(lines)


def _sh(value: str) -> str:
    return f'"{value}"' if " " in value else value


def render_plan(sc: Scorecard) -> str:
    """A checklist someone can actually work through."""
    verdict, _confidence, _reasons = decide(sc.claims, sc.findings, sc.smoke)
    lines: list[str] = []
    add = lines.append
    add(f"# Reproduction plan for `{sc.paper_meta.get('title') or sc.paper}`")
    add("")
    add(f"Starting verdict: **{sc.verdict} — {VERDICT_LABELS.get(sc.verdict, '')}**")
    add("")
    add("## 0. Environment")
    add("")
    add("- [ ] Clone the repository at the paper's released commit and record the commit hash.")
    add("- [ ] Create a clean virtual environment; install exactly what the manifest pins.")
    add("- [ ] Record Python, CUDA, driver and GPU model — they are part of the result.")
    add("")
    add("## 1. Assets")
    add("")
    author_items = [f for f in sc.findings if f.author_dependent]
    if author_items:
        for f in author_items:
            add(f"- [ ] Obtain: {f.title.lower()} ({f.rule_id}). Ref: `{f.evidence[0].ref if f.evidence else 'n/a'}`")
    else:
        add("- [ ] No author-supplied asset was detected; confirm data and weights are downloadable.")
    add("")
    add("## 2. Claims to reproduce")
    add("")
    for claim in sc.claims:
        if claim.role != "paper":
            continue
        checked = "x" if claim.level == "E1" else " "
        add(f"- [{checked}] **{claim.id}** {_claim_line(claim)} — current evidence **{claim.level}**")
        for gap in claim.gaps:
            add(f"  - gap: {gap}")
    add("")
    add("## 3. Execution")
    add("")
    add("- [ ] Run the smallest end-to-end command the README advertises, then the evaluation script.")
    add("- [ ] Fix every absolute path and rerun; note each edit, because edits are part of the repro.")
    add("- [ ] Run with the authors' seed first, then two more seeds to measure variance.")
    add("")
    add("## 4. Comparison")
    add("")
    add("- [ ] Build the table `claim | paper | reproduced | delta | within tolerance?`.")
    add("- [ ] Decide tolerance before looking at results (e.g. abs 0.5 for accuracy in points).")
    add("- [ ] Report failures as findings, not as silent omissions.")
    add("")
    if sc.next_actions:
        add("## Open items from the audit")
        add("")
        for action in sc.next_actions:
            add(f"- [ ] {action}")
        add("")
    return "\n".join(lines)


def render_console(sc: Scorecard) -> str:
    """Short terminal summary."""
    lines = [
        f"verdict   {sc.verdict}  {VERDICT_LABELS.get(sc.verdict, '')}  (confidence {sc.confidence:.2f})",
        f"paper     {sc.paper}",
        f"repo      {sc.repo}",
    ]
    paper_claims = [c for c in sc.claims if c.role == "paper"]
    levels: dict[str, int] = {}
    for c in paper_claims:
        levels[c.level] = levels.get(c.level, 0) + 1
    lines.append(
        "claims    " + ", ".join(f"{k}:{v}" for k, v in sorted(levels.items())) if levels else "claims    none extracted"
    )
    for f in sc.findings[:3]:
        lines.append(f"  {f.severity:<7} {f.rule_id} {f.title}")
    return "\n".join(lines)
