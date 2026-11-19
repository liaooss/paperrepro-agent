"""Claim extraction: which numbers would a reproduction have to match?"""

from __future__ import annotations

import re

from ..models import Claim, Evidence, PaperDoc, PaperTable
from ..textutil import (
    METRIC_SYNONYMS,
    dataset_canonical,
    is_number,
    metric_canonical,
    norm,
    split_sentences,
)

__all__ = ["extract_claims"]

MAX_CLAIMS = 40

_OURS = re.compile(r"\b(ours?|this work|proposed|our method|our model)\b", re.IGNORECASE)
_DATASET_HEADERS = ("dataset", "data", "corpus", "benchmark", "task")
_SPLIT_HINTS = ("val", "valid", "test", "dev", "test-dev", "test-std")

# Sections whose prose never states a result, so they are not searched for numbers.
_SKIP_SECTIONS = (
    "method",
    "approach",
    "architecture",
    "implementation",
    "related work",
    "related",
    "introduction",
    "background",
    "preliminar",
    "limitation",
    "conclusion",
    "discussion",
    "references",
    "appendix",
    "acknowledg",
    "supplementary material",
)


def _claim_text(doc: PaperDoc) -> list[tuple[str, str]]:
    """(heading, body) pairs worth searching for numeric claims."""
    pairs: list[tuple[str, str]] = []
    for heading, body in doc.sections.items():
        low = heading.lower()
        if any(key in low for key in _SKIP_SECTIONS):
            continue
        if body.strip():
            pairs.append((heading, body))
    if not pairs and doc.text.strip():
        pairs.append(("Body", doc.text))
    return pairs


def _all_aliases() -> list[str]:
    aliases: set[str] = set()
    for values in METRIC_SYNONYMS.values():
        aliases.update(values)
    # Longest first so "top-1 accuracy" wins over "acc".
    return sorted(aliases, key=len, reverse=True)


_ALIASES = _all_aliases()
_ALIAS_ALT = "|".join(re.escape(a) for a in _ALIASES)
_FORWARD = re.compile(
    r"(?P<metric>" + _ALIAS_ALT + r")\s*(?:score|value)?\s*(?:of|is|was|are|were|=|:|reaches|reached|achieves|achieved|attains|attained)\s*(?P<value>-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_BACKWARD = re.compile(
    r"(?P<value>-?\d+(?:\.\d+)?)\s*(?:%|percent|points?)?\s*(?P<metric>" + _ALIAS_ALT + r")\b",
    re.IGNORECASE,
)


def _row_role(label: str) -> str:
    return "paper" if _OURS.search(label) else "reference"


def _dataset_from(header: str, caption: str, row_value: str) -> str:
    for candidate in (row_value, header, caption):
        found = dataset_canonical(candidate)
        if found:
            return found
    return ""


def _claims_from_table(table: PaperTable, start: int) -> list[Claim]:
    header = table.header
    if not header:
        return []
    metric_cols: list[tuple[int, str]] = []
    dataset_col = -1
    for idx, name in enumerate(header):
        low = norm(name)
        if any(low.startswith(h) for h in _DATASET_HEADERS):
            dataset_col = idx
            continue
        canon = metric_canonical(name)
        if canon:
            metric_cols.append((idx, canon))
    if not metric_cols:
        return []

    label_col = 0 if not any(idx == 0 for idx, _ in metric_cols) else -1
    claims: list[Claim] = []
    for row in table.rows:
        if not row:
            continue
        label = row[label_col].strip() if label_col >= 0 and label_col < len(row) else ""
        for idx, canon in metric_cols:
            if idx >= len(row):
                continue
            value = row[idx].strip()
            # Strip confidence intervals such as "72.3 ± 0.4" but keep the mean.
            value = re.split(r"[±\u00b1]", value)[0].strip()
            value = value.replace("%", "").strip()
            if not is_number(value):
                continue
            dataset = ""
            if dataset_col >= 0 and dataset_col < len(row):
                dataset = _dataset_from(header[dataset_col], table.caption, row[dataset_col])
            if not dataset:
                dataset = _dataset_from(header[idx], table.caption, "")
            split = ""
            for hint in _SPLIT_HINTS:
                if hint in norm(header[idx]) or hint in norm(table.caption):
                    split = hint
                    break
            claims.append(
                Claim(
                    id=f"T{start + len(claims) + 1:02d}",
                    metric=canon,
                    raw_metric=header[idx],
                    value=value,
                    row_label=label,
                    dataset=dataset,
                    split=split,
                    role=_row_role(label),
                    evidence=[
                        Evidence(
                            kind="paper",
                            ref=f"{table.id} / row '{label or '?'}' / column '{header[idx]}'",
                            text=f"{label or '?'}: {header[idx]} = {value}",
                            detail=table.caption,
                        )
                    ],
                )
            )
    return claims


def _claims_from_text(doc: PaperDoc, start: int) -> list[Claim]:
    claims: list[Claim] = []
    for heading, body in _claim_text(doc):
        for sentence in split_sentences(body):
            if len(sentence) > 600:
                continue
            numbers = re.findall(r"-?\d+(?:\.\d+)?", sentence)
            if len(numbers) != 1 or len(sentence) < 25:
                continue
            match = _FORWARD.search(sentence) or _BACKWARD.search(sentence)
            if not match:
                continue
            canon = metric_canonical(match.group("metric"))
            if not canon:
                continue
            value = match.group("value")
            if not is_number(value):
                continue
            dataset = dataset_canonical(sentence) or ""
            claims.append(
                Claim(
                    id=f"S{start + len(claims) + 1:02d}",
                    metric=canon,
                    raw_metric=match.group("metric"),
                    value=value,
                    row_label="(in-text)",
                    dataset=dataset,
                    role="paper",
                    notes="Extracted from prose, not from a table; verify the surrounding protocol.",
                    evidence=[
                        Evidence(
                            kind="paper",
                            ref=f"{heading} (prose)",
                            text=sentence.strip()[:280],
                        )
                    ],
                )
            )
    return claims


def _renumber(claims: list[Claim]) -> list[Claim]:
    ordered = sorted(claims, key=lambda c: (c.role != "paper", c.metric, c.value))
    for idx, claim in enumerate(ordered, start=1):
        claim.id = f"C{idx:02d}"
    return ordered


def extract_claims(doc: PaperDoc) -> list[Claim]:
    """Build the claim ledger for a paper, table claims first."""
    claims: list[Claim] = []
    for table in doc.tables:
        claims.extend(_claims_from_table(table, len(claims)))
    claims.extend(_claims_from_text(doc, len(claims)))

    # De-duplicate on (metric, value, dataset).
    seen: set[tuple[str, str, str]] = set()
    unique: list[Claim] = []
    for claim in claims:
        key = (claim.metric, claim.value, claim.dataset)
        if key in seen:
            continue
        seen.add(key)
        unique.append(claim)

    if not any(c.role == "paper" for c in unique):
        # No row was marked "ours"; assume the table's own numbers are the claim.
        for claim in unique:
            claim.role = "paper"
            claim.row_label = claim.row_label or "(paper)"

    unique = unique[:MAX_CLAIMS]
    return _renumber(unique)
