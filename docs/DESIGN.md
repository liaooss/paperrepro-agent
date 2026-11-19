# Design

## The one-sentence constraint

> A claim you cannot trace is not a finding.

Everything below follows from it. If a design choice would let reprocheck say something that a reviewer cannot check against the paper or the code, the choice is wrong.

## Pipeline

```
            ┌──────────────┐
 paper ────►│  paper.py    │──► PaperDoc {sections, tables, text}
            └──────────────┘
            ┌──────────────┐
 repo  ────►│  repo.py     │──► RepoScan {files, manifests, entry points,
            └──────────────┘             metric refs, paths, checkpoints}
                     │
                     ▼
            ┌──────────────┐
            │  claims.py   │──► [Claim] with paper evidence
            └──────────────┘
                     │            ┌──────────────────┐
                     ├───────────►│  smoke.py        │ (optional, --smoke)
                     │            └──────────────────┘
                     ▼
            ┌──────────────┐
            │  matcher.py  │──► Claim.level ∈ {E1,E2,E3,X} + code evidence + gaps
            └──────────────┘
                     │
                     ▼
            ┌──────────────┐
            │  rules.py    │──► [Finding] (17 deterministic rules)
            └──────────────┘
                     │
                     ▼
            ┌──────────────┐
            │  score.py    │──► verdict R0–R3 + confidence
            └──────────────┘
                     │
                     ▼
            report.md / scorecard.json / reproduction_plan.md
```

## Module map

| Path | Responsibility | Rule it must not break |
|---|---|---|
| `ingest/paper.py` | LaTeX/Markdown/HTML/PDF → sections + tables | never invent a table row that is not in the source |
| `ingest/repo.py` | Walk the checkout, collect evidence pointers | never execute repository code |
| `extract/claims.py` | Numbers with meaning → claim ledger | every claim carries a paper location |
| `align/matcher.py` | Claim → code evidence, level decision | a level is only raised by evidence, never by plausibility |
| `risk/rules.py` | 17 checks, pure functions of the scan | no network, no clock, no randomness |
| `smoke.py` | Compile + entry point + manifest check | no downloads, no training, no writes into the repo |
| `verdict/score.py` | Verdict and confidence | the mapping is documented in RUBRIC.md and testable |
| `verdict/report.py` | Render Markdown / plan / console | every finding prints its evidence pointer |
| `llm/client.py` | Optional prose + dataset hint | may never introduce a fact that is not in the evidence |

## Decisions and their costs

### Static first, execution optional

Reproduction attempts fail for boring reasons long before training starts: a missing checkpoint, an unpinned dependency, an absolute path. Those are observable without running anything, and checking them costs seconds instead of GPU-days.

**Cost:** E1 only means "compiles, has an entry point". A release can be R3 by this rubric and still fail on the first real batch. That is stated in every report under "Limits".

**Why not execute by default:** executing untrusted research code is a security decision and a cost decision. Neither belongs in a tool a reviewer runs on a laptop. `--smoke` is the deliberate, bounded compromise.

### Deterministic core, LLM at the edge

Two audits of the same commit must agree. That rules out using a model to produce findings. Rules are pure functions; the LLM may only rewrite the summary and propose a dataset label, and its proposal is rejected unless it cites evidence it was given.

**Cost:** recall. A rule cannot recognise a novel failure mode; symbolic metric matching misses paraphrases. The roadmap addresses this with better static analysis, not with a bigger model.

### Claim ledger as the contract

The ledger is the interface between paper and code. It is small, JSON-serialisable, and stable: `{metric, value, dataset, split, role, evidence[], level}`. Everything downstream reads it, and it is the only thing a future benchmark needs.

**Cost:** a number that lives only in a figure never enters the ledger. Accepted; OCR of plots is a different project with a much worse error profile.

### Zero runtime dependencies

`pip install reprocheck` must work in a bare CI image, on an air-gapped reviewer's laptop, in five years. The core imports nothing outside the standard library. PDF support is an extra because `pypdf` is the one thing genuinely hard to reimplement.

**Cost:** no `requests`, no `rich`, no `pydantic`. The HTTP client is 40 lines of `urllib`; the terminal output is plain text. That is fine.

### Baselines are context, not claims

A results table row for `ResNet-18` is not something the release promises to reproduce. Counting it would inflate or deflate the verdict. Rows whose label says "ours"/"this work" become `role="paper"`; the rest are `role="reference"` and are shown but excluded from the verdict.

**Cost:** if no row is marked, everything is treated as a paper claim (conservative).

## Extension points

- **New rule** — add a function to `risk/rules.py`, append `(id, title, severity)` to `RULES`, add a test. Rules receive the whole `RepoScan`, so anything observable statically is fair game.
- **New paper format** — add a `_parse_x` in `ingest/paper.py` returning `PaperDoc`; the rest of the pipeline is format-agnostic.
- **New metric or dataset** — extend `METRIC_SYNONYMS` / `DATASET_SYNONYMS` in `textutil.py`. Matching is case- and separator-insensitive.
- **Better alignment** — `align/matcher.py` is the only place that assigns levels; swapping in embeddings or a code index changes one module.

## Known failure modes

| Symptom | Cause | Mitigation |
|---|---|---|
| No claims extracted | paper states numbers only in prose with several numbers per sentence, or only in figures | pass the LaTeX source; the extractor is deliberately strict (one number per sentence) |
| Metric matched in a docstring | no definition exists, so the fallback cites the first mention | the finding is still true; `E3` marks it weak |
| Over-eager X | dataset name is a house name ("our benchmark") | rule RC17 is `major`, not `blocker`; a human re-reads the listed claims |
| False RC13 | optional imports inside `try:` | known false positive; documented in RUBRIC.md |

## Roadmap

1. **Container execution (M2)** — opt-in `--execute` that builds an image, runs the README command, captures exit codes and the first 50 log lines as evidence.
2. **Figure OCR (M3)** — recover numbers from plotted curves, marked as `E-figure` and never used to raise a level on its own.
3. **Benchmark of verdicts** — 50 known releases with human-labelled outcomes, published with the tool, so the rubric itself can be evaluated for precision and recall.
4. **Diff mode** — compare two releases of the same paper and report what the new artifact fixed.
