# Reproducibility assessment — TinyCLIP: Efficient Contrastive Pretraining at Small Scale

> **Verdict: R2 — reproducible after engineering work**  
> Confidence: 0.41 · claims examined: 3 (+2 baseline numbers)

Verdict R2 (reproducible after engineering work): 3 quantitative claim(s) from the paper were checked against the code. 4 major issue(s) remain, starting with RC02 dependencies are not version-pinned. 3 claim(s) still need execution before any number can be called reproduced.

| | |
|---|---|
| Paper | `examples\demo\paper.md` (markdown, 1 table(s)) |
| Repository | `E:\Projects\new-project\examples\demo\code` — 10 files, python:7, docs:1, text:1, config:1 |
| Generated | 2026-11-19T04:22:29+00:00 |
| Tool | reprocheck 0.1.0 · rules-only (no LLM) |

## Why this verdict

- 3 of 3 claim(s) still lack executable evidence, but no asset was found that only the authors could supply. 1 claim(s) have no counterpart in the code at all.
- 1 claim(s) have strong static evidence (implementation and inputs found, nothing executed).
- 1 claim(s) rest on name-level matches only.
- 1 claim(s) could not be matched to any code, dataset or number.
- Smoke check ran: all Python files compile and an entry point exists.

## Claim ledger

| ID | Claim | Reported | Dataset | Evidence | Strongest code evidence |
|----|-------|----------|---------|----------|-------------------------|
| C01 | ImageNet Top-1 | 72.3 | imagenet | E2 | `utils/metrics.py:8` |
| C02 | mAP | 0.41 | coco | X | `—` |
| C03 | Zero-shot ImageNet | 45.1 | imagenet | E3 | `evaluate.py:1` |
| C04 | ImageNet Top-1 _(baseline)_ | 68.3 | imagenet | E2 | `utils/metrics.py:8` |
| C05 | Zero-shot ImageNet _(baseline)_ | 43.3 | imagenet | E3 | `evaluate.py:1` |

## Claim detail

### C01 · ImageNet Top-1 = 72.3 · `E2`

- **Paper:** `Table 1 / row 'TinyCLIP (ours)' / column 'ImageNet Top-1'` — "TinyCLIP (ours): ImageNet Top-1 = 72.3"
- **Code:**
  - `utils/metrics.py:8` — `def top1_accuracy(logits: torch.Tensor, targets: torch.Tensor) -> int:`
  - `evaluate.py:1` — `"""Evaluate a trained TinyCLIP checkpoint on the ImageNet validation split."""`
  - `utils/data.py:1` — `"""ImageNet dataloader."""`
- **Gaps:**
  - the reported value 72.3 appears nowhere in the code or result files

### C02 · mAP = 0.41 · `X`

- **Paper:** `4.2 Detection transfer (prose)` — "On the detection task we reach 0.41 mAP on COCO."
- **Code:** nothing found
- **Gaps:**
  - no implementation of metric 'map' was found in the repository
  - dataset 'coco' is never referenced in the repository
  - the reported value 0.41 appears nowhere in the code or result files
- **Note:** Extracted from prose, not from a table; verify the surrounding protocol.

### C03 · Zero-shot ImageNet = 45.1 · `E3`

- **Paper:** `Table 1 / row 'TinyCLIP (ours)' / column 'Zero-shot ImageNet'` — "TinyCLIP (ours): Zero-shot ImageNet = 45.1"
- **Code:**
  - `evaluate.py:1` — `"""Evaluate a trained TinyCLIP checkpoint on the ImageNet validation split."""`
  - `utils/data.py:1` — `"""ImageNet dataloader."""`
- **Gaps:**
  - no implementation of metric 'zero_shot_accuracy' was found in the repository
  - the reported value 45.1 appears nowhere in the code or result files

### C04 · ImageNet Top-1 = 68.3 · `E2`

- **Paper:** `Table 1 / row 'CLIP-B/32' / column 'ImageNet Top-1'` — "CLIP-B/32: ImageNet Top-1 = 68.3"
- **Code:**
  - `utils/metrics.py:8` — `def top1_accuracy(logits: torch.Tensor, targets: torch.Tensor) -> int:`
  - `evaluate.py:1` — `"""Evaluate a trained TinyCLIP checkpoint on the ImageNet validation split."""`
  - `utils/data.py:1` — `"""ImageNet dataloader."""`
- **Gaps:**
  - the reported value 68.3 appears nowhere in the code or result files

### C05 · Zero-shot ImageNet = 43.3 · `E3`

- **Paper:** `Table 1 / row 'CLIP-B/32' / column 'Zero-shot ImageNet'` — "CLIP-B/32: Zero-shot ImageNet = 43.3"
- **Code:**
  - `evaluate.py:1` — `"""Evaluate a trained TinyCLIP checkpoint on the ImageNet validation split."""`
  - `utils/data.py:1` — `"""ImageNet dataloader."""`
- **Gaps:**
  - no implementation of metric 'zero_shot_accuracy' was found in the repository
  - the reported value 43.3 appears nowhere in the code or result files

## Risk findings

### Major issues (4)

#### RC02 · Dependencies are not version-pinned

4 requirement(s) carry no version constraint, so a fresh install can resolve to versions the authors never tested. Example: torch
- `requirements.txt` — `torch`
- `requirements.txt` — `numpy`
- `requirements.txt` — `pyyaml`
- `requirements.txt` — `tqdm`

#### RC03 · Absolute filesystem paths in source

2 hard-coded path(s) such as '/data/imagenet' point at the authors' machine. Any other checkout has to be patched before it runs.
- `evaluate.py:16` — `DATA_ROOT = "/data/imagenet"`

#### RC13 · Imports not declared in any manifest

1 module(s) are imported but absent from every dependency file (sklearn). A clean environment will fail at import time.
- `evaluate.py:9` — `from sklearn.metrics import average_precision_score  # noqa: F401  (used by an older branch)`

#### RC17 · Paper claims with no code counterpart

1 claim(s) have no implementation, dataset or value in the repository (C02). These results cannot be reproduced from this release.
- `4.2 Detection transfer (prose)` — `mAP`

### Minor issues (1)

#### RC12 · GPU requirement undocumented

The code moves tensors to CUDA but no GPU model, memory size or driver version is stated, so the compute budget of a reproduction is unbounded.
- `repository-wide scan`

### Notes (2)

#### RC10 · No tests

Nothing verifies the implementation against known-good behaviour, so a silent bug in the pipeline looks exactly like a reproduction failure.
- `repository-wide scan`

#### RC15 · No licence file

Without an explicit licence the code is all-rights-reserved by default, which blocks reuse and redistribution even when it runs.
- `repository root`

## What to do next

1. [RC02] Dependencies are not version-pinned — requirements.txt
2. [RC03] Absolute filesystem paths in source — evaluate.py:16
3. [RC13] Imports not declared in any manifest — evaluate.py:9
4. [RC17] Paper claims with no code counterpart — 4.2 Detection transfer (prose)
5. [C02] Find or implement 'mAP' for coco (paper reports 0.41).

## Reproduce this assessment

```bash
reprocheck assess examples\demo\paper.md --repo E:\Projects\new-project\examples\demo\code --smoke
```

## Limits of this report

- The analysis is static: no dependency was installed, no dataset downloaded, no model trained. E1 requires `--smoke`; without it the ceiling is E2.
- Claim extraction reads tables and results prose. A number stated only in a figure is invisible to it.
- A reproduced number can still differ for statistical reasons (seeds, hardware); this report judges whether the *evidence to attempt* a reproduction exists, not whether a re-run will land within 0.1.
