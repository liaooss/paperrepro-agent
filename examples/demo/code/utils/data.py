"""ImageNet dataloader."""

from __future__ import annotations

from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset

IMAGENET_ROOT = Path("/data/imagenet")


class ImageNetSubset(Dataset):
    """Placeholder loader; the real one lives on the authors' cluster."""

    def __init__(self, root: Path, split: str = "val") -> None:
        self.root = root
        self.split = split

    def __len__(self) -> int:
        return 0

    def __getitem__(self, index: int):  # pragma: no cover - data not released
        raise NotImplementedError("ImageNet loader is not part of this release")


def build_loader(cfg: dict, batch_size: int = 64) -> DataLoader:
    dataset = ImageNetSubset(Path(cfg.get("root", IMAGENET_ROOT)), split="val")
    return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=8)
