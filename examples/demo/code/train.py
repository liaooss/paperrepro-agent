"""TinyCLIP training script."""

from __future__ import annotations

import argparse
import random

import numpy as np
import torch
import yaml

from models.tinyclip import TinyCLIP
from utils.data import build_loader


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train TinyCLIP")
    parser.add_argument("--config", default="configs/tinyclip.yaml")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TinyCLIP(**cfg["model"]).to(device)
    loader = build_loader(cfg["data"], batch_size=cfg["train"]["batch_size"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg["train"]["lr"])

    for epoch in range(cfg["train"]["epochs"]):
        model.train()
        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)
            loss = model(images, targets)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        print(f"epoch {epoch} loss {loss.item():.4f}")


if __name__ == "__main__":
    main()
