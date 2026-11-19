"""Metric extraction from run output."""

import unittest

import helpers  # noqa: F401
from paperrepro.execute.parse import extract_metrics
from paperrepro.execute.recipe import Recipe


def _recipe(regex=""):
    return Recipe.from_dict({"name": "t", "eval_cmd": "x", "metric": "accuracy", "metric_regex": regex})


class TestExtractMetrics(unittest.TestCase):
    def test_explicit_regex_wins(self):
        text = "noise accuracy: 0.12\nfinal accuracy: 0.9130\n"
        metrics = extract_metrics(text, _recipe(r"final accuracy:\s*(?P<value>\d+\.\d+)"))
        self.assertAlmostEqual(metrics["accuracy"], 0.913)

    def test_json_line(self):
        text = '{"loss": 0.2, "accuracy": 0.8776}\n'
        metrics = extract_metrics(text, _recipe())
        self.assertAlmostEqual(metrics["accuracy"], 0.8776)

    def test_generic_scan(self):
        text = "Epoch 3 | dev F1: 82.5 | loss 0.31\n"
        metrics = extract_metrics(text, _recipe())
        self.assertAlmostEqual(metrics["f1"], 82.5)

    def test_percent_is_converted(self):
        text = "accuracy 91.3%\n"
        metrics = extract_metrics(text, _recipe())
        self.assertLessEqual(metrics["accuracy"], 1.0)

    def test_no_metric_returns_empty(self):
        self.assertEqual(extract_metrics("nothing useful here", _recipe()), {})

    def test_bad_regex_is_reported(self):
        with self.assertRaises(ValueError):
            extract_metrics("x", _recipe("(unclosed"))


if __name__ == "__main__":
    unittest.main()
