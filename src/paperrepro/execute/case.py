"""One end-to-end execution case: paper + release + recipe -> measured outcome."""

from __future__ import annotations

import json
import re
import shutil
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..audit import audit_parameters
from ..extract import extract_claims
from ..ingest import load_paper, scan_repo
from ..models import Claim, Evidence, Finding, PaperDoc, RepoScan
from ..plan import PlanError, infer_recipe
from ..plan.infer import describe as describe_plan
from ..risk import run_rules
from ..textutil import metric_canonical
from .compare import ClaimOutcome, compare_claims, summarise_outcomes
from .recipe import Recipe, load_recipe
from .report import render_run_markdown
from .runner import RunResult, execute_recipe
from .status import reproduction_status
from .viability import Viability, assess_viability

__all__ = ["RunAssessment", "run_case", "fetch_paper", "clone_repo"]


@dataclass
class RunAssessment:
    name: str
    paper: str
    repo: str
    recipe: Recipe
    run: RunResult
    outcomes: list[ClaimOutcome]
    viability: Viability
    claims: list[Claim] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    audit: list = field(default_factory=list)
    status: str = "INSUFFICIENT_EVIDENCE"
    status_reason: str = ""
    plan: str = ""
    markdown: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "paperrepro/run/v1",
            "name": self.name,
            "paper": self.paper,
            "repo": self.repo,
            "recipe": self.recipe.to_dict(),
            "plan": self.plan,
            "status": self.status,
            "status_reason": self.status_reason,
            "run": self.run.to_dict(),
            "claims": [c.to_dict() for c in self.claims],
            "audit": [c.to_dict() for c in self.audit],
            "outcomes": [o.to_dict() for o in self.outcomes],
            "outcome_summary": summarise_outcomes(self.outcomes),
            "viability": self.viability.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
        }

    def write(self, out_dir: str | Path) -> dict[str, Path]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        report = out / "run_report.md"
        results = out / "results.json"
        report.write_text(self.markdown, encoding="utf-8")
        results.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"report": report, "results": results}


def fetch_paper(url: str, dest: Path) -> Path:
    """Download a paper (PDF, HTML or .tex) and return the local path."""
    dest.mkdir(parents=True, exist_ok=True)
    suffix = ".pdf" if url.lower().endswith(".pdf") else ".html"
    target = dest / ("paper" + suffix)
    request = urllib.request.Request(url, headers={"User-Agent": "paperrepro/0.2"})
    with urllib.request.urlopen(request, timeout=120) as resp:
        target.write_bytes(resp.read())
    return target


def clone_repo(url: str, dest: Path) -> Path:
    """Acquire the release: shallow git clone, tarball fallback.

    Large clones fail surprisingly often on real networks ("early EOF",
    "invalid index-pack output"), and an interrupted clone leaves a directory
    that *looks* present but has no working tree. Both cases are handled here
    instead of being discovered three commands later.
    """
    import subprocess
    import tarfile
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)

    proc = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)], capture_output=True, text=True
    )
    if proc.returncode == 0 and (dest / ".git").exists() and any(dest.iterdir()):
        commit = subprocess.run(
            ["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        (dest / ".paperrepro-commit").write_text(commit, encoding="utf-8")
        return dest

    shutil.rmtree(dest, ignore_errors=True)
    match = re.match(r"https?://github\.com/([^/]+)/([^/#?]+?)(?:\.git)?/?$", url.strip())
    if not match:
        raise RuntimeError(f"git clone failed and no tarball fallback applies: {proc.stderr[-400:]}")

    owner, repo = match.group(1), match.group(2)
    last_error = proc.stderr[-400:]
    for ref in ("refs/heads/main", "refs/heads/master", "HEAD"):
        tarball = f"https://codeload.github.com/{owner}/{repo}/tar.gz/{ref}"
        try:
            request = urllib.request.Request(tarball, headers={"User-Agent": "paperrepro"})
            with urllib.request.urlopen(request, timeout=180) as resp:
                payload = resp.read()
            archive = dest.with_suffix(".tar.gz")
            archive.write_bytes(payload)
            with tarfile.open(archive) as tar:
                tar.extractall(dest.parent)
            extracted = [p for p in dest.parent.iterdir() if p.is_dir() and p.name.startswith(repo)]
            if not extracted:
                raise RuntimeError("tarball did not contain the expected directory")
            if dest.exists():
                shutil.rmtree(dest)
            extracted[0].rename(dest)
            archive.unlink(missing_ok=True)
            (dest / ".paperrepro-commit").write_text(f"tarball:{ref}", encoding="utf-8")
            return dest
        except Exception as exc:  # noqa: BLE001 - try the next ref
            last_error = f"{type(exc).__name__}: {exc}"
            continue

    raise RuntimeError(f"could not acquire {url}: {last_error}")


def _prepare_harness(recipe: Recipe, workdir: Path) -> Recipe:
    """Copy driver scripts next to the checkout so every backend can see them."""
    if not recipe.harness_dir:
        return recipe
    source = Path(recipe.harness_dir).resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"harness_dir does not exist: {source}")
    target = workdir / ".paperrepro-harness"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    (target / "recipe.json").unlink(missing_ok=True)
    (target / "README.md").unlink(missing_ok=True)
    cloned = Recipe(**{**recipe.__dict__})
    cloned.harness_dir = ".paperrepro-harness"
    return cloned


def _with_target(claims: list[Claim], recipe: Recipe) -> list[Claim]:
    """Attach the recipe's declared target when table extraction found nothing.

    Some papers put datasets in the columns and metrics in the caption (GLUE
    tables are the classic case), so a purely automatic extractor cannot see the
    claim. A recipe may state it explicitly - and must state where it came from.
    """
    target = recipe.target or {}
    value = str(target.get("value") or "").strip()
    if not value:
        return claims
    metric = str(target.get("metric") or recipe.metric)
    canonical = metric_canonical(metric) or metric
    for claim in claims:
        if claim.role == "paper" and claim.metric == canonical:
            return claims
    claim = Claim(
        id="T01",
        metric=canonical,
        raw_metric=str(target.get("raw_metric") or metric),
        value=value,
        dataset=str(target.get("dataset") or ""),
        role="paper",
        notes="Target supplied by the recipe because the paper table could not be parsed automatically.",
        evidence=[
            Evidence(
                kind="paper",
                ref=str(target.get("source") or "recipe target"),
                text=f"declared target: {metric} = {value}",
            )
        ],
    )
    return [claim] + claims


def run_case(
    paper: str,
    repo: str,
    out_dir: str | Path,
    recipe_path: str | Path | None = None,
    backend: str = "local",
    limit_minutes: int | None = None,
    gpu: bool = False,
    auto: bool = False,
    confirmed: bool = False,
) -> RunAssessment:
    """Acquire, plan, execute, audit, compare, and score one paper/release pair.

    With ``auto=True`` the recipe is inferred from the repository. An inferred
    plan is never executed until ``confirmed`` is set, because a planner that
    can run arbitrary commands unattended is a liability, not a feature.
    """
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    paper_path = Path(paper)
    if str(paper).startswith(("http://", "https://")):
        paper_path = fetch_paper(str(paper), out / "paper")

    repo_path = Path(repo)
    if str(repo).startswith(("http://", "https://", "git@")):
        repo_path = clone_repo(str(repo), out / "repo")

    doc: PaperDoc = load_paper(paper_path)
    scan: RepoScan = scan_repo(repo_path)
    claims = extract_claims(doc)

    if recipe_path:
        recipe = load_recipe(recipe_path)
        base = Path(recipe_path).resolve().parent
        if recipe.harness_dir and not Path(recipe.harness_dir).is_absolute():
            recipe.harness_dir = str(base / recipe.harness_dir)
        plan = describe_plan(recipe)
    elif auto:
        recipe = infer_recipe(doc, scan, name=Path(repo_path).name)
        plan = describe_plan(recipe)
        if not confirmed:
            raise PlanError(
                "the plan below was inferred from the repository and has not been reviewed.\n"
                "Re-run with --yes to execute it, or write a recipe and pass --recipe.\n\n" + plan
            )
    else:
        raise PlanError("nothing to run: pass --recipe FILE, or --auto to infer a plan")

    claims = _with_target(claims, recipe)
    recipe = _prepare_harness(recipe, repo_path)

    run = execute_recipe(
        recipe,
        workdir=repo_path,
        out_dir=out,
        backend_name=backend,
        limit_minutes=limit_minutes,
        gpu=gpu,
    )
    outcomes = compare_claims(
        claims, run.metrics, tolerance_abs=recipe.tolerance_abs, tolerance_rel=recipe.tolerance_rel
    )
    findings = run_rules(scan, doc, claims)
    viability = assess_viability(run, outcomes, findings)
    audit = audit_parameters(doc, scan)
    status, status_reason = reproduction_status(run, outcomes)

    assessment = RunAssessment(
        name=recipe.name,
        paper=str(paper_path),
        repo=str(repo_path),
        recipe=recipe,
        run=run,
        outcomes=outcomes,
        viability=viability,
        claims=claims,
        findings=findings,
        audit=audit,
        status=status,
        status_reason=status_reason,
        plan=plan,
    )
    assessment.markdown = render_run_markdown(assessment)
    return assessment
