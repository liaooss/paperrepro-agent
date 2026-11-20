# Reproduction run — mimic3-benchmarks

> **Status: INSUFFICIENT_EVIDENCE** — insufficient evidence.  
> after 1 repair attempt(s) on ENV_CONFLICT: the run failed before producing a measurement (COMMAND_FAILED)  
> Recommendation: **do not use as a baseline yet** · viability 2.5/5

Claims compared: NOT_RUN:1 (tolerance 0.5 points).

## Claim comparison

| Claim | Metric | Paper | Measured | Delta (points) | Status |
|-------|--------|-------|----------|----------------|--------|
| C01 | AUC | 0.91 | — | — | not run |

## Consistency audit — paper versus code

| Parameter | Paper says | Code says | Result | Evidence |
|-----------|------------|-----------|--------|----------|
| optimizer | ADAM | — | PAPER_ONLY | `Experiments, Model selection and Evaluation: "ADAM"` |

None of the paper's stated parameters could be matched to a value in the code, so this audit is inconclusive rather than clean.

## What was run

| | |
|---|---|
| Paper | `E:\Projects\new-project\.scratch\case-b7\paper\paper.html` |
| Repository | `.scratch\mimic3` |
| Backend | local |
| Commands | 1 (failed: 1) |
| Wall clock | 0.8 min |
| Local disk | 0.0 GB |
| Recipe source | curated |
| Level | execution plan |

## Why it failed

- **Kind:** `COMMAND_FAILED`
- **Evidence:**  maybe_cythonize
        File "E:\Projects\new-project\.scratch\mimic3\pip-build-env-_um87y3p\overlay\Lib\site-packages\Cython\Build\Dependencies.py", line 1106, in cythonize
          result.get(99999)  # seconds
          ~~~~~~~~~~^^^^^^^
        File "E:\tool\miniconda\Lib\multiprocessing\pool.py", line 774, in get
          raise self._value
      Cython.Compiler.Errors.CompileError: pandas\_libs/algos.pyx
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
ERROR: Failed to build 'pandas' when getting requirements to build wheel


Failure kinds map to different remedies:

- `MISSING_WEIGHTS` / `DATA_UNAVAILABLE` — only the authors can fix this; ask them.
- `ENV_CONFLICT` — try `--backend docker`, or let the bounded repair drop a dead pin (it will say so in **Repair attempts**).
- `OOM` — reduce batch size or resolution; the claim may still be checkable.
- `TIMEOUT` — raise `--limit-minutes` or reduce the evaluation split.

## Repair attempts

The first attempt failed. Only the environment was touched; no model or training logic was modified, and each edit is kept as a patch next to the run.

| # | Failure | Strategy | Change | Patch | Result |
|---|---------|----------|--------|-------|--------|
| 1 | `ENV_CONFLICT` | unpin | requirements.txt: 'tensorflow==1.15.0' -> 'tensorflow' (the pinned wheel no longer exists) | unpin-tensorflow.diff | did not help |

The repair did not produce a measurement; the status below reflects the repaired attempt.

## Command log

| # | Command | Exit | Time | Log |
|---|---------|------|------|-----|
| 1 | `"E:\Projects\new-project\.scratch\mimic3\.paperrepro-venv\Scripts\python.exe" -m pip install -r requirements.txt` | 1 | 49s | 01-install.log |

## Plan that was executed

```
plan: mimic3-benchmarks (source: curated)
  install 1: {pip} install -r requirements.txt
  eval      : {python} -m mimic3benchmark.scripts.extract_subjects data/root/ data/root/
  notes     : The release pins tensorflow==1.15.0 and Keras==2.1.2 (Python 3.7 era) and its README states the MIMIC-III data must be acquired from PhysioNet by the reader. Either constraint alone is enough to stop a reproduction on a modern machine.
```

## Viability

| Dimension | Score | Note |
|-----------|-------|------|
| executability | 2.0/5 | run status failed (COMMAND_FAILED) |
| fidelity | 0.0/5 | no claim could be compared |
| cost | 2.5/5 | 1 min, 0.0 GB on disk (run did not complete; cost is a lower bound) |
| comparability | 3.0/5 | protocol must be checked by hand: split, preprocessing and metric definition |
| openness | 5.0/5 | licence present |

**Overall 2.5/5 → do not use as a baseline yet.**

Blockers:

- COMMAND_FAILED:  maybe_cythonize
        File "E:\Projects\new-project\.scratch\mimic3\pip-build-env-_um87y3p\overlay\Lib\site-packages\Cython\Build\Dependencies.py", line 1106, in cythonize
          result.get(99999)  # seconds
          ~~~~~~~~~~^^^^^^^
        File "E:\tool\miniconda\Lib\multiprocessing\pool.py", line 774, in get
          raise self._value
      Cython.Compiler.Errors.CompileError: pandas\_libs/algos.pyx
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
ERROR: Failed to build 'pandas' when getting requirements to build wheel

- no measured value to compare against the paper

## Limits of this run

- One environment, one seed, one machine. A match here is evidence, not proof.
- The comparison covers only claims whose metric the run actually printed.
- Protocol differences (split, preprocessing, metric definition) are not detected automatically; check them before quoting these numbers in a paper.
