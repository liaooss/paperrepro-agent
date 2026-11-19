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

## Known weak points

| Area | Current behaviour | Fix direction |
|---|---|---|
| Claim extraction | tables need a metric column; GLUE-style tables fall back to a declared `target` | parse captions and column groups |
| Planning | only conventional README/entry-point layouts | LLM-assisted plan with human confirmation |
| Audit precision | only 6 parameter families, code side limited to config-like files | broader parameter vocabulary, AST-based defaults |
| Failure repair | classified, not repaired | bounded repair loop (Phase 2) |
| Multi-seed | single run | Phase 3 |
