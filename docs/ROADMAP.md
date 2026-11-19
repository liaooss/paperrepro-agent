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
| Case that fails honestly | not yet |
| Automatic plan inference | works on conventional repositories, refuses otherwise |

**Exit criterion:** two real cases, one success and one honest failure, both
committed with artifacts. One of the two must run from an inferred plan.

## Phase 2 - autonomous planning and repair

- Plan inference for repositories without a README command (config-driven
  entry points, `argparse` defaults, `hydra`/`omegaconf` configs).
- Bounded repair loop: environment, path and API-rename failures only; each
  attempt logged, each source edit kept as a patch beside the run.
- A repaired attempt is a separate run with its own status; the report shows
  both, so a repaired run can never masquerade as the original.

## Phase 3 - evaluation system

- Multi-seed execution (>=3 seeds) with variance reported next to the delta.
- Consistency audit extended to dataset splits, preprocessing and metric
  definitions.
- Viability report with the "is this a defensible baseline" recommendation and
  the cost of keeping it in a comparison table.

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
