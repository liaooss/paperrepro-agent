# Architecture

## One sentence

> Paper claim -> code location -> command that ran -> log line -> measured value
> -> delta -> judgement, with every arrow openable.

Everything below serves that chain.

## Layers

```
             ┌─────────────────────────────────────────────┐
   entry     │  CLI (paperrepro)   MCP server   Web (later) │
             └───────────────────┬─────────────────────────┘
                                 │ same engine, no duplicated logic
             ┌───────────────────▼─────────────────────────┐
   case      │ execute.case.run_case                       │
             │  acquire -> plan -> execute -> audit ->     │
             │  compare -> status -> viability -> report   │
             └───┬─────────┬──────────┬─────────┬──────────┘
                 │         │          │         │
   domain    ┌───▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼──────┐
   modules   │ingest │ │ extract│ │  plan  │ │  audit  │
             │paper  │ │ claims │ │ infer  │ │ config  │
             │repo   │ │        │ │        │ │         │
             └───────┘ └────────┘ └────────┘ └─────────┘
                 │         │          │         │
   execution  ┌──▼─────────▼──────────▼─────────▼───────┐
              │ execute.runner  +  backends              │
              │ local venv | conda | docker              │
              └───┬──────────────────────┬───────────────┘
                  │                      │
   scoring    ┌──▼────────┐   ┌─────────▼──────┐   ┌────────────┐
              │ risk rules │   │ compare/status │   │ viability  │
              └────────────┘   └────────────────┘   └────────────┘
```

## Module map

| Path | Responsibility | Invariant |
|---|---|---|
| `ingest/paper.py` | LaTeX/Markdown/HTML/PDF -> sections + tables | never invent a row that is not in the source |
| `ingest/repo.py` | walk the checkout, collect pointers | never execute repository code |
| `extract/claims.py` | numbers with meaning -> claim ledger | every claim carries a paper location |
| `plan/infer.py` | derive a recipe from README/entry points | refuse rather than guess |
| `execute/recipe.py` | the only thing that may be executed | declarative, reviewable, serialisable |
| `execute/backends.py` | isolated environments | no global installs, caches inside the run dir |
| `execute/runner.py` | run commands, record everything | a conclusion may not precede the log |
| `execute/parse.py` | metrics out of output | explicit regex beats heuristics |
| `execute/compare.py` | paper vs measured | unit normalisation is explicit |
| `execute/repair.py` | bounded environment repair | never touches model or training logic |
| `execute/status.py` | five-state verdict | no evidence is not a negative result |
| `execute/viability.py` | should this be a baseline | dimensions are independent and named |
| `audit/config_audit.py` | paper hyperparameters vs code | quotes both sides |
| `risk/rules.py` | 17 static checks | pure functions of the scan |
| `verdict/score.py` | static R0-R3 | documented in RUBRIC.md and tested |
| `llm/client.py` | optional prose | may never introduce a fact |

## Data flow of one run

```
paper.html ──load_paper──► PaperDoc {sections, tables}
                              │
                              ├─extract_claims──► [Claim]  (paper location)
                              └─audit──► [ParamCheck] (paper value, code value)
repo/ ─────scan_repo────► RepoScan {files, manifests, entry points, refs}
                              │
recipe.json / infer_recipe ───┴──► Recipe {install, data, eval_cmd, metric}
                                        │
                                   execute_recipe
                                        │
                              artifacts/*.log + run.json + commands.jsonl
                                        │
                        extract_metrics ─┴─► {metric: value}
                                        │
                       compare_claims ────┴─► [ClaimOutcome]  MATCH/CLOSE/MISMATCH/NOT_RUN
                                        │
                  reproduction_status ────┴─► REPRODUCED | PARTIALLY | NOT | BLOCKED | INSUFFICIENT
                                        │
                     assess_viability ────┴─► 5 dimensions + recommendation
                                        │
                              render_run_markdown ──► run_report.md
```

## Core records

| Record | Holds | Why it exists |
|---|---|---|
| `Claim` | metric, value, dataset, role, paper evidence, level | the interface between paper and code |
| `Recipe` | install/data/eval commands, metric, tolerances, budget | the only executable unit |
| `RunResult` | status, failure kind, metrics, commands, duration, disk | makes the run auditable after the fact |
| `ClaimOutcome` | paper value, measured value, delta, status | the comparison, never a rounding |
| `Viability` | five dimensions + recommendation | separates "reproducible" from "usable" |
| `ParamCheck` | paper value, code value, both locations | the consistency audit |

## Why the engine has no web framework

The engine's output is a directory: `run_report.md`, `results.json`,
`artifacts/*.log`. A UI is a viewer over that directory. Building the viewer
first produces a product that looks finished and cannot answer a single
question; building the directory first means every surface later is a thin
adapter.

## Extension points

- **New rule** - `risk/rules.py`, register in `RULES`, test, document in RUBRIC.
- **New paper format** - `_parse_x` returning `PaperDoc`; nothing downstream cares.
- **New backend** - implement `prepare/run` in `backends.py`; `docker` and
  `conda` are the reference implementations.
- **New metric** - extend `METRIC_SYNONYMS`; comparison already normalises units.
- **New domain adapter** - only needed once a second vertical is added; the
  current plan/execute cycle is domain-agnostic.

## Docker backend

`docker` builds one image per recipe (`FROM python:<recipe.python>-slim`, the
install steps as `RUN`, the checkout `COPY`ed in), then runs each command with
the checkout bind-mounted at `/work` so datasets and caches survive the run.

Three things are deliberate:

- the image name is a SHA-1 of the recipe name, not `hash()`, so a re-run reuses
  the image instead of rebuilding;
- a `.dockerignore` is written before the build, keeping `.git` and the local
  virtualenv out of the context;
- if BuildKit fails to resolve the base image (a network-shaped failure), the
  build is retried once with the legacy builder, which uses the local image
  store. Both attempts are recorded.

## Consistency audit families

| Parameter | Kind | Why it is worth comparing |
|---|---|---|
| learning_rate, batch_size, epochs, weight_decay, dropout | number | the usual suspects, compared with a 1% relative tolerance |
| optimizer | name | Adam vs AdamW changes the result |
| image_size | number | "we resize to 224" vs `image_size: 256` is a silent mismatch |
| f1_average | enum | macro-F1 and micro-F1 are different numbers with the same name |
| split | enum | a validation number compared against a test number is apples to oranges |
| norm_mean | tuple | per-channel normalisation mean shifts every input |

The code side only reads configuration files and config-like modules; values
outside a plausible range are discarded rather than reported.

## Repair policy

A run may be repaired twice, and only in these ways:

| Strategy | Trigger | Effect | Guard |
|---|---|---|---|
| `unpin` | `ENV_CONFLICT` naming `pkg==version` | drop the pin that no longer resolves | patch + backup kept beside the run |
| `mkdir` | `FileNotFoundError` naming a path | create the missing directory | only inside the checkout; never a parent above it |

Anything else stops. The checkout is restored after the attempts (`restore`), so
a repair leaves no untracked edit behind; the patch and its backup are evidence in
`repairs/`, not a new release. A repaired run gets its own `attempt-N/` directory
and its own status, and the report says explicitly that the numbers come from the
repaired attempt.

## Known weak points

| Area | Current behaviour | Fix direction |
|---|---|---|
| Claim extraction | tables need a metric column; GLUE-style tables fall back to a declared `target` | parse captions and column groups |
| Planning | only conventional README/entry-point layouts | LLM-assisted plan with human confirmation |
| Audit precision | only 6 parameter families, code side limited to config-like files | broader parameter vocabulary, AST-based defaults |
| Failure repair | classified, not repaired | bounded repair loop (Phase 2) |
| Multi-seed | single run | Phase 3 |
