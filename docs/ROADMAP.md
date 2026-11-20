# Roadmap

Status as of 2026-11-19. Phases follow `docs/PROJECT_PLAN.md`.

## Phase 1 - core reproduction engine (in progress)

| Item | Status |
|---|---|
| Paper ingest (LaTeX, Markdown, HTML, PDF via extra) | done |
| Claim ledger with paper locations | done |
| Repository scan and 17 static rules | done |
| Recipe format and three backends | done, docker unexercised |
| Command recording, failure taxonomy | done |
| Metric extraction and comparison | done |
| Five-state reproduction status | done |
| Consistency audit (paper vs code) | first version, 6 parameter families |
| Report: Markdown + JSON + artifacts | done |
| Case that reproduces (DistilBERT / SST-2) | **done** |
| Case that fails honestly (MIMIC-III / ENV_CONFLICT) | **done** |
| Automatic plan inference | works on conventional repositories, refuses otherwise |
| BLOCKED path exercised by a real case (missing weights at runtime) | not yet - only unit tested |

**Exit criterion:** two real cases, one success and one honest failure, both
committed with artifacts. One of the two must run from an inferred plan.

## Phase 2 - autonomous planning and repair

- **Done:** config-driven plan inference - an entry point that takes
  `--config` is paired with the config the release ships, and beats the bare
  `run.py` candidate.
- **Done:** bounded repair for `ENV_CONFLICT` dead pins and missing directories;
  each attempt is a separate run, each edit kept as a patch and a backup, and
  the checkout is restored afterwards.
- **Done:** the report labels repaired numbers as coming from the repaired
  attempt, never as the original.
- **Next:** API-rename repair (`cannot import name X from Y`), which needs a
  symbol map and is not safe to guess yet.

## Phase 3 - evaluation system

- **Done:** multi-seed execution. `recipe.seeds` repeats the evaluation and
  the report shows mean, standard deviation, per-seed values, and whether the
  spread is small relative to the tolerance.
- **Next:** consistency audit extended to dataset splits, preprocessing and
  metric definitions.
- **Next:** viability report with the "is this a defensible baseline"
  recommendation and the cost of keeping it in a comparison table.

## Phase 4 - surfaces

- MCP server: `create_reproduction`, `get_task_status`, `get_experiment_logs`,
  `compare_results`, `generate_report`; read-only resources for artifacts.
- Web UI over the same run directory: task list, live log, evidence viewer,
  comparison chart.
- No business logic in either surface.

## Phase 5 - domains

One adapter per vertical, each with a real case before the adapter counts as
done: time series anomaly detection, CV classification, GNN node classification,
NLP classification, scientific ML regression.

## Phase 6 - release

- Benchmark of 20 releases with human labels, published with the tool.
- Packaging, install guide, contribution guide, issue templates.
- A published precision/recall figure for the verdict itself.
