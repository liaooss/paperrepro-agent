# Case: MIMIC-III benchmarks (an honest failure)

The second case exists to prove the tool can say "I cannot check this" without
turning that into a verdict about the paper.

| | |
|---|---|
| Paper | *Multitask learning and benchmarking with clinical time series data* (arXiv:1703.07771) |
| Release | [YerevaNN/mimic3-benchmarks](https://github.com/YerevaNN/mimic3-benchmarks) |
| Attempt | modeleval on the in-hospital-mortality benchmark |
| Outcome | **not verifiable on this machine**, for two independent reasons |

## Two independent blocks

**1. Static assessment: R1, `RC05`**

```
verdict   R1  needs assets outside the release
  blocker RC05 Dataset requires manual or restricted acquisition
```

The repository's own README says it:

> We do not provide the MIMIC-III data itself. You must acquire the data yourself
> from https://mimic.physionet.org/.

PhysioNet access is credential-gated (training + data use agreement). The release
cannot be checked from a clean checkout, no matter how much engineering is done
on our side.

**2. Executed attempt: `ENV_CONFLICT`**

```
status    INSUFFICIENT_EVIDENCE  the run failed before producing a measurement (ENV_CONFLICT)
run       failed  (ENV_CONFLICT)
```

Evidence, quoted from the install log:

```
ERROR: No matching distribution found for tensorflow==1.15.0
```

The release pins `tensorflow==1.15.0`, `Keras==2.1.2` and `numpy==1.16.5` — a
Python 3.7 stack. No wheel exists for the interpreter on this machine, so the
environment cannot be built at all.

## Why this is the behaviour we want

- The tool did **not** report `NOT_REPRODUCED`. A failure on our side is not a
  finding about the paper; the status is `INSUFFICIENT_EVIDENCE`.
- The recommendation is **do not use as a baseline yet** (2.5/5), not "usable
  with conditions", even though the raw score sits at the threshold. Cost and
  licence scores are not evidence about the paper.
- The install log is kept verbatim, so the reader can see the resolver's own
  words rather than a summary.

## What would unblock it

1. `conda create -p .env python=3.7` (the release's own instruction), then
   `pip install -r requirements.txt`.
2. Credentialed MIMIC-III access, then the five `mimic3benchmark.scripts.*`
   preprocessing steps.

Both are outside what a reproduction tool can obtain on its own. Recording that
precisely is the deliverable.

## What is still unexercised

The `BLOCKED` status (missing checkpoints, data unavailable *at runtime*) is
covered by unit tests but has not yet been produced by a real case; this case
fails earlier, at environment build time. That gap is recorded in
`docs/ROADMAP.md`.

## Artifacts

| File | Content |
|---|---|
| [`result/run_report.md`](result/run_report.md) | the executed attempt |
| [`result/static_report.md`](result/static_report.md) | the static assessment |
| [`result/install.log`](result/install.log) | the failing pip run, verbatim |
| [`result/results.json`](result/results.json) | machine-readable record |
| [`recipe.json`](recipe.json) | what was attempted, and why |
