# Reproduction run — distilbert-sst2-seeds

> **Status: REPRODUCED** — reproduced.  
> all 1 compared claim(s) match within tolerance  
> Recommendation: **use as a baseline** · viability 4.3/5

Claims compared: MATCH:1 (tolerance 0.5 points).

## Claim comparison

| Claim | Metric | Paper | Measured | Delta (points) | Status |
|-------|--------|-------|----------|----------------|--------|
| T01 | SST-2 accuracy (GLUE dev) | 91.3 | 91.06 | -0.24 | match |

## Stability across seeds

| Metric | Mean | Std | Runs | Per-seed |
|--------|------|-----|------|----------|
| accuracy | 0.9106 | 0.0000 | 3/3 | 1:0.9106, 2:0.9106, 3:0.9106 |

The spread is small relative to the tolerance, so the comparison is stable across seeds.

## Consistency audit — paper versus code

No comparable configuration was found: the repository has no config file or config-like module that states these hyperparameters, so the paper's settings cannot be attributed to this code with evidence.

## What was run

| | |
|---|---|
| Paper | `E:\Projects\new-project\.scratch\case-a\seeds\paper\paper.html` |
| Repository | `.scratch\case-a\out3\repo` |
| Backend | local |
| Commands | 12 (failed: 0) |
| Wall clock | 2.0 min |
| Local disk | 1.7 GB |
| Recipe source | curated |
| Level | L2 - released weights, no training |

## Evidence

- `accuracy: 0.9106`
- from `E:\Projects\new-project\.scratch\case-a\seeds\seed-3\artifacts\99-eval.log`

## Command log

| # | Command | Exit | Time | Log |
|---|---------|------|------|-----|
| 1 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/prepare_data` | 0 | 0s | 01-data.log |
| 2 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install torch --index-url` | 0 | 3s | 01-install.log |
| 3 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install -e .` | 0 | 14s | 02-install.log |
| 4 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/eval_sst2.py` | 0 | 28s | 99-eval.log |
| 5 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/prepare_data` | 0 | 0s | 01-data.log |
| 6 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install torch --index-url` | 0 | 2s | 01-install.log |
| 7 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install -e .` | 0 | 12s | 02-install.log |
| 8 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/eval_sst2.py` | 0 | 22s | 99-eval.log |
| 9 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/prepare_data` | 0 | 0s | 01-data.log |
| 10 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install torch --index-url` | 0 | 2s | 01-install.log |
| 11 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install -e .` | 0 | 13s | 02-install.log |
| 12 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/eval_sst2.py` | 0 | 22s | 99-eval.log |

## Plan that was executed

```
plan: distilbert-sst2-seeds (source: curated)
  install 1: {pip} install torch --index-url https://download.pytorch.org/whl/cpu
  install 2: {pip} install -e .
  data    1: {python} {harness}/prepare_data.py --dest data
  eval      : {python} {harness}/eval_sst2.py --data data --model distilbert-base-uncased-finetuned-sst-2-english --seed {seed}
  notes     : L2 evaluation with released weights, repeated under three seeds to measure spread. The evaluation is deterministic, so a zero spread is the expected answer here - and it means the delta is protocol, not sampling noise.
```

## Viability

| Dimension | Score | Note |
|-----------|-------|------|
| executability | 5.0/5 | run status ok |
| fidelity | 5.0/5 | 1/1 claims match |
| cost | 5.0/5 | 2 min, 1.7 GB on disk |
| comparability | 3.0/5 | protocol must be checked by hand: split, preprocessing and metric definition |
| openness | 3.5/5 | licence present |

**Overall 4.3/5 → use as a baseline.**

## Limits of this run

- One environment, one seed, one machine. A match here is evidence, not proof.
- The comparison covers only claims whose metric the run actually printed.
- Protocol differences (split, preprocessing, metric definition) are not detected automatically; check them before quoting these numbers in a paper.
