"""Minimal TinyCLIP model definition."""

from __future__ import annotations

import torch
from torch import nn


class TinyCLIP(nn.Module):
    def __init__(self, width: int = 256, depth: int = 6) -> None:
        super().__init__()
        self.visual = nn.Sequential(
            *[nn.TransformerEncoderLayer(d_model=width, nhead=8) for _ in range(depth)]
        )
        self.proj = nn.Linear(width, 512)

    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        tokens = images.flatten(2).transpose(1, 2)
        features = self.visual(tokens)
        return self.proj(features.mean(dim=1))

    def forward(self, images: torch.Tensor, texts: torch.Tensor) -> torch.Tensor:
        image_features = self.encode_image(images)
        text_features = texts.float()
        logits = image_features @ text_features.t()
        labels = torch.arange(logits.size(0), device=logits.device)
        return nn.functional.cross_entropy(logits, labels)
