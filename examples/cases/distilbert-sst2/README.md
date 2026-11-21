# Case: DistilBERT on SST-2 (level L2)

The first executed case, kept in the repository as the reference for what a
`run_report.md` should look like — including the failures it took to get there.

| | |
|---|---|
| Paper | [arXiv:1910.01108](https://arxiv.org/abs/1910.01108) — *DistilBERT, a distilled version of BERT* |
| Claim | Table 2, GLUE results, DistilBERT, SST-2: **91.3** |
| Release | [huggingface/transformers](https://github.com/huggingface/transformers) |
| Level | L2 — released weights, no training |
| Recommendation | **use as a baseline** (conditions: cite the measured value, keep the recipe) |

## Result

```
paper     91.3  (Table 2, SST-2)
measured  91.06 (872 dev examples)
delta     -0.24 points (tolerance 0.5)
status    MATCH
viability 4.3 / 5  -> use as a baseline
```

Full report: [`result/run_report.md`](result/run_report.md) · raw metrics and
command log: [`result/results.json`](result/results.json) · the line that
produced the number: [`result/eval.log`](result/eval.log).

Reproduce it:

```bash
paperrepro run https://ar5iv.labs.arxiv.org/html/1910.01108 \
  --repo https://github.com/huggingface/transformers \
  --recipe examples/cases/distilbert-sst2/recipe.json \
  --out runs/distilbert-sst2
```

Cold run: ~6 min (torch download dominates). Warm run: ~50 s.

## What broke first, and what it changed

The value of a case like this is the list of things that fail before the number
appears. All three were found by running, not by reading.

**1. `git clone` died mid-transfer.** `fatal: early EOF / invalid index-pack
output` on a large repository. Worse, the interrupted clone left a directory
that *existed* and *looked* populated, so the next step failed three commands
later with "not a Python project".
→ Repository acquisition now validates the working tree and falls back to a
`codeload` tarball (`clone_repo`), recording `tarball:refs/heads/main` when that
path is taken.

**2. The evaluation crashed on a cache directory outside the workspace.**
`PermissionError [WinError 5]` on `~/.cache/huggingface/hub`.
→ Every backend now pins `HF_HOME`, `HF_HUB_CACHE`, `TORCH_HOME` and
`MPLCONFIGDIR` inside the run directory. This is also the correct behaviour for
auditability: a run must not depend on a cache that predates it.

**3. The paper's table could not be parsed automatically.** DistilBERT's Table 2
puts *datasets* in the columns (MNLI, QQP, SST-2, ...) and the metric in the
caption, so a metric-column extractor finds nothing to compare.
→ A recipe may declare `target` explicitly, and must declare where it came from:
`"source": "arXiv:1910.01108, Table 2 (GLUE results), row DistilBERT, column SST-2"`.
The report prints that provenance next to the delta. Automatic extraction of
dataset-in-column tables is still on the roadmap; until then the honest fallback
is a declared target, not a guessed one.

## Repeatability across seeds

`recipe-seeds.json` repeats the same evaluation under three seeds:

| Metric | Mean | Std | Runs | Per-seed |
|---|---|---|---|---|
| accuracy | 0.9106 | 0.0000 | 3/3 | 1:0.9106, 2:0.9106, 3:0.9106 |

A zero spread is the correct answer for a deterministic evaluation, and it is
informative: the -0.24 point delta cannot be sampling noise, so it must come from
the protocol (tokenisation, max length, label mapping) or from the checkpoint
itself. Evidence: [`result/multiseed_report.md`](result/multiseed_report.md).

## Two backends, same number

The same recipe ran under both isolation backends:

| Backend | Isolation | Wall clock | Metric |
|---|---|---|---|
| `local` | venv | 0.6 min (warm) | 0.9106 |
| `docker` | container, 3.26 GB image | 10.0 min cold (3.3 min build) | 0.9106 |

Identical to four decimals, which is what a deterministic evaluation should do
and what makes the container path trustworthy. Evidence:
[`result/docker_report.md`](result/docker_report.md).

## What this case does and does not prove

- It proves the loop closes: acquire → isolate → run → parse → compare → score,
  with the producing log line kept.
- It does not prove the protocol matches. SST-2 dev is the split the paper used,
  but tokenisation, max length and label mapping were our choices. The
  comparability dimension is scored 3.0/5 for exactly this reason.
- One seed, one machine, one dependency resolution. A 0.24-point gap is inside
  noise; a 5-point gap would not be.
