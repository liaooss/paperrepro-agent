"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .version import __version__
from .api import assess
from .config import Settings
from .execute.case import run_case
from .execute.recipe import RecipeError
from .execute.report import render_run_console
from .ingest.paper import IngestError
from .plan import PlanError
from .risk.rules import RULES
from .verdict.report import render_console

VERDICT_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paperrepro",
        description="Assess whether a code release can reproduce a paper's reported numbers.",
    )
    parser.add_argument("--version", action="version", version=f"paperrepro {__version__}")
    sub = parser.add_subparsers(dest="command")

    ap = sub.add_parser("assess", help="assess one (paper, code) pair")
    ap.add_argument("paper", help="paper file: .tex, .md, .html or .pdf")
    ap.add_argument("--repo", required=True, help="path to the code checkout")
    ap.add_argument("--out", default="reproduction-assessment", help="output directory")
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="compile-check Python files and require an entry point (needed for E1)",
    )
    ap.add_argument("--no-llm", action="store_true", help="disable LLM enrichment")
    ap.add_argument("--json", action="store_true", help="print the scorecard JSON to stdout")
    ap.add_argument("--quiet", action="store_true", help="suppress the terminal summary")
    ap.add_argument(
        "--fail-on",
        choices=["R0", "R1", "R2", "R3"],
        help="exit with status 2 when the verdict is at or below this level (for CI)",
    )

    sub.add_parser("rules", help="list the deterministic risk rules")
    sub.add_parser("version", help="print the version")

    rp = sub.add_parser("run", help="execute a recipe and compare measured numbers with the paper")
    rp.add_argument("paper", help="paper file or URL (arXiv abs/ar5iv/PDF)")
    rp.add_argument("--repo", required=True, help="local checkout or git URL of the release")
    rp.add_argument("--recipe", default="", help="recipe JSON/YAML; omit with --auto to infer one")
    rp.add_argument("--auto", action="store_true", help="infer the plan from the repository")
    rp.add_argument("--yes", action="store_true", help="confirm executing an inferred plan")
    rp.add_argument("--plan-only", action="store_true", help="print the inferred plan and stop")
    rp.add_argument(
        "--no-repair",
        action="store_true",
        help="disable bounded repair of environment failures (dead pins, missing directories)",
    )
    rp.add_argument("--out", default="", help="output directory (default: runs/<recipe-name>)")
    rp.add_argument("--backend", default="local", choices=["local", "conda", "docker"])
    rp.add_argument("--limit-minutes", type=int, default=None, help="hard wall-clock cap")
    rp.add_argument("--gpu", action="store_true", help="pass GPUs to the backend (docker only)")
    rp.add_argument("--json", action="store_true", help="print the result JSON to stdout")
    rp.add_argument("--quiet", action="store_true", help="suppress the terminal summary")
    return parser


def _print_summary(scorecard) -> None:
    print(render_console(scorecard))
    if scorecard.summary:
        print()
        print(scorecard.summary)


def cmd_assess(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    try:
        result = assess(
            args.paper,
            args.repo,
            settings=settings,
            use_llm=False if args.no_llm else None,
            smoke=args.smoke,
        )
    except IngestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except NotADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    paths = result.write(args.out)
    if args.json:
        print(result.to_json())
    elif not args.quiet:
        _print_summary(result.scorecard)
        print()
        print(f"wrote {paths['report']}")
        print(f"wrote {paths['scorecard']}")
        print(f"wrote {paths['plan']}")

    if args.fail_on:
        reached = VERDICT_ORDER.get(result.scorecard.verdict, 0)
        if reached <= VERDICT_ORDER[args.fail_on]:
            return 2
    return 0


def cmd_rules(_args: argparse.Namespace) -> int:
    print(f"{'ID':<6} {'SEVERITY':<9} TITLE")
    for rule_id, title, severity in RULES:
        print(f"{rule_id:<6} {severity:<9} {title}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.recipe and not args.auto:
        print("error: pass --recipe FILE, or --auto to infer a plan", file=sys.stderr)
        return 1

    stem = Path(args.recipe).stem if args.recipe else "auto"
    out = args.out or f"runs/{stem}"
    try:
        assessment = run_case(
            paper=args.paper,
            repo=args.repo,
            recipe_path=args.recipe or None,
            out_dir=out,
            backend=args.backend,
            limit_minutes=args.limit_minutes,
            gpu=args.gpu,
            auto=args.auto,
            confirmed=args.yes,
            repair=not args.no_repair,
        )
    except PlanError as exc:
        if args.plan_only:
            print(str(exc))
            return 0
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (RecipeError, IngestError, NotADirectoryError, FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    paths = assessment.write(out)
    if args.json:
        import json

        print(json.dumps(assessment.to_dict(), indent=2, ensure_ascii=False))
    elif not args.quiet:
        print(render_run_console(assessment))
        print()
        print(f"wrote {paths['report']}")
        print(f"wrote {paths['results']}")
        print(f"artifacts in {assessment.run.artifacts}")

    return 0 if assessment.run.status == "ok" else 3


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in (None, "version"):
        if args.command == "version":
            print(f"paperrepro {__version__}")
            return 0
        parser.print_help()
        return 0
    if args.command == "assess":
        return cmd_assess(args)
    if args.command == "rules":
        return cmd_rules(args)
    if args.command == "run":
        return cmd_run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
