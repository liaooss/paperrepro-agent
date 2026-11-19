# Reproduction run — distilbert-sst2

> **the run did not complete: COMMAND_FAILED**  
> Recommendation: **do not use as a baseline yet** · viability 2.4/5

## What was run

| | |
|---|---|
| Paper | `E:\Projects\new-project\.scratch\case-a\out\paper\paper.html` |
| Repository | `.scratch\case-a\transformers` |
| Backend | local |
| Commands | 3 (failed: 1) |
| Wall clock | 3.0 min |
| Local disk | 0.7 GB |
| Recipe source | curated |
| Level | L2 evaluation (released weights, no training) |

## Why it failed

- **Kind:** `COMMAND_FAILED`
- **Evidence:** Obtaining file:///E:/Projects/new-project/.scratch/case-a/transformers

ERROR: file:///E:/Projects/new-project/.scratch/case-a/transformers does not appear to be a Python project: neither 'setup.py' nor 'pyproject.toml' found.


Failure kinds map to different remedies:

- `MISSING_WEIGHTS` / `DATA_UNAVAILABLE` — only the authors can fix this; ask them.
- `ENV_CONFLICT` — try `--backend docker` or pin the versions the release expects.
- `OOM` — reduce batch size or resolution; the claim may still be checkable.
- `TIMEOUT` — raise `--limit-minutes` or reduce the evaluation split.

## Command log

| # | Command | Exit | Time | Log |
|---|---------|------|------|-----|
| 1 | `"E:\Projects\new-project\.scratch\case-a\transformers\.reprocheck-venv\Scripts\python.exe" .reprocheck-harness/prepare_d` | 0 | 5s | 01-data.log |
| 2 | `"E:\Projects\new-project\.scratch\case-a\transformers\.reprocheck-venv\Scripts\python.exe" -m pip install torch --index-` | 0 | 164s | 01-install.log |
| 3 | `"E:\Projects\new-project\.scratch\case-a\transformers\.reprocheck-venv\Scripts\python.exe" -m pip install -e .` | 1 | 6s | 02-install.log |

## Viability

| Dimension | Score | Note |
|-----------|-------|------|
| executability | 2.0/5 | run status failed (COMMAND_FAILED) |
| fidelity | 0.0/5 | no claim could be compared |
| cost | 5.0/5 | 3 min, 0.7 GB on disk |
| comparability | 1.5/5 | protocol must be checked by hand: split, preprocessing and metric definition |
| openness | 3.5/5 | no licence file |

**Overall 2.4/5 → do not use as a baseline yet.**

Blockers:

- COMMAND_FAILED: Obtaining file:///E:/Projects/new-project/.scratch/case-a/transformers

ERROR: file:///E:/Projects/new-project/.scratch/case-a/transformers does not appear to be a Python project: neither 'setup.py' nor 'pyproject.toml' found.

- no measured value to compare against the paper

## Limits of this run

- One environment, one seed, one machine. A match here is evidence, not proof.
- The comparison covers only claims whose metric the run actually printed.
- Protocol differences (split, preprocessing, metric definition) are not detected automatically; check them before quoting these numbers in a paper.
