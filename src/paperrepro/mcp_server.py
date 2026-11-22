"""A small MCP server over stdio, exposing the evidence rather than a shell.

Design decision: this server deliberately does **not** expose an "execute this
repository" tool. Running unknown code is a decision a human makes at a
terminal, with a recipe they can read; an agent calling a tool should be able to
*inspect* evidence, not to start a 10-minute container build by accident.

Tools:

- ``assess_paper`` - static assessment of a (paper, repo) pair
- ``list_runs``   - run directories under a root, with status
- ``get_run``     - one run's status, metrics and recommendation
- ``get_report``  - the Markdown report of a run

Transport: JSON-RPC 2.0, one JSON object per line on stdin/stdout. Diagnostics go
to stderr, never to stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .version import __version__

__all__ = ["MCP_PROTOCOL_VERSION", "PaperReproMCP", "serve"]

MCP_PROTOCOL_VERSION = "2024-11-05"

_TOOLS: list[dict[str, Any]] = [
    {
        "name": "assess_paper",
        "description": (
            "Statically assess whether a paper's claims are supported by a code release: builds the "
            "claim ledger, runs the deterministic risk rules, and returns the verdict with evidence. "
            "Does not execute any code."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "paper": {"type": "string", "description": "Path or http(s) URL to the paper"},
                "repo": {"type": "string", "description": "Path to a local checkout of the release"},
                "smoke": {
                    "type": "boolean",
                    "description": "Compile-check Python sources (needed for E1 evidence levels)",
                    "default": False,
                },
            },
            "required": ["paper", "repo"],
        },
    },
    {
        "name": "list_runs",
        "description": "List reproduction run directories under a root, with their status.",
        "inputSchema": {
            "type": "object",
            "properties": {"runs_dir": {"type": "string", "description": "Directory containing runs"}},
            "required": ["runs_dir"],
        },
    },
    {
        "name": "get_run",
        "description": "Return one run's status, measured metrics, claim outcomes and recommendation.",
        "inputSchema": {
            "type": "object",
            "properties": {"run_dir": {"type": "string", "description": "A run output directory"}},
            "required": ["run_dir"],
        },
    },
    {
        "name": "get_report",
        "description": "Return the Markdown report of a run, or of an assessment directory.",
        "inputSchema": {
            "type": "object",
            "properties": {"run_dir": {"type": "string", "description": "A run output directory"}},
            "required": ["run_dir"],
        },
    },
]


class MCPError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class PaperReproMCP:
    """The protocol surface. Pure functions in, JSON out, so it is testable."""

    def __init__(self) -> None:
        self.initialized = False

    # -- protocol ---------------------------------------------------------- #
    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        request_id = message.get("id")

        if method is None:
            return None
        # JSON-RPC notifications carry no id and must not be answered.
        if "id" not in message:
            return None

        try:
            if method == "initialize":
                self.initialized = True
                return _ok(
                    request_id,
                    {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {"name": "paperrepro", "version": __version__},
                    },
                )
            if method == "ping":
                return _ok(request_id, {})
            if method == "tools/list":
                return _ok(request_id, {"tools": _TOOLS})
            if method == "tools/call":
                params = message.get("params") or {}
                return _ok(request_id, self._call(params.get("name"), params.get("arguments") or {}))
            raise MCPError(-32601, f"method not found: {method}")
        except MCPError as exc:
            return _error(request_id, exc.code, exc.message)
        except Exception as exc:  # noqa: BLE001 - the protocol must not crash
            return _error(request_id, -32603, f"{type(exc).__name__}: {exc}")

    # -- tools ------------------------------------------------------------- #
    def _call(self, name: str | None, args: dict[str, Any]) -> dict[str, Any]:
        if name == "assess_paper":
            return self._assess(args)
        if name == "list_runs":
            return self._list_runs(args)
        if name == "get_run":
            return self._get_run(args)
        if name == "get_report":
            return self._get_report(args)
        raise MCPError(-32602, f"unknown tool: {name}")

    def _assess(self, args: dict[str, Any]) -> dict[str, Any]:
        from .api import assess

        paper = args.get("paper")
        repo = args.get("repo")
        if not paper or not repo:
            raise MCPError(-32602, "both 'paper' and 'repo' are required")
        result = assess(paper, repo, smoke=bool(args.get("smoke")), use_llm=False)
        sc = result.scorecard
        lines = [
            f"verdict: {sc.verdict} ({sc.confidence:.2f} confidence)",
            f"claims: " + ", ".join(f"{c.id}={c.level}" for c in sc.claims) or "none",
            "",
            "findings:",
        ]
        for finding in sc.findings[:8]:
            ref = finding.evidence[0].ref if finding.evidence else ""
            lines.append(f"- {finding.severity} {finding.rule_id} {finding.title} ({ref})")
        return _text("\n".join(lines))

    def _list_runs(self, args: dict[str, Any]) -> dict[str, Any]:
        root = Path(str(args.get("runs_dir") or ".")).expanduser()
        if not root.is_dir():
            raise MCPError(-32602, f"not a directory: {root}")
        runs: list[str] = []
        for candidate in sorted(root.iterdir()):
            payload = candidate / "results.json"
            nested = candidate / "attempt-1" / "run.json"
            if payload.exists():
                try:
                    data = json.loads(payload.read_text(encoding="utf-8"))
                except ValueError:
                    runs.append(f"{candidate.name}: unreadable results.json")
                    continue
                runs.append(
                    f"{candidate.name}: {data.get('status', '?')} "
                    f"({data.get('name', '')}) metrics={data.get('run', {}).get('metrics', {})}"
                )
            elif nested.exists():
                runs.append(f"{candidate.name}: run.json only (no results.json)")
        return _text("\n".join(runs) if runs else f"no runs under {root}")

    def _get_run(self, args: dict[str, Any]) -> dict[str, Any]:
        data = _load_results(args)
        run = data.get("run", {})
        recommendation = data.get("recommendation") or {}
        lines = [
            f"status: {data.get('status', '?')} - {data.get('status_reason', '')}",
            f"metrics: {run.get('metrics', {})}",
            f"backend: {run.get('backend', '?')}  duration: {run.get('duration_s', 0):.0f}s",
            f"viability: {data.get('viability', {}).get('score', '?')} ({data.get('viability', {}).get('label', '')})",
            f"recommendation: {recommendation.get('label', 'n/a')}",
        ]
        for outcome in data.get("outcomes", []):
            lines.append(
                f"- {outcome['claim_id']} {outcome['metric']}: paper={outcome['paper_value']} "
                f"measured={outcome['measured']} delta={outcome['delta']} {outcome['status']}"
            )
        return _text("\n".join(lines))

    def _get_report(self, args: dict[str, Any]) -> dict[str, Any]:
        run = Path(str(args.get("run_dir") or "")).expanduser()
        for name in ("run_report.md", "report.md"):
            candidate = run / name
            if candidate.exists():
                return _text(candidate.read_text(encoding="utf-8", errors="replace"))
        raise MCPError(-32602, f"no run_report.md or report.md in {run}")


def _ok(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _text(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _load_results(args: dict[str, Any]) -> dict[str, Any]:
    run = Path(str(args.get("run_dir") or "")).expanduser()
    for candidate in (run / "results.json", run / "run.json"):
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except ValueError as exc:
                raise MCPError(-32603, f"unreadable {candidate}: {exc}") from exc
    raise MCPError(-32602, f"no results.json or run.json in {run}")


def serve() -> int:
    """Run the stdio loop until stdin closes."""
    server = PaperReproMCP()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            print(json.dumps(_error(None, -32700, "parse error")), flush=True)
            continue
        response = server.handle(message)
        if response is not None:
            print(json.dumps(response), flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(serve())
