"""Evaluate a released checkpoint on SST-2 dev and print its accuracy.

This is the "L2" driver: no training, only the authors' weights and the
paper's evaluation split. It prints one machine-readable line so the comparison
is not a human reading numbers off a screen.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def read_dev(path: Path) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            sentence = (row.get("sentence") or "").strip()
            label = (row.get("label") or "").strip()
            if sentence and label in {"0", "1"}:
                rows.append((sentence, int(label)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data")
    parser.add_argument("--model", default="distilbert-base-uncased-finetuned-sst-2-english")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--limit", type=int, default=0, help="evaluate only the first N rows")
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    dev_path = Path(args.data) / "SST-2" / "dev.tsv"
    if not dev_path.exists():
        print(f"missing data: {dev_path}", file=sys.stderr)
        return 2

    rows = read_dev(dev_path)
    if args.limit:
        rows = rows[: args.limit]
    print(f"device: cpu | model: {args.model} | examples: {len(rows)}")

    torch.set_num_threads(min(8, torch.get_num_threads()))
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model)
    model.eval()

    correct = 0
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start : start + args.batch_size]
        sentences = [s for s, _ in batch]
        labels = torch.tensor([y for _, y in batch])
        encoded = tokenizer(
            sentences, truncation=True, padding=True, max_length=128, return_tensors="pt"
        )
        with torch.no_grad():
            logits = model(**encoded).logits
        correct += int((logits.argmax(dim=-1) == labels).sum().item())

    accuracy = correct / max(len(rows), 1)
    print(f"correct: {correct}/{len(rows)}")
    print(f"accuracy: {accuracy:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
