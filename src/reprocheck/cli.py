"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .version import __version__
from .api import assess
from .config import Settings
from .ingest.paper import IngestError
from .risk.rules import RULES
from .verdict.report import render_console

VERDICT_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reprocheck",
        description="Assess whether a code release can reproduce a paper's reported numbers.",
    )
    parser.add_argument("--version", action="version", version=f"reprocheck {__version__}")
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in (None, "version"):
        if args.command == "version":
            print(f"reprocheck {__version__}")
            return 0
        parser.print_help()
        return 0
    if args.command == "assess":
        return cmd_assess(args)
    if args.command == "rules":
        return cmd_rules(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
