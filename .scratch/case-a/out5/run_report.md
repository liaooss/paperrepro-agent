# Reproduction run — distilbert-sst2

> **1/1 claim(s) match (tolerance 0.5 points)**  
> Recommendation: **use as a baseline** · viability 4.3/5

## Claim comparison

| Claim | Metric | Paper | Measured | Delta (points) | Status |
|-------|--------|-------|----------|----------------|--------|
| T01 | SST-2 accuracy (GLUE dev) | 91.3 | 91.06 | -0.24 | match |

## What was run

| | |
|---|---|
| Paper | `E:\Projects\new-project\.scratch\case-a\out5\paper\paper.html` |
| Repository | `.scratch\case-a\out3\repo` @ `90cbc670be7f` |
| Backend | local |
| Commands | 4 (failed: 0) |
| Wall clock | 0.8 min |
| Local disk | 1.1 GB |
| Recipe source | curated |
| Level | L2 evaluation (released weights, no training) |

## Evidence

- `accuracy: 0.9106`
- from `E:\Projects\new-project\.scratch\case-a\out5\artifacts\99-eval.log`

## Command log

| # | Command | Exit | Time | Log |
|---|---------|------|------|-----|
| 1 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" .reprocheck-harness/prepare_data` | 0 | 0s | 01-data.log |
| 2 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" -m pip install torch --index-url` | 0 | 3s | 01-install.log |
| 3 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" -m pip install -e .` | 0 | 13s | 02-install.log |
| 4 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" .reprocheck-harness/eval_sst2.py` | 0 | 31s | 99-eval.log |

## Viability

| Dimension | Score | Note |
|-----------|-------|------|
| executability | 5.0/5 | run status ok |
| fidelity | 5.0/5 | 1/1 claims match |
| cost | 5.0/5 | 1 min, 1.1 GB on disk |
| comparability | 3.0/5 | protocol must be checked by hand: split, preprocessing and metric definition |
| openness | 3.5/5 | licence present |

**Overall 4.3/5 → use as a baseline.**

## Limits of this run

- One environment, one seed, one machine. A match here is evidence, not proof.
- The comparison covers only claims whose metric the run actually printed.
- Protocol differences (split, preprocessing, metric definition) are not detected automatically; check them before quoting these numbers in a paper.
