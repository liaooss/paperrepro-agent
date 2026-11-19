"""Text normalisation and metric matching."""

import unittest

import helpers  # noqa: F401  (puts src/ on sys.path)
from paperrepro.textutil import (
    dataset_canonical,
    find_alias,
    is_number,
    line_of,
    metric_canonical,
    norm,
)


class TestMetricCanonical(unittest.TestCase):
    def test_table_headers(self):
        self.assertEqual(metric_canonical("ImageNet Top-1"), "accuracy")
        self.assertEqual(metric_canonical("Top-5 Accuracy"), "top5_accuracy")
        self.assertEqual(metric_canonical("Zero-shot ImageNet"), "zero_shot_accuracy")
        self.assertEqual(metric_canonical("mAP"), "map")
        self.assertEqual(metric_canonical("BLEU-4"), "bleu")
        self.assertEqual(metric_canonical("F1"), "f1")

    def test_properties_are_not_metrics(self):
        self.assertIsNone(metric_canonical("Params"))
        self.assertIsNone(metric_canonical("FLOPs"))
        self.assertIsNone(metric_canonical("Latency (ms)"))
        self.assertIsNone(metric_canonical("Method"))

    def test_unknown_header(self):
        self.assertIsNone(metric_canonical("Favourite colour"))


class TestDatasetCanonical(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(dataset_canonical("Results on CIFAR-10."), "cifar10")
        self.assertEqual(dataset_canonical("ImageNet-1k"), "imagenet")
        self.assertEqual(dataset_canonical("MS-COCO"), "coco")
        self.assertIsNone(dataset_canonical("our private corpus"))


class TestNumbers(unittest.TestCase):
    def test_is_number(self):
        for good in ("72.3", "-1.5", "0", "1,234"):
            self.assertTrue(is_number(good), good)
        for bad in ("88M", "n/a", "", "±0.4", "72.3±0.4"):
            self.assertFalse(is_number(bad), bad)


class TestFindAlias(unittest.TestCase):
    def test_word_boundaries(self):
        self.assertGreaterEqual(find_alias("batch_size=256  # acc", "acc"), 0)
        self.assertEqual(find_alias("accepted papers", "acc"), -1)

    def test_long_alias_substring(self):
        self.assertGreaterEqual(find_alias("def top1_accuracy(logits)", "accuracy"), 0)


class TestLineNumbers(unittest.TestCase):
    def test_line_of(self):
        text = "a\nb\nc"
        self.assertEqual(line_of(text, 0), 1)
        self.assertEqual(line_of(text, 2), 2)
        self.assertEqual(line_of(text, 4), 3)

    def test_norm(self):
        self.assertEqual(norm("  Hello   World "), "hello world")


if __name__ == "__main__":
    unittest.main()
