"""LLM client: configuration, graceful degradation, JSON robustness."""

import unittest
from unittest import mock

import helpers  # noqa: F401
from paperrepro.config import Settings
from paperrepro.llm.client import LLMClient, _parse_json


class TestSettings(unittest.TestCase):
    def test_no_key_means_unavailable(self):
        settings = Settings(llm_enabled=True, llm_api_key="", llm_model="")
        self.assertFalse(settings.llm_available)

    def test_key_and_model_means_available(self):
        settings = Settings(llm_api_key="k", llm_model="m")
        self.assertTrue(settings.llm_available)

    def test_env_overrides(self):
        env = {
            "PAPERREPRO_API_KEY": "secret",
            "PAPERREPRO_MODEL": "deepseek-chat",
            "PAPERREPRO_BASE_URL": "https://api.example.com/v1/",
        }
        with mock.patch.dict("os.environ", env, clear=False):
            settings = Settings.from_env()
        self.assertTrue(settings.llm_available)
        self.assertEqual(settings.llm_model, "deepseek-chat")
        self.assertEqual(settings.llm_base_url, "https://api.example.com/v1")


class TestDegradation(unittest.TestCase):
    def test_unconfigured_client_returns_empty_summary(self):
        client = LLMClient(Settings(llm_api_key="", llm_model=""))
        self.assertFalse(client.available)
        self.assertEqual(client.summarise("facts"), "")

    def test_suggest_dataset_is_noop_without_key(self):
        class FakeClaim:
            dataset = ""
            raw_metric = "accuracy"
            value = "1.0"
            evidence = []

        client = LLMClient(Settings(llm_api_key="", llm_model=""))
        self.assertEqual(client.suggest_dataset(FakeClaim(), set()), "")


class TestJsonParsing(unittest.TestCase):
    def test_plain_object(self):
        self.assertEqual(_parse_json('{"summary": "ok"}'), {"summary": "ok"})

    def test_fenced_object(self):
        self.assertEqual(_parse_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_garbage_returns_none(self):
        for bad in ("", "no json here", "[1, 2, 3]", "{broken"):
            self.assertIsNone(_parse_json(bad), bad)


if __name__ == "__main__":
    unittest.main()
