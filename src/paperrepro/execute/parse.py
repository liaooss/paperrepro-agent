"""Extract measured metric values from a run's output.

Two sources: an explicit regex named by the recipe (precise, preferred), and a
generic scanner for the many ways a script prints a number. Everything found is
kept with its surrounding line so the report can quote it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

__all__ = ["MetricHit", "extract_metrics"]

_METRIC_WORDS = (
    "accuracy|acc|f1|f1-score|macro-f1|micro-f1|bleu|rouge-l|rouge|meteor|wer|cer|"
    "psnr|ssim|lpips|fid|auc|auroc|auprc|mAP|AP50|precision|recall|ndcg|mrr|"
    "exact match|em|pass@1|top-1|top1|top-5|top5|iou|miou|dice|perplexity|ppl"
)

_GENERIC = re.compile(
    r"(?P<name>" + _METRIC_WORDS + r")"
    r"\s*(?:[:=]|\bis\b|\bof\b)?\s*"
    r"(?P<value>-?\d+(?:\.\d+)?)\s*(?P<pct>%?)",
    re.IGNORECASE,
)

# "eval_accuracy: 0.913" / '"accuracy": 0.913'
_JSON_FIELD = re.compile(
    r'"?\b(?P<name>' + _METRIC_WORDS + r')\b"?\s*[:=]\s*(?P<value>-?\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


@dataclass
class MetricHit:
    metric: str
    value: float
    line: str


def _to_float(raw: str) -> float | None:
    try:
        return float(raw)
    except ValueError:
        return None


def _scan_json_lines(text: str) -> dict[str, MetricHit]:
    hits: dict[str, MetricHit] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("{") and stripped.endswith("}")):
            continue
        try:
            payload = json.loads(stripped)
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if not isinstance(value, (int, float)):
                continue
            if not re.fullmatch(_METRIC_WORDS, str(key), re.IGNORECASE):
                continue
            hits[str(key).lower()] = MetricHit(str(key).lower(), float(value), stripped[:200])
    return hits


def extract_metrics(text: str, recipe: Any = None) -> dict[str, float]:
    """Return ``{metric: value}`` measured in ``text``.

    Precedence: explicit recipe regex > JSON lines > generic scan, so a recipe
    can always disambiguate a noisy log.
    """
    found: dict[str, MetricHit] = {}

    regex = getattr(recipe, "metric_regex", "") if recipe is not None else ""
    if regex:
        try:
            pattern = re.compile(regex, re.IGNORECASE)
        except re.error as exc:  # pragma: no cover - validated earlier
            raise ValueError(f"recipe.metric_regex is not a valid regex: {exc}") from exc
        for match in pattern.finditer(text):
            raw = match.groupdict().get("value")
            if raw is None:
                continue
            value = _to_float(raw)
            if value is None:
                continue
            metric = str(getattr(recipe, "metric", "value") or "value").lower()
            found[metric] = MetricHit(metric, value, match.group(0)[:200])
            break

    if not found:
        found.update(_scan_json_lines(text))

    if not found:
        for match in _GENERIC.finditer(text):
            name = re.sub(r"[^a-z0-9]", "", match.group("name").lower())
            value = _to_float(match.group("value"))
            if value is None:
                continue
            if match.group("pct") and value > 1:
                value = value / 100.0
            found.setdefault(name, MetricHit(name, value, match.group(0)[:200]))

    return {k: v.value for k, v in found.items()}
