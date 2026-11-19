# Reproduction run — distilbert-sst2

> **the run did not complete: DATA_UNAVAILABLE**  
> Recommendation: **do not use as a baseline yet** · viability 2.2/5

## What was run

| | |
|---|---|
| Paper | `E:\Projects\new-project\.scratch\case-a\out3\paper\paper.html` |
| Repository | `E:\Projects\new-project\.scratch\case-a\out3\repo` @ `90cbc670be7f` |
| Backend | local |
| Commands | 4 (failed: 1) |
| Wall clock | 3.9 min |
| Local disk | 0.9 GB |
| Recipe source | curated |
| Level | L2 evaluation (released weights, no training) |

## Why it failed

- **Kind:** `DATA_UNAVAILABLE`
- **Evidence:** PermissionError: [WinError 5] 拒绝访问。: 'C:\\Users\\l\\.cache\\huggingface\\hub\\models--distilbert-base-uncased-finetuned-sst-2-english'

Failure kinds map to different remedies:

- `MISSING_WEIGHTS` / `DATA_UNAVAILABLE` — only the authors can fix this; ask them.
- `ENV_CONFLICT` — try `--backend docker` or pin the versions the release expects.
- `OOM` — reduce batch size or resolution; the claim may still be checkable.
- `TIMEOUT` — raise `--limit-minutes` or reduce the evaluation split.

## Command log

| # | Command | Exit | Time | Log |
|---|---------|------|------|-----|
| 1 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" .reprocheck-harness/prepare_data` | 0 | 8s | 01-data.log |
| 2 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" -m pip install torch --index-url` | 0 | 124s | 01-install.log |
| 3 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" -m pip install -e .` | 0 | 83s | 02-install.log |
| 4 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" .reprocheck-harness/eval_sst2.py` | 1 | 10s | 99-eval.log |

## Viability

| Dimension | Score | Note |
|-----------|-------|------|
| executability | 1.0/5 | run status failed (DATA_UNAVAILABLE) |
| fidelity | 0.0/5 | no claim could be compared |
| cost | 5.0/5 | 4 min, 0.9 GB on disk |
| comparability | 1.5/5 | protocol must be checked by hand: split, preprocessing and metric definition |
| openness | 3.5/5 | licence present |

**Overall 2.2/5 → do not use as a baseline yet.**

Blockers:

- DATA_UNAVAILABLE: PermissionError: [WinError 5] 拒绝访问。: 'C:\\Users\\l\\.cache\\huggingface\\hub\\models--distilbert-base-uncased-finetuned-sst-2-english'
- no measured value to compare against the paper

## Limits of this run

- One environment, one seed, one machine. A match here is evidence, not proof.
- The comparison covers only claims whose metric the run actually printed.
- Protocol differences (split, preprocessing, metric definition) are not detected automatically; check them before quoting these numbers in a paper.
