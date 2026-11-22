"""The read-only web view over run directories."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import helpers  # noqa: F401
from paperrepro.webapp import index_rows, make_server, render_markdown


class TestMarkdown(unittest.TestCase):
    def test_headings_and_tables(self):
        html = render_markdown("# Title\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("<th>a</th>", html)
        self.assertIn("<td>2</td>", html)

    def test_inline_code_and_bold(self):
        html = render_markdown("use `--smoke` and **cite** it")
        self.assertIn("<code>--smoke</code>", html)
        self.assertIn("<strong>cite</strong>", html)

    def test_code_block_is_escaped(self):
        html = render_markdown("```\n<script>alert(1)</script>\n```")
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_lists_and_quotes(self):
        html = render_markdown("- one\n- two\n\n> note\n")
        self.assertEqual(html.count("<li>"), 2)
        self.assertIn("<blockquote>note</blockquote>", html)


class TestServer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        run = self.root / "demo"
        run.mkdir()
        (run / "results.json").write_text(
            json.dumps({"status": "REPRODUCED", "run": {"metrics": {"accuracy": 0.91}}}),
            encoding="utf-8",
        )
        (run / "run_report.md").write_text("# Demo run\n\n| metric | value |\n|---|---|\n| acc | 0.91 |\n")
        (self.root / "not-a-run").mkdir()

        self.server = make_server(self.root, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def _get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as response:
            return response.status, response.read().decode("utf-8")

    def test_index_lists_runs(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("demo", body)
        self.assertNotIn("not-a-run", body)

    def test_api_runs(self):
        status, body = self._get("/api/runs")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["status"], "REPRODUCED")

    def test_run_page_renders_report(self):
        status, body = self._get("/run/demo")
        self.assertEqual(status, 200)
        self.assertIn("Demo run", body)
        self.assertIn("<table>", body)

    def test_unknown_run_is_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/run/nope")
        self.assertEqual(ctx.exception.code, 404)

    def test_path_traversal_is_refused(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/run/..%2F..%2Fetc")
        self.assertEqual(ctx.exception.code, 404)

    def test_index_rows_skips_non_runs(self):
        names = {row["name"] for row in index_rows(self.root)}
        self.assertEqual(names, {"demo"})


if __name__ == "__main__":
    unittest.main()
