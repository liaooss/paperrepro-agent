"""Recipe parsing: the execution contract."""

import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from paperrepro.execute.recipe import Recipe, RecipeError, load_recipe


class TestRecipe(unittest.TestCase):
    def test_minimal_recipe_defaults(self):
        recipe = Recipe.from_dict({"name": "x", "eval_cmd": "python run.py"})
        self.assertEqual(recipe.python, "3.11")
        self.assertEqual(recipe.tolerance_abs, 0.5)
        self.assertEqual(recipe.source, "curated")
        self.assertEqual(recipe.install, [])

    def test_missing_required_fields(self):
        with self.assertRaises(RecipeError):
            Recipe.from_dict({"name": "x"})
        with self.assertRaises(RecipeError):
            Recipe.from_dict({"eval_cmd": "python run.py"})

    def test_string_commands_become_lists(self):
        recipe = Recipe.from_dict(
            {"name": "x", "eval_cmd": "run", "install": "pip install -e .", "data": "fetch"}
        )
        self.assertEqual(recipe.install, ["pip install -e ."])
        self.assertEqual(recipe.data, ["fetch"])

    def test_load_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(
                json.dumps({"name": "t", "eval_cmd": "run", "metric": "f1", "tolerance_abs": 0.2}),
                encoding="utf-8",
            )
            recipe = load_recipe(path)
        self.assertEqual(recipe.metric, "f1")
        self.assertEqual(recipe.tolerance_abs, 0.2)

    def test_missing_file(self):
        with self.assertRaises(RecipeError):
            load_recipe("does-not-exist.json")

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(RecipeError):
                load_recipe(path)

    def test_shipped_recipe_is_valid(self):
        path = helpers.ROOT / "examples" / "cases" / "distilbert-sst2" / "recipe.json"
        recipe = load_recipe(path)
        self.assertEqual(recipe.name, "distilbert-sst2")
        self.assertTrue(recipe.metric_regex)
        self.assertTrue(recipe.harness_dir)


if __name__ == "__main__":
    unittest.main()
