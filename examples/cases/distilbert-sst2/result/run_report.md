# Reproduction run — distilbert-sst2

> **Status: REPRODUCED** — reproduced.  
> all 1 compared claim(s) match within tolerance  
> **Recommendation: use as a baseline** — The reported number reproduces within tolerance and the configuration is consistent.

Claims compared: MATCH:1 (tolerance 0.5 points).

## Claim comparison

| Claim | Metric | Paper | Measured | Delta (points) | Status |
|-------|--------|-------|----------|----------------|--------|
| T01 | SST-2 accuracy (GLUE dev) | 91.3 | 91.06 | -0.24 | match |

## Consistency audit — paper versus code

No comparable configuration was found: the repository has no config file or config-like module that states these hyperparameters, so the paper's settings cannot be attributed to this code with evidence.

## What was run

| | |
|---|---|
| Paper | `E:\Projects\new-project\.scratch\case-a\final\paper\paper.html` |
| Repository | `.scratch\case-a\out3\repo` |
| Backend | local |
| Commands | 4 (failed: 0) |
| Wall clock | 0.6 min |
| Local disk | 1.7 GB |
| Recipe source | curated |
| Level | L2 - released weights, no training |

## Evidence

- `accuracy: 0.9106`
- from `E:\Projects\new-project\.scratch\case-a\final\attempt-1\artifacts\99-eval.log`

## Command log

| # | Command | Exit | Time | Log |
|---|---------|------|------|-----|
| 1 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/prepare_data` | 0 | 0s | 01-data.log |
| 2 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install torch --index-url` | 0 | 2s | 01-install.log |
| 3 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" -m pip install -e .` | 0 | 14s | 02-install.log |
| 4 | `"E:\Projects\new-project\.scratch\case-a\out3\repo\.paperrepro-venv\Scripts\python.exe" .paperrepro-harness/eval_sst2.py` | 0 | 22s | 99-eval.log |

## Plan that was executed

```
plan: distilbert-sst2 (source: curated)
  install 1: {pip} install torch --index-url https://download.pytorch.org/whl/cpu
  install 2: {pip} install -e .
  data    1: {python} {harness}/prepare_data.py --dest data
  eval      : {python} {harness}/eval_sst2.py --data data --model distilbert-base-uncased-finetuned-sst-2-english
  notes     : L2: released DistilBERT checkpoint, evaluated on the SST-2 dev split with the repository installed as a package. No training.
```

## Recommendation

**use as a baseline.** The reported number reproduces within tolerance and the configuration is consistent.

Conditions:

- cite the measured value, not the paper's, when you compare against it
- keep the recipe with your results so the comparison can be re-run

Re-running: about 1 min per run; a 3-seed comparison costs ~0.0 machine-hours, plus your own data preparation.

## Viability

| Dimension | Score | Note |
|-----------|-------|------|
| executability | 5.0/5 | run status ok |
| fidelity | 5.0/5 | 1/1 claims match |
| cost | 5.0/5 | 1 min, 1.7 GB on disk |
| comparability | 3.0/5 | protocol must be checked by hand: split, preprocessing and metric definition |
| openness | 3.5/5 | licence present |

**Overall 4.3/5 → use as a baseline.**

## Limits of this run

- One environment, one seed, one machine. A match here is evidence, not proof.
- The comparison covers only claims whose metric the run actually printed.
- Protocol differences (split, preprocessing, metric definition) are not detected automatically; check them before quoting these numbers in a paper.
