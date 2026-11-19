"""Runtime configuration, all of it optional and environment-driven."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MAX_FILE_BYTES = 512 * 1024
DEFAULT_MAX_FILES = 4000
DEFAULT_LLM_TIMEOUT = 90


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class Settings:
    """Everything the pipeline needs to know about its environment."""

    # Repository scanning limits.
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES
    max_files: int = DEFAULT_MAX_FILES

    # LLM enrichment. Any OpenAI-compatible endpoint works; when the key is
    # missing the pipeline degrades to rules-only and says so in the report.
    llm_enabled: bool = True
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout: int = DEFAULT_LLM_TIMEOUT
    llm_cache_dir: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            max_file_bytes=_env_int("REPROCHECK_MAX_FILE_BYTES", DEFAULT_MAX_FILE_BYTES),
            max_files=_env_int("REPROCHECK_MAX_FILES", DEFAULT_MAX_FILES),
            llm_enabled=_env_bool("REPROCHECK_LLM", True),
            llm_base_url=(
                os.environ.get("REPROCHECK_BASE_URL")
                or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1"
            ).rstrip("/"),
            llm_api_key=(
                os.environ.get("REPROCHECK_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or ""
            ),
            llm_model=(
                os.environ.get("REPROCHECK_MODEL")
                or os.environ.get("OPENAI_MODEL")
                or ""
            ),
            llm_timeout=_env_int("REPROCHECK_LLM_TIMEOUT", DEFAULT_LLM_TIMEOUT),
            llm_cache_dir=os.environ.get("REPROCHECK_CACHE_DIR", ""),
        )

    @property
    def llm_available(self) -> bool:
        return bool(self.llm_enabled and self.llm_api_key and self.llm_model)
