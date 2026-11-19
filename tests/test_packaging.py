"""Packaging sanity: the metadata must be parseable by every supported Python."""

import sys
import unittest

import helpers

try:  # tomllib is 3.11+; the project supports 3.10
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


class TestPyproject(unittest.TestCase):
    def setUp(self):
        self.raw = (helpers.ROOT / "pyproject.toml").read_bytes()

    def test_no_byte_order_mark(self):
        # A BOM at the start breaks `pip install -e .` with a TOMLDecodeError,
        # and every editor that rewrites the file can introduce one silently.
        self.assertFalse(self.raw.startswith(b"\xef\xbb\xbf"), "pyproject.toml starts with a BOM")

    @unittest.skipIf(tomllib is None, "tomllib requires Python 3.11+")
    def test_parses_as_toml(self):
        data = tomllib.loads(self.raw.decode("utf-8"))
        self.assertEqual(data["project"]["name"], "paperrepro")
        self.assertIn("paperrepro", data["project"]["scripts"])

    def test_entry_point_target_exists(self):
        self.assertTrue((helpers.ROOT / "src" / "paperrepro" / "cli.py").exists())

    def test_python_floor(self):
        text = self.raw.decode("utf-8")
        self.assertIn("requires-python", text)


if __name__ == "__main__":
    unittest.main()
