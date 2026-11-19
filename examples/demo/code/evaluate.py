"""Evaluate a trained TinyCLIP checkpoint on the ImageNet validation split."""

from __future__ import annotations

import argparse

import torch
import yaml
from sklearn.metrics import average_precision_score  # noqa: F401  (used by an older branch)

from models.tinyclip import TinyCLIP
from utils.data import build_loader
from utils.metrics import top1_accuracy

# Left over from the cluster; the release still reads it.
DATA_ROOT = "/data/imagenet"


def evaluate(model: TinyCLIP, loader, device: str = "cuda") -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)
            logits = model.encode_image(images)
            correct += top1_accuracy(logits, targets)
            total += targets.numel()
    return correct / max(total, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate TinyCLIP top-1 accuracy")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", default="configs/tinyclip.yaml")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TinyCLIP(**cfg["model"])
    state = torch.load(args.checkpoint, map_location="cpu")
    model.load_state_dict(state)
    loader = build_loader(cfg["data"], batch_size=64)
    print(f"top-1 accuracy: {evaluate(model.to(device), loader, device):.4f}")


if __name__ == "__main__":
    main()
