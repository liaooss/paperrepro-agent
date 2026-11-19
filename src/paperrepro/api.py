"""The public API: one call, one assessment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .align import link_claims
from .config import Settings
from .extract import extract_claims
from .ingest import load_paper, scan_repo
from .llm import LLMClient
from .models import Scorecard, SmokeReport
from .risk import run_rules
from .smoke import run_smoke
from .textutil import human_list
from .verdict.report import render_markdown, render_plan
from .verdict.score import build_scorecard

__all__ = ["Assessment", "assess"]


@dataclass
class Assessment:
    """Everything one audit produces."""

    scorecard: Scorecard
    markdown: str
    plan: str

    def to_json(self) -> str:
        return json.dumps(self.scorecard.to_dict(), indent=2, ensure_ascii=False)

    def write(self, out_dir: str | Path) -> dict[str, Path]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = {
            "report": out / "report.md",
            "scorecard": out / "scorecard.json",
            "plan": out / "reproduction_plan.md",
        }
        paths["report"].write_text(self.markdown, encoding="utf-8")
        paths["scorecard"].write_text(self.to_json() + "\n", encoding="utf-8")
        paths["plan"].write_text(self.plan, encoding="utf-8")
        return paths


def _fetch_paper(url: str) -> str:
    """Download a paper URL once, so ``assess`` accepts the same inputs as ``run``."""
    import tempfile
    from pathlib import Path

    from .execute.case import fetch_paper

    target = Path(tempfile.mkdtemp(prefix="paperrepro-paper-"))
    return str(fetch_paper(url, target))


def _facts(sc: Scorecard) -> str:
    """A compact, factual digest the LLM is allowed to talk about."""
    lines = [
        f"verdict: {sc.verdict}",
        f"claims: {len([c for c in sc.claims if c.role == 'paper'])} paper claims",
    ]
    for c in [c for c in sc.claims if c.role == "paper"][:8]:
        lines.append(f"- {c.id}: {c.raw_metric}={c.value} on {c.dataset or 'unknown'} -> {c.level}")
    for f in sc.findings[:6]:
        lines.append(f"- {f.severity} {f.rule_id} {f.title}: {f.detail[:180]}")
    return "\n".join(lines)


def assess(
    paper: str | Path,
    repo: str | Path,
    settings: Settings | None = None,
    use_llm: bool | None = None,
    smoke: bool = False,
) -> Assessment:
    """Assess whether ``repo`` can reproduce the claims in ``paper``.

    Parameters
    ----------
    paper:
        Path to a ``.tex``, ``.md``, ``.html`` or ``.pdf`` paper.
    repo:
        Path to a local checkout of the code.
    settings:
        Runtime settings; read from the environment when omitted.
    use_llm:
        ``None`` means "use it if configured", ``False`` forces rules-only.
    smoke:
        Compile-check Python sources and require an entry point.  Without it no
        claim can reach the executable (E1) level.
    """
    settings = settings or Settings.from_env()
    if str(paper).startswith(("http://", "https://")):
        paper = _fetch_paper(str(paper))
    doc = load_paper(paper)
    scan = scan_repo(repo, settings)
    claims = extract_claims(doc)

    client: LLMClient | None = None
    llm_used = False
    llm_model = ""
    if use_llm is None:
        use_llm = settings.llm_available
    if use_llm and settings.llm_available:
        client = LLMClient(settings)
        llm_model = client.model
        # A missing dataset is the one field the model may help with, and only
        # when it cites evidence it was shown.
        for claim in claims:
            if claim.dataset:
                continue
            ids = {ev.ref for ev in claim.evidence}
            guess = client.suggest_dataset(claim, ids)
            if guess:
                claim.dataset = guess
                claim.notes = (claim.notes + " Dataset inferred by the configured LLM.").strip()
                llm_used = True

    smoke_report = run_smoke(scan) if smoke else SmokeReport(enabled=False)
    link_claims(claims, scan, smoke_report)
    findings = run_rules(scan, doc, claims)

    scorecard = build_scorecard(
        doc, scan, claims, findings, smoke_report, llm_used=llm_used, llm_model=llm_model
    )

    if client is not None:
        summary = client.summarise(_facts(scorecard))
        if summary:
            scorecard.summary = summary
            scorecard.llm_used = True
            scorecard.llm_model = client.model
            llm_used = True

    return Assessment(
        scorecard=scorecard,
        markdown=render_markdown(scorecard),
        plan=render_plan(scorecard),
    )
