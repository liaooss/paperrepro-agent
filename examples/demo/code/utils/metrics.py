"""Metric implementations used by the evaluation script."""

from __future__ import annotations

import torch


def top1_accuracy(logits: torch.Tensor, targets: torch.Tensor) -> int:
    """Number of samples whose highest-scoring class is the target class."""
    preds = logits.argmax(dim=-1)
    return int((preds == targets).sum().item())


def top5_accuracy(logits: torch.Tensor, targets: torch.Tensor) -> int:
    _, preds = logits.topk(5, dim=-1)
    return int((preds == targets.unsqueeze(-1)).any(dim=-1).sum().item())
