# The rubric

This document is normative: the code implements it, the tests pin it, and a disagreement with a verdict should be argued here rather than in a comment.

## 1. Evidence levels (per claim)

A claim is one row of the ledger: a metric, a value, and the setting it was measured in. Each claim gets exactly one level.

| Level | Name | Requires |
|---|---|---|
| **E1** | executable evidence | metric implementation + dataset (when the claim names one) + the literal value somewhere in the repo + a passing `--smoke` |
| **E2** | strong static evidence | metric implementation **and** (dataset reference **or** literal value) |
| **E3** | weak static evidence | at least one of {metric, dataset, literal value}; the link is name-level only |
| **X** | no correspondence | none of the three |

Two adjustments apply:

1. If the claim names a dataset and the repository never mentions it, the level is capped at **E3**. A metric in isolation does not reproduce a number measured on a dataset you cannot load.
2. A literal value is only searched for when it has at least three characters and is not a trivially common constant (`0.0`, `1.0`, `100.0`).

"Metric implementation" means a `def`/`class` whose name contains a known alias of the metric, preferring such a definition anywhere in the repository over an import or a docstring mention.

## 2. Verdict (per paper/release pair)

Let `n` be the number of claims with `role="paper"`, and `X, E3, E2, E1` the counts per level. Baseline rows (`role="reference"`) never affect the verdict.

```
if every claim is E1                          -> R3
elif X / n > 0.5                              -> R0
elif at least one author-dependent blocker    -> R1
else                                          -> R2
```

Order matters. R0 is checked before R1 because "the code does not implement the result" is a stronger statement than "an asset is missing": more data will not fix a missing implementation.

`n = 0` is not a verdict about reproducibility. It returns **R1** with confidence ≤ 0.3 and an explicit statement that nothing could be anchored.

### Author-dependent blockers

Only two rules are author-dependent, because only they describe artifacts a reader cannot obtain:

- **RC04** — a checkpoint path is referenced but the file is not in the repository;
- **RC05** — the README routes the reader to a form, email, registration, or a cloud drive that may be revoked.

Every other rule — unpinned dependencies, absolute paths, missing config, undeclared imports — is engineering work, so it yields R2.

## 3. Confidence

```
confidence = mean(level_score[claim]) × penalty
level_score = {E1: 0.95, E2: 0.78, E3: 0.45, X: 0.08}
penalty = 1.0
penalty *= 0.85                                  # no --smoke: nothing was executed
penalty *= 1 - 0.15 × (X / n)                    # unmatched claims reduce certainty
confidence = clamp(confidence, 0.05, 0.95)
```

Confidence is a *reporting* device: it ranks how much evidence backs a verdict, and it is deliberately never 1.0. It is not a calibrated probability, and the report says so.

## 4. Rule catalogue

| ID | Severity | Fires when | Author-dependent |
|---|---|---|---|
| RC01 | major | no `requirements.txt` / `pyproject.toml` / `environment.yml` / `Dockerfile` | no |
| RC02 | major | a requirement line has no version specifier | no |
| RC03 | major | a string literal looks like `/home/...`, `/data/...`, `C:\...` | no |
| RC04 | blocker | `*.pt/.pth/.ckpt/.bin/.safetensors` referenced and absent | **yes** |
| RC05 | blocker | README mentions a form, email request, Google Drive, Baidu Pan, OneDrive, Dropbox | **yes** |
| RC06 | minor | no seed/`manual_seed`/`--seed` anywhere | no |
| RC07 | major | no `__main__` guard, CLI parser, or conventional entry script | no |
| RC08 | minor | README has no `pip install` / `conda install` / `make` / `bash *.sh` | no |
| RC09 | minor | no YAML/JSON/TOML config or hparams module | no |
| RC10 | info | no test file | no |
| RC11 | minor | `TODO`/`FIXME`/`NotImplementedError` present | no |
| RC12 | minor | CUDA is used but the README never mentions GPU hardware | no |
| RC13 | major | a top-level import is neither stdlib, local, nor declared in a manifest | no |
| RC14 | major | notebooks exist and no Python file does | no |
| RC15 | info | no `LICENSE`/`LICENCE`/`COPYING` file | no |
| RC16 | major | no README | no |
| RC17 | major | at least one claim reached level X | no |

### Known false positives

- **RC13** with optional imports guarded by `try: import x except ImportError:`. The release still works, but the dependency is genuinely undeclared, so the finding stays.
- **RC03** on documentation examples such as `python train.py /data/my-set`. Mitigation: fix the release, not the rule.
- **RC06** on repositories that seed inside a launcher that is not in the repository.

## 5. Worked example

`examples/demo` ships a paper with three paper claims and a release with a real gap.

| Claim | Evidence found | Level |
|---|---|---|
| ImageNet top-1 = 72.3 | `utils/metrics.py` defines `top1_accuracy`; `utils/data.py` mentions ImageNet; 72.3 appears nowhere | **E2** |
| Zero-shot ImageNet = 45.1 | ImageNet found, no zero-shot implementation | **E3** |
| COCO mAP = 0.41 | no mAP code, no COCO reference, 0.41 absent | **X** |

Counts: `n=3, E2=1, E3=1, X=1`. `X/n = 0.33` is not above 0.5, so not R0. The release has no missing checkpoint and no restricted data, so not R1. **R2**, with RC17 flagging the unmatched claim.

Confidence: `(0.78 + 0.45 + 0.08)/3 = 0.437`; `--smoke` passed so no penalty; `X` penalty `1 − 0.15/3 = 0.95`; result `0.415 → 0.41`. That matches the report.

## 6. Arguing with a verdict

Every verdict is falsifiable by pointing at evidence:

1. Open `scorecard.json`. Each claim lists `code_evidence` and `gaps`.
2. If a gap is wrong ("we do implement zero-shot"), the fix is a text pattern in `textutil.py` or a rule in `matcher.py`, plus a regression test.
3. If the verdict is wrong but every level is right, the disagreement is in section 2 — change this document and `decide()` together.
4. If a rule misfires, reproduce it with the smallest repository that triggers it and add it under `tests/`.
