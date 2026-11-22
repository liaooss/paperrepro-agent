"""A read-only web view over run directories.

A run writes a directory: ``run_report.md``, ``results.json`` and raw logs. This
module serves that directory, and nothing else. It is a viewer, not a console:
there is no way to start a run from the browser, because starting one is a
decision with a cost attached.

Standard library only, bound to localhost by default.
"""

from __future__ import annotations

import html
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

__all__ = ["render_markdown", "serve", "make_server", "index_rows"]

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:-]+\|[\s:|-]+\|?\s*$")
_LIST_ITEM = re.compile(r"^\s*[-*]\s+(.*)$")
_ORDERED_ITEM = re.compile(r"^\s*\d+\.\s+(.*)$")


def _inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def render_markdown(text: str) -> str:
    """A deliberately small Markdown subset: headings, tables, code, lists."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    in_code = False
    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(html.escape(line, quote=False))
            i += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        # Pipe table: header row followed by a separator row.
        if "|" in line and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append("<table><thead><tr>")
            out.extend(f"<th>{_inline(c)}</th>" for c in header)
            out.append("</tr></thead><tbody>")
            j = i + 2
            while j < len(lines) and "|" in lines[j] and lines[j].strip():
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
                j += 1
            out.append("</tbody></table>")
            i = j
            continue

        if line.startswith("> "):
            out.append(f"<blockquote>{_inline(line[2:])}</blockquote>")
            i += 1
            continue

        item = _LIST_ITEM.match(line) or _ORDERED_ITEM.match(line)
        if item:
            out.append("<ul>")
            while i < len(lines):
                match = _LIST_ITEM.match(lines[i]) or _ORDERED_ITEM.match(lines[i])
                if not match:
                    break
                out.append(f"<li>{_inline(match.group(1))}</li>")
                i += 1
            out.append("</ul>")
            continue

        if line.strip():
            out.append(f"<p>{_inline(line)}</p>")
        i += 1

    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def index_rows(root: Path) -> list[dict[str, Any]]:
    """One row per run directory under ``root``."""
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return rows
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        report = next((p for p in (entry / "run_report.md", entry / "report.md") if p.exists()), None)
        results = entry / "results.json"
        if report is None and not results.exists():
            continue
        status = ""
        metrics: dict[str, Any] = {}
        if results.exists():
            try:
                data = json.loads(results.read_text(encoding="utf-8"))
                status = data.get("status", "")
                metrics = (data.get("run") or {}).get("metrics", {}) or {}
            except ValueError:
                status = "unreadable"
        rows.append(
            {
                "name": entry.name,
                "status": status,
                "metrics": metrics,
                "has_report": report is not None,
            }
        )
    return rows


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<style>"
        "body{font:15px/1.6 -apple-system,Segoe UI,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;color:#1b1f24}"
        "pre{background:#f6f8fa;padding:1rem;overflow:auto;border-radius:6px}"
        "code{background:#f6f8fa;padding:.1rem .3rem;border-radius:4px}"
        "table{border-collapse:collapse;margin:1rem 0}th,td{border:1px solid #d0d7de;padding:.35rem .6rem;text-align:left}"
        "th{background:#f6f8fa}blockquote{border-left:3px solid #d0d7de;margin:0;padding-left:1rem;color:#57606a}"
        "a{color:#0969da;text-decoration:none}a:hover{text-decoration:underline}"
        "</style></head><body>"
        f"<h1>{html.escape(title)}</h1>{body}"
        "<hr><p style='color:#57606a'>PaperRepro - read-only view</p>"
        "</body></html>"
    )


def make_server(root: Path, port: int = 0, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    root = Path(root).expanduser().resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "PaperReproWeb/1.0"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return  # keep stdout clean

        def _send(self, body: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802 - http.server API
            path = unquote(urlparse(self.path).path)

            if path in {"/", "/index.html"}:
                rows = index_rows(root)
                items = "".join(
                    f"<tr><td><a href='/run/{html.escape(r['name'])}'>{html.escape(r['name'])}</a></td>"
                    f"<td>{html.escape(str(r['status']))}</td>"
                    f"<td><code>{html.escape(json.dumps(r['metrics']))}</code></td></tr>"
                    for r in rows
                )
                body = (
                    f"<p>{len(rows)} run(s) under <code>{html.escape(str(root))}</code></p>"
                    "<table><thead><tr><th>Run</th><th>Status</th><th>Metrics</th></tr></thead>"
                    f"<tbody>{items}</tbody></table>"
                )
                return self._send(_page("PaperRepro runs", body))

            if path == "/api/runs":
                return self._send(
                    json.dumps(index_rows(root), indent=2),
                    content_type="application/json; charset=utf-8",
                )

            if path.startswith("/api/run/"):
                name = path[len("/api/run/") :]
                target = (root / name / "results.json").resolve()
                if not str(target).startswith(str(root)) or not target.exists():
                    return self._send("not found", 404)
                return self._send(
                    target.read_text(encoding="utf-8"), content_type="application/json; charset=utf-8"
                )

            if path.startswith("/run/"):
                name = path[len("/run/") :].strip("/")
                directory = (root / name).resolve()
                if not str(directory).startswith(str(root)) or not directory.is_dir():
                    return self._send("not found", 404)
                for candidate in ("run_report.md", "report.md"):
                    if (directory / candidate).exists():
                        markdown = (directory / candidate).read_text(encoding="utf-8", errors="replace")
                        return self._send(_page(name, render_markdown(markdown)))
                return self._send(f"<p>no report in {html.escape(name)}</p>", 404)

            return self._send("not found", 404)

    return ThreadingHTTPServer((host, port), Handler)


def serve(runs_dir: str | Path, port: int = 8765, host: str = "127.0.0.1") -> None:
    server = make_server(Path(runs_dir), port=port, host=host)
    url = f"http://{host}:{server.server_address[1]}/"
    print(f"PaperRepro web view: {url}")
    print(f"serving {Path(runs_dir).resolve()} (read-only, Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
