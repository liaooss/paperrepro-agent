"""Small text helpers shared by the paper and code analysers."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

# Canonical metric name -> the spellings that may appear in a paper header or in
# source code. Aliases shorter than four characters are matched on word
# boundaries so that "acc" does not fire on "accept".
METRIC_SYNONYMS: dict[str, tuple[str, ...]] = {
    "accuracy": ("accuracy", "acc", "top-1", "top1", "top 1", "top-1 accuracy"),
    "top5_accuracy": ("top-5", "top5", "top 5", "top-5 accuracy"),
    "zero_shot_accuracy": ("zero-shot", "zero shot", "zeroshot", "zs-acc"),
    "f1": ("f1", "f1-score", "f1 score", "f1score", "macro-f1", "micro-f1"),
    "bleu": ("bleu", "sacrebleu", "bleu-4", "bleu4"),
    "rouge": ("rouge", "rouge-l", "rouge-1", "rouge-lsum"),
    "meteor": ("meteor",),
    "wer": ("wer", "word error rate"),
    "cer": ("cer", "character error rate"),
    "psnr": ("psnr",),
    "ssim": ("ssim",),
    "lpips": ("lpips",),
    "fid": ("fid",),
    "auc": ("auc", "auroc", "roc-auc", "roc auc"),
    "auprc": ("auprc", "average precision", "ap"),
    "map": ("map", "map@50", "map@75", "mAP"),
    "precision": ("precision",),
    "recall": ("recall",),
    "perplexity": ("perplexity", "ppl", "ptb perplexity"),
    "wer_wer": ("wer",),
    "ndcg": ("ndcg", "ndcg@10"),
    "mrr": ("mrr",),
    "em": ("exact match", "em", "exact-match"),
    "pass@1": ("pass@1", "pass@k"),
    "success_rate": ("success rate", "success-rate"),
    "return": ("episode return", "average return", "mean return"),
    "iou": ("iou", "miou", "mean iou", "jaccard"),
    "dice": ("dice", "dice score", "dice coefficient"),
}

# Headers that look like metrics but are properties of the model, not results.
NON_METRIC_HEADERS: tuple[str, ...] = (
    "param",
    "params",
    "#param",
    "flops",
    "gflops",
    "tflops",
    "size",
    "latency",
    "throughput",
    "time",
    "memory",
    "speedup",
    "epoch",
    "steps",
    "cost",
)

DATASET_SYNONYMS: dict[str, tuple[str, ...]] = {
    "imagenet": ("imagenet", "imagenet-1k", "imagenet1k", "ilsvrc"),
    "imagenet-c": ("imagenet-c", "imagenet-r", "imagenet-a"),
    "cifar10": ("cifar-10", "cifar10"),
    "cifar100": ("cifar-100", "cifar100"),
    "mnist": ("mnist",),
    "coco": ("coco", "mscoco", "ms-coco"),
    "sst2": ("sst-2", "sst2"),
    "glue": ("glue", "superglue"),
    "squad": ("squad", "squad2.0", "squad 2.0"),
    "wmt14": ("wmt14", "wmt-14"),
    "wmt16": ("wmt16",),
    "iwslt": ("iwslt", "iwslt14"),
    "librispeech": ("librispeech", "libri-speech"),
    "cityscapes": ("cityscapes",),
    "ade20k": ("ade20k", "ade-20k"),
    "celeba": ("celeba", "celeba-hq"),
    "genimage": ("genimage",),
    "msrvtt": ("msrvtt", "msr-vtt"),
    "kinetics400": ("kinetics-400", "kinetics400"),
    "openwebtext": ("openwebtext", "open-webtext"),
    "the_pile": ("the pile", "the-pile"),
    "laion": ("laion",),
    "vqa": ("vqa", "vqa2", "vqav2"),
}

_ALIAS_TO_METRIC: dict[str, str] = {}
for _canon, _aliases in METRIC_SYNONYMS.items():
    for _a in _aliases:
        _ALIAS_TO_METRIC.setdefault(_a.lower(), _canon)

_ALIAS_TO_DATASET: dict[str, str] = {}
for _canon, _aliases in DATASET_SYNONYMS.items():
    for _a in _aliases:
        _ALIAS_TO_DATASET.setdefault(_a.lower(), _canon)


def norm(text: str) -> str:
    """Lower-case and collapse whitespace, keeping the punctuation that matters."""
    return re.sub(r"\s+", " ", text or "").strip().lower()


def norm_key(text: str) -> str:
    """Strip everything that is not alphanumeric, for loose comparisons."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def metric_canonical(header: str) -> str | None:
    """Map a table header or config key to a canonical metric name, if any."""
    low = norm(header)
    if not low:
        return None
    for non in NON_METRIC_HEADERS:
        if low == non or low.startswith(non + " ") or low.startswith(non + "("):
            return None
    key = norm_key(low)
    if not key:
        return None
    best: tuple[int, int, str] | None = None
    for alias, canon in _ALIAS_TO_METRIC.items():
        akey = norm_key(alias)
        if not akey:
            continue
        if akey == key:
            return canon
        if len(akey) >= 3 and akey in key:
            # The alias that starts earliest wins, so "Top-5 Accuracy" is
            # top-5 and not plain accuracy; ties go to the longer alias.
            cand = (key.find(akey), -len(akey), canon)
            if best is None or cand < best:
                best = cand
    return best[2] if best else None


def dataset_canonical(text: str) -> str | None:
    low = norm(text)
    if not low:
        return None
    key = norm_key(low)
    best: tuple[int, str] | None = None
    for alias, canon in _ALIAS_TO_DATASET.items():
        akey = norm_key(alias)
        if not akey:
            continue
        if akey == key:
            return canon
        if len(akey) >= 4 and akey in key:
            cand = (len(akey), canon)
            if best is None or cand[0] > best[0]:
                best = cand
    return best[1] if best else None


def aliases_for(metric: str) -> tuple[str, ...]:
    return METRIC_SYNONYMS.get(metric, (metric,))


_ALIAS_PATTERNS: dict[str, "re.Pattern[str]"] = {}


def _alias_pattern(alias: str) -> "re.Pattern[str]":
    """Compiled once per alias.

    Scanning a monorepo means hundreds of thousands of searches; recompiling the
    same expression each time turns a two-second scan into a ten-minute one.
    """
    pattern = _ALIAS_PATTERNS.get(alias)
    if pattern is None:
        escaped = re.escape(alias)
        if len(alias) <= 3:
            escaped = r"(?<![A-Za-z0-9_])" + escaped + r"(?![A-Za-z0-9_])"
        pattern = re.compile(escaped, re.IGNORECASE)
        _ALIAS_PATTERNS[alias] = pattern
    return pattern


def find_alias(text: str, alias: str) -> int:
    """Return the offset of an alias inside text, or -1.

    Short aliases are matched on word boundaries; long ones as plain
    case-insensitive substrings, which is what source code usually needs.
    """
    if not text or not alias:
        return -1
    match = _alias_pattern(alias).search(text)
    return match.start() if match else -1


def line_of(text: str, offset: int) -> int:
    """1-based line number of an offset inside text."""
    if offset <= 0:
        return 1
    return text.count("\n", 0, offset) + 1


def snippet(text: str, offset: int, width: int = 90) -> str:
    """A single-line excerpt around an offset, with ellipses."""
    if offset < 0 or not text:
        return ""
    start = max(0, offset - width // 3)
    end = min(len(text), offset + width)
    chunk = text[start:end].replace("\n", " ")
    chunk = re.sub(r"\s+", " ", chunk).strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{chunk}{suffix}"


def is_number(text: str) -> bool:
    t = (text or "").strip().replace(",", "")
    if t.endswith("%"):
        t = t[:-1].strip()
    # "72.3±0.4" is a mean and an interval, not a single reported value.
    if any(ch in t for ch in "±~<>≈"):
        return False
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", t))


def numbers_in(text: str) -> list[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", text or "")


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm_key(a), norm_key(b)).ratio()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text or "")
    return [p.strip() for p in parts if p.strip()]


def human_list(items: list[str], limit: int = 3) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) <= limit:
        return ", ".join(items)
    return ", ".join(items[:limit]) + f" (+{len(items) - limit} more)"
