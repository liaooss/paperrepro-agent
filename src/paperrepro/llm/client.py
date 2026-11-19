"""Optional LLM enrichment, strictly subordinate to the deterministic core.

The LLM never invents evidence.  It is given identifiers of evidence objects
that already exist and may only (a) restate the summary and (b) suggest a
dataset for a claim that has none.  Every suggestion is validated against the
supplied evidence list and dropped when it does not check out, so a hallucinating
model degrades the report's prose, never its facts.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ..config import Settings

__all__ = ["LLMClient"]

_SYSTEM = (
    "You audit reproducibility of machine-learning papers. You answer with JSON only. "
    "You never invent file paths, numbers or datasets: everything you say must be traceable "
    "to the evidence identifiers you are given. If the evidence is insufficient, say so."
)

_SUMMARY_PROMPT = """Paper claims and code evidence have already been extracted deterministically.
Write a 3-4 sentence executive summary for a reader deciding whether to attempt a reproduction.

Rules:
- Use only the supplied facts. Do not add numbers that are not present.
- Name the single most important blocker, if any.
- End with one concrete next step.
- No markdown, no bullet points.

Facts:
{facts}

Return JSON: {{"summary": "..."}}
"""

_DATASET_PROMPT = """A paper claim has no dataset attached. Choose the dataset it was measured on,
but only if the supplied evidence clearly names one. Otherwise return an empty string.

Claim: metric={metric}, value={value}, table header={header}
Evidence snippets:
{evidence}

Return JSON: {{"dataset": "...", "evidence_id": "..."}}
"""


class LLMClient:
    """Minimal OpenAI-compatible chat client with an on-disk cache."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url.rstrip("/")
        cache_dir = settings.llm_cache_dir or str(Path.home() / ".cache" / "paperrepro")
        self.cache_dir = Path(cache_dir)

    @property
    def available(self) -> bool:
        return self.settings.llm_available

    def _cache_path(self, payload: dict[str, Any]) -> Path:
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{key}.json"

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        cached = self._cache_path(payload)
        if cached.exists():
            try:
                return json.loads(cached.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.llm_api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.settings.llm_timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps(body), encoding="utf-8")
        except OSError:
            pass
        return body

    def _chat_json(self, user: str, max_tokens: int = 500) -> dict[str, Any] | None:
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
        }
        try:
            body = self._post(payload)
            content = body["choices"][0]["message"]["content"]
            return _parse_json(content)
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError, OSError):
            return None

    # -- public enrichment hooks ----------------------------------------- #
    def summarise(self, facts: str) -> str:
        if not self.available:
            return ""
        data = self._chat_json(_SUMMARY_PROMPT.format(facts=facts), max_tokens=350)
        if not data:
            return ""
        summary = str(data.get("summary", "")).strip()
        return summary if 20 <= len(summary) <= 1200 else ""

    def suggest_dataset(self, claim, evidence_ids: set[str]) -> str:
        """Fill a missing dataset only when the model cites evidence we gave it."""
        if not self.available or claim.dataset:
            return ""
        evidence = "\n".join(f"- [{e.ref}] {e.text}" for e in claim.evidence[:3])
        data = self._chat_json(
            _DATASET_PROMPT.format(
                metric=claim.raw_metric, value=claim.value, header=claim.raw_metric, evidence=evidence
            ),
            max_tokens=150,
        )
        if not data:
            return ""
        dataset = str(data.get("dataset", "")).strip()
        cited = str(data.get("evidence_id", "")).strip()
        if not dataset or not cited:
            return ""
        # Accept only if the model cited evidence it was actually shown.
        if cited not in evidence_ids:
            return ""
        return dataset[:60]


def _parse_json(content: str) -> dict[str, Any] | None:
    content = (content or "").strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(content[start : end + 1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def resolve_settings(settings: Settings | None) -> Settings:
    return settings or Settings.from_env()
