# Reproduction run — distilbert-sst2

> **the run produced metrics but no claim from the paper could be compared**  
> Recommendation: **usable with conditions** · viability 3.0/5

## What was run

| | |
|---|---|
| Paper | `E:\Projects\new-project\.scratch\case-a\out4\paper\paper.html` |
| Repository | `.scratch\case-a\out3\repo` @ `90cbc670be7f` |
| Backend | local |
| Commands | 4 (failed: 0) |
| Wall clock | 1.3 min |
| Local disk | 1.1 GB |
| Recipe source | curated |
| Level | L2 evaluation (released weights, no training) |

## Evidence

- `accuracy: 0.9106`
- from `E:\Projects\new-project\.scratch\case-a\out4\artifacts\99-eval.log`

## Command log

| # | Command | Exit | Time | Log |
|---|---------|------|------|-----|
| 1 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" .reprocheck-harness/prepare_data` | 0 | 0s | 01-data.log |
| 2 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" -m pip install torch --index-url` | 0 | 3s | 01-install.log |
| 3 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" -m pip install -e .` | 0 | 13s | 02-install.log |
| 4 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.reprocheck-venv\Scripts\python.exe" .reprocheck-harness/eval_sst2.py` | 0 | 61s | 99-eval.log |

## Viability

| Dimension | Score | Note |
|-----------|-------|------|
| executability | 5.0/5 | run status ok |
| fidelity | 0.0/5 | no claim could be compared |
| cost | 5.0/5 | 1 min, 1.1 GB on disk |
| comparability | 1.5/5 | protocol must be checked by hand: split, preprocessing and metric definition |
| openness | 3.5/5 | licence present |

**Overall 3.0/5 → usable with conditions.**

Blockers:

- no measured value to compare against the paper

## Limits of this run

- One environment, one seed, one machine. A match here is evidence, not proof.
- The comparison covers only claims whose metric the run actually printed.
- Protocol differences (split, preprocessing, metric definition) are not detected automatically; check them before quoting these numbers in a paper.
