# Reproduction report: DistilBERT on SST-2

The first end-to-end case, executed by the engine on 2026-11-19.

## Identification

| | |
|---|---|
| Paper | *DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter* (arXiv:1910.01108) |
| Claim checked | Table 2, GLUE results, row DistilBERT, column SST-2: **91.3** |
| Release | `huggingface/transformers` |
| Level | L2 — released weights, evaluated on the paper's dev split; no training |

## Result

| | |
|---|---|
| **Status** | **REPRODUCED** |
| Measured | 91.06 (872 dev examples) |
| Delta | **-0.24 points** (tolerance 0.5) |
| Viability | **4.3 / 5** — *use as a baseline* |
| Wall clock | ~1 min warm, ~6 min cold |
| Local disk | 1.1 GB |

Evidence line, quoted from the run's own log:

```
accuracy: 0.9106
```

Provenance: `artifacts/99-eval.log` <- command 4 of 4 (exit 0) <- repository
`huggingface/transformers` @ `90cbc670be7f` <- recipe
`examples/cases/distilbert-sst2/recipe.json`.

## Viability detail

| Dimension | Score | Basis |
|---|---|---|
| executability | 5.0 | environment built, all four commands exited 0 |
| fidelity | 5.0 | 1/1 compared claim within tolerance |
| cost | 5.0 | ~1 min and 1.1 GB to re-run |
| comparability | 3.0 | split matches; preprocessing and label mapping were ours, not the paper's |
| openness | 3.5 | licence present; a static rule still flags unreleased checkpoints elsewhere in the repository |

## Consistency audit

The audit compares what the paper states with what the code configures.

**Result: no comparable configuration found.**

That is the correct answer here, and it is a finding rather than a failure of the
tool: `transformers` is a library, not the training script that produced this
checkpoint. Its configuration files describe model architecture, not the
DistilBERT distillation run (learning rate, batch size, epochs), and the paper's
hyperparameters live in the paper and the model card rather than in this
repository.

The report says so explicitly instead of quoting a generic `trainer_pt_utils.py`
constant as if it were the experiment's batch size. An earlier build did exactly
that and produced six confident, meaningless rows; restricting the audit to
configuration files and plausible ranges removed them.

## What this proves

- The loop closes: acquire -> isolate -> run -> parse -> compare -> status ->
  score, with the producing log line preserved.
- A measured 91.06 against a published 91.3 is what "reproducible" looks like
  when the protocol is close but not identical.

## What this does not prove

- **Not a training reproduction.** The checkpoint was downloaded, not retrained.
  DistilBERT's distillation itself remains unreproduced here.
- **Not a protocol claim.** Tokenisation, max length (128) and label mapping were
  our choices; the comparability dimension is scored 3.0 for that reason.
- **One seed.** There is no training run and therefore no seed variance.
- **One environment.** CPU, one dependency resolution, one torch version.

## How to re-run

```bash
paperrepro run https://ar5iv.labs.arxiv.org/html/1910.01108 \
  --repo https://github.com/huggingface/transformers \
  --recipe examples/cases/distilbert-sst2/recipe.json \
  --out runs/distilbert-sst2
```

Artifacts for this exact run are committed under
`examples/cases/distilbert-sst2/result/`.

---

# Case 2: MIMIC-III benchmarks — the failure

A tool that has only ever seen success has never been tested. The second case is
a real release that cannot be verified, and the point is *how* that is reported.

| | |
|---|---|
| Paper | *Multitask learning and benchmarking with clinical time series data* (arXiv:1703.07771) |
| Release | `YerevaNN/mimic3-benchmarks` |
| Static verdict | **R1** — `RC05` dataset requires manual or restricted acquisition |
| Executed status | **INSUFFICIENT_EVIDENCE** — `ENV_CONFLICT` |
| Viability | 2.5 / 5 — *do not use as a baseline yet* |

## Two independent reasons

1. The README states: *"We do not provide the MIMIC-III data itself. You must
   acquire the data yourself from https://mimic.physionet.org/."* PhysioNet is
   credential-gated; the data cannot be part of an automated reproduction.
2. The release pins `tensorflow==1.15.0` and `Keras==2.1.2`, a Python 3.7 stack.
   On a current interpreter the install dies with
   `ERROR: No matching distribution found for tensorflow==1.15.0`.

## What the tool refused to do

- It did not report `NOT_REPRODUCED`. Our inability to build a 2019 environment
  says nothing about the paper's results.
- It did not recommend the paper "with conditions" just because the arithmetic
  landed at 2.5/5. A run with no measurement cannot be recommended at all.
- It did not paraphrase the failure. The resolver's own line is in the report
  and in `examples/cases/mimic3-benchmarks/result/install.log`.

## What remains unexercised

`BLOCKED` (missing checkpoints, data unavailable at runtime) is covered by unit
tests but no real case has produced it yet; this case stops earlier, at
environment build time. Recorded as an open item in `docs/ROADMAP.md`.
