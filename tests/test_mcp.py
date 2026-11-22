"""MCP protocol surface, exercised without spawning a process."""

import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from paperrepro.mcp_server import MCP_PROTOCOL_VERSION, PaperReproMCP


class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.server = PaperReproMCP()

    def test_initialize(self):
        response = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(response["result"]["protocolVersion"], MCP_PROTOCOL_VERSION)
        self.assertIn("tools", response["result"]["capabilities"])
        self.assertEqual(response["result"]["serverInfo"]["name"], "paperrepro")

    def test_ping(self):
        response = self.server.handle({"jsonrpc": "2.0", "id": 2, "method": "ping"})
        self.assertEqual(response["result"], {})

    def test_tools_list(self):
        response = self.server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(names, {"assess_paper", "list_runs", "get_run", "get_report"})
        for tool in response["result"]["tools"]:
            self.assertIn("inputSchema", tool)

    def test_unknown_method(self):
        response = self.server.handle({"jsonrpc": "2.0", "id": 4, "method": "nope"})
        self.assertEqual(response["error"]["code"], -32601)
        self.assertIsNone(response.get("result"))

    def test_unknown_tool(self):
        response = self.server.handle(
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "rm_rf"}}
        )
        self.assertEqual(response["error"]["code"], -32602)

    def test_notification_has_no_response(self):
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))


class TestTools(unittest.TestCase):
    def setUp(self):
        self.server = PaperReproMCP()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / "demo-run"
        self.run.mkdir()
        (self.run / "results.json").write_text(
            json.dumps(
                {
                    "name": "demo",
                    "status": "REPRODUCED",
                    "status_reason": "all claims match",
                    "run": {"metrics": {"accuracy": 0.91}, "backend": "local", "duration_s": 60},
                    "viability": {"score": 4.3, "label": "use as a baseline"},
                    "recommendation": {"label": "use as a baseline"},
                    "outcomes": [
                        {
                            "claim_id": "C01",
                            "metric": "accuracy",
                            "paper_value": "91.3",
                            "measured": 91.06,
                            "delta": -0.24,
                            "status": "MATCH",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.run / "run_report.md").write_text("# Reproduction run\n\naccuracy 0.9106\n", encoding="utf-8")

    def _call(self, name, args):
        response = self.server.handle(
            {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": name, "arguments": args}}
        )
        return response["result"]["content"][0]["text"]

    def test_list_runs(self):
        text = self._call("list_runs", {"runs_dir": str(self.root)})
        self.assertIn("demo-run", text)
        self.assertIn("REPRODUCED", text)

    def test_get_run(self):
        text = self._call("get_run", {"run_dir": str(self.run)})
        self.assertIn("REPRODUCED", text)
        self.assertIn("0.91", text)
        self.assertIn("use as a baseline", text)
        self.assertIn("C01", text)

    def test_get_report(self):
        text = self._call("get_report", {"run_dir": str(self.run)})
        self.assertIn("# Reproduction run", text)

    def test_missing_report_is_an_error(self):
        empty = self.root / "empty"
        empty.mkdir()
        response = self.server.handle(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {"name": "get_report", "arguments": {"run_dir": str(empty)}},
            }
        )
        self.assertIn("error", response)

    def test_assess_requires_both_arguments(self):
        response = self.server.handle(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {"name": "assess_paper", "arguments": {"paper": "x"}},
            }
        )
        self.assertEqual(response["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
