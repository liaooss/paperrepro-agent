# Roadmap: from static assessment to executed reproduction

This document records the plan agreed after the first working prototype: reprocheck
starts as a *static* assessment tool and grows an execution engine, because the
only thing that answers "is this paper worth using as a baseline" is a number
that we produced ourselves.

## The thesis, in one line

> Paper claim -> code location -> command that was actually run -> log line ->
> measured value -> delta -> judgement, with every arrow openable.

If a feature does not strengthen an arrow in that chain, it is not M1 work.

## What exists today (v0.1)

| Layer | Status | What it does |
|---|---|---|
| Paper ingest | done | LaTeX / Markdown / HTML, optional PDF |
| Claim ledger | done | metric, value, dataset, table row/column, paper location |
| Repository scan | done | entry points, manifests, configs, seeds, metric/dataset refs, checkpoints |
| Risk rules | done | 17 deterministic checks, two author-dependent blockers |
| Static verdict | done | R0-R3 + per-claim E1/E2/E3/X |
| **Execution** | **v0.2, in progress** | recipe -> isolated env -> run -> parse metrics -> compare -> viability |

## What "done" means for M1

A single command, on a machine with one consumer GPU, takes a paper URL and a
repository URL and produces `run_report.md` containing:

1. the claim, quoted, with its table and row;
2. the released artifact that implements it (file, or checkpoint);
3. the exact command that ran, with exit code and duration;
4. the measured value, quoted from the log line that printed it;
5. the delta against the paper, in points, with the tolerance used;
6. a viability verdict with its five dimension scores;
7. the artifacts needed to re-run: commit hash, recipe, logs.

**Acceptance:** at least one real paper reaches step 5 with a real number, and
the whole run is reproducible from the committed recipe. Two papers is better
than one, one of each outcome (match / miss) is better still.

## Deliberate non-goals for M1

- **No web UI.** A report file is the interface until the engine is trustworthy.
- **No nine-agent orchestra.** See below.
- **No five domain adapters.** One vertical, run through end to end.
- **No Postgres / Redis / Celery / MinIO / MLflow.** A single process writing
  JSON + SQLite is enough for hundreds of runs. The storage *interface* is what
  matters; swapping the backend later is a day of work, not a redesign.
- **No automatic source-code patching.** Fixes may only touch environment,
  paths and entry commands; anything that changes model or training semantics is
  recorded as a variant run, never silently applied.

## Agents vs tools

The spec lists nine agents. Nine conversational agents multiply cost, latency
and nondeterminism, and each hand-off is a place where evidence gets paraphrased.

The split that survives contact with real repositories:

| Role | Implementation | Why |
|---|---|---|
| Paper analysis | LLM, structured JSON, every field carrying a paper location | genuinely fuzzy |
| Code analysis | deterministic scan + AST | exact, cheap, reproducible |
| Consistency audit | deterministic diff of paper fields vs config values | a comparison, not a judgement |
| Environment | deterministic resolver + container build | must be repeatable |
| Execution | subprocess in container, no LLM in the loop | must not "decide" anything |
| Failure diagnosis | rule table over log signatures, LLM only for unseen kinds | 90% of failures are recognisable |
| Result comparison | arithmetic | no model may round a number |
| Evaluation | rubric over recorded evidence, LLM writes prose only | the verdict must be auditable |

So: **3 LLM call sites** (paper extraction, unseen-failure explanation, report
prose), everything else deterministic. An agent framework can wrap this later
without changing it, because the state machine and the artifacts already exist.

## Phases

### M1 - executed reproduction (current)

- [x] recipe format, backends (local venv, conda, docker), command recording
- [x] metric extraction with explicit regex precedence
- [x] fraction/points normalisation and tolerance-based comparison
- [x] five-dimension viability scoring
- [ ] failure taxonomy hardened against real runs (repo integrity, network, auth)
- [ ] one paper reproduced end to end, committed as `examples/cases/<name>`
- [ ] `run_report.md` + `results.json` + artifacts published in the repo

### M2 - automation and repair

- [ ] recipe inference from README/entry points, always human-confirmed
- [ ] bounded repair loop: environment and path failures only, each attempt logged
- [ ] multi-seed runs, variance reported next to the delta
- [ ] baseline shortlist: given 3-5 papers, rank by viability and cost

### M3 - surface area

- [ ] MCP server exposing create/status/logs/compare/report (thin wrapper over the CLI)
- [ ] HTML report with the comparison chart
- [ ] web UI: task list, live log, evidence viewer

### M4 - breadth

- [ ] domain adapters (time series anomaly detection, CV classification, GNN node classification)
- [ ] benchmark suite of 20 releases with human labels, published with the tool

## Security posture

Running a stranger's repository is the riskiest thing this project does.

- Execution happens in a container with the repository directory as the only
  mount; no host home, no Docker socket, no privileged mode.
- Network is needed for dependencies and datasets; it is enabled per recipe and
  recorded, and can be restricted to an allowlist.
- No credentials from the analyst's environment are passed into the container.
- Every command, its exit code and its output is written to disk before any
  conclusion is drawn from it.
- The default backend for a new recipe is `docker`; `local` exists for
  development and for machines where Docker is unavailable.

## Open questions

1. Which single vertical to prove first (time series anomaly detection, CV
   classification, or the analyst's own field)?
2. Whether to keep the name `reprocheck` for the engine and use a product name
   for the umbrella, or rename once.
3. Budget for the first case: consumer GPU only (8 GB), no paid compute.
