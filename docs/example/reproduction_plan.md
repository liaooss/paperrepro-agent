# Reproduction plan for `TinyCLIP: Efficient Contrastive Pretraining at Small Scale`

Starting verdict: **R2 — reproducible after engineering work**

## 0. Environment

- [ ] Clone the repository at the paper's released commit and record the commit hash.
- [ ] Create a clean virtual environment; install exactly what the manifest pins.
- [ ] Record Python, CUDA, driver and GPU model — they are part of the result.

## 1. Assets

- [ ] No author-supplied asset was detected; confirm data and weights are downloadable.

## 2. Claims to reproduce

- [ ] **C01** ImageNet Top-1 = **72.3** on `imagenet` — current evidence **E2**
  - gap: the reported value 72.3 appears nowhere in the code or result files
- [ ] **C02** mAP = **0.41** on `coco` — current evidence **X**
  - gap: no implementation of metric 'map' was found in the repository
  - gap: dataset 'coco' is never referenced in the repository
  - gap: the reported value 0.41 appears nowhere in the code or result files
- [ ] **C03** Zero-shot ImageNet = **45.1** on `imagenet` — current evidence **E3**
  - gap: no implementation of metric 'zero_shot_accuracy' was found in the repository
  - gap: the reported value 45.1 appears nowhere in the code or result files

## 3. Execution

- [ ] Run the smallest end-to-end command the README advertises, then the evaluation script.
- [ ] Fix every absolute path and rerun; note each edit, because edits are part of the repro.
- [ ] Run with the authors' seed first, then two more seeds to measure variance.

## 4. Comparison

- [ ] Build the table `claim | paper | reproduced | delta | within tolerance?`.
- [ ] Decide tolerance before looking at results (e.g. abs 0.5 for accuracy in points).
- [ ] Report failures as findings, not as silent omissions.

## Open items from the audit

- [ ] [RC02] Dependencies are not version-pinned — requirements.txt
- [ ] [RC03] Absolute filesystem paths in source — evaluate.py:16
- [ ] [RC13] Imports not declared in any manifest — evaluate.py:9
- [ ] [RC17] Paper claims with no code counterpart — 4.2 Detection transfer (prose)
- [ ] [C02] Find or implement 'mAP' for coco (paper reports 0.41).
