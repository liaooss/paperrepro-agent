"""Paper ingest: LaTeX, Markdown and HTML."""

import unittest
from pathlib import Path

import helpers
from reprocheck.ingest.paper import IngestError, load_paper


class TestLatex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_paper(helpers.TEX_PAPER)

    def test_format_and_title(self):
        self.assertEqual(self.doc.format, "tex")
        self.assertIn("Repro Test Paper", self.doc.title)

    def test_table_recovered_with_header(self):
        self.assertEqual(len(self.doc.tables), 1)
        table = self.doc.tables[0]
        self.assertEqual(table.header, ["Method", "Accuracy", "F1"])
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(table.rows[1][0], "Ours")
        self.assertIn("CIFAR-10", table.caption)

    def test_sections_are_named(self):
        joined = " ".join(self.doc.sections)
        self.assertIn("Method", joined)
        self.assertIn("Experiments", joined)
        self.assertIn("Main results", joined)

    def test_table_environment_stripped_from_prose(self):
        self.assertNotIn("\\begin{tabular}", self.doc.sections.get("Main results", ""))


class TestMarkdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_paper(helpers.DEMO_PAPER)

    def test_table(self):
        self.assertEqual(len(self.doc.tables), 1)
        table = self.doc.tables[0]
        self.assertEqual(table.header[0], "Method")
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(table.rows[1][:2], ["TinyCLIP (ours)", "72.3"])

    def test_title_from_first_h1(self):
        self.assertIn("TinyCLIP", self.doc.title)


class TestHtml(unittest.TestCase):
    def test_headings_and_tables(self):
        import tempfile

        html = """
        <html><head><title>HTML Paper</title></head>
        <body>
        <h1>Main</h1><p>We report 91.2 accuracy on CIFAR-10.</p>
        <h2>Results</h2>
        <table><caption>Table one</caption>
          <tr><th>Method</th><th>Accuracy</th></tr>
          <tr><td>Ours</td><td>95.3</td></tr>
        </table>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.html"
            path.write_text(html, encoding="utf-8")
            doc = load_paper(path)
        self.assertEqual(doc.format, "html")
        self.assertEqual(doc.title, "HTML Paper")
        self.assertEqual(len(doc.tables), 1)
        self.assertEqual(doc.tables[0].header, ["Method", "Accuracy"])
        self.assertIn("Results", " ".join(doc.sections))


class TestErrors(unittest.TestCase):
    def test_missing_paper(self):
        with self.assertRaises(IngestError):
            load_paper("does-not-exist.tex")

    def test_empty_paper(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.md"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(IngestError):
                load_paper(path)


if __name__ == "__main__":
    unittest.main()
