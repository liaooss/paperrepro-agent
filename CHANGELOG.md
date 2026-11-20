# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-11-20

Phase 2: the engine repairs what is safe to repair, and plans differently for
config-driven repositories.

### Added

- Bounded repair loop (`--no-repair` to disable): drops a dead `pkg==version`
  pin, or creates a missing directory inside the checkout. Two attempts maximum.
- Each repair keeps a `.diff` patch and a backup under `repairs/`, runs in its
  own `attempt-N/` directory, and restores the checkout afterwards.
- Report section **Repair attempts**, and the numbers are labelled as coming
  from the repaired attempt.
- Config-driven plan inference: an entry point taking `--config` is paired with
  the config the release ships, and beats the bare script candidate.

### Fixed

- `mkdir` repair created the missing *file* as a directory; it now creates the
  parent when the path has a suffix.
- Repair left the checkout modified; `restore` now reverts the patched files.

## [0.3.1] - 2026-11-19

The second case: a release that cannot be verified, and a report that says so
without turning it into a verdict about the paper.

### Added

- examples/cases/mimic3-benchmarks/ - MIMIC-III benchmarks, static verdict R1
  (credential-gated data) and executed status INSUFFICIENT_EVIDENCE
  (ENV_CONFLICT, 	ensorflow==1.15.0 unavailable on the current interpreter).
- paperrepro assess accepts paper URLs, matching 
un.

### Fixed

- Viability can no longer recommend a run that produced no measurement.
- RC05 recognises credential-gated data sources (PhysioNet, data use agreements).
- The report no longer claims "every parameter agrees" when none could be compared.
- Learning-rate parsing no longer accepts a bare integer.
## [0.3.0] - 2026-11-19

PaperRepro. The project is renamed and the engine learns to plan, audit and
grade.

### Changed

- **Breaking:** distribution, package and CLI renamed `reprocheck` -> `paperrepro`;
  repository renamed to `paperrepro-agent`. Environment variables are now
  `PAPERREPRO_*`.
- Repository scanning on a monorepo went from ~10 min to ~25 s: compiled alias
  patterns, a file cap, and a size limit for metric/dataset searches.

### Added

- `paperrepro run --auto`: derives an execution plan from README commands and
  entry points, rejects setup lines (`python -m venv`, `pytest`) and repository
  chores (`convert_*`, `check_*`), and raises `PlanError` rather than guessing.
  An inferred plan requires `--yes`.
- Consistency audit: six hyperparameter families compared between the paper and
  config-like files, quoting both sides, restricted to configuration; ranges
  outside plausibility are ignored.
- Five-state reproduction status (`REPRODUCED`, `PARTIALLY_REPRODUCED`,
  `NOT_REPRODUCED`, `BLOCKED`, `INSUFFICIENT_EVIDENCE`), independent of the
  viability score.
- Report sections for status, consistency audit and the plan that ran.
- Documentation set: PROJECT_PLAN, ARCHITECTURE, DECISIONS, DEVELOPMENT_LOG,
  TEST_REPORT, REPRODUCTION_REPORT.
- 15 new tests (140 total).

## [0.2.0] - 2026-11-19

Execution: paperrepro no longer only judges whether a release *could* be
reproduced, it runs it and reports what it measured.

### Added

- `paperrepro run PAPER --repo PATH|URL --recipe FILE` 鈥?acquire the release,
  build an isolated environment, execute a recipe, parse the metric, compare it
  with the paper, and score baseline viability.
- Execution backends: `local` (venv), `conda` (pinned Python), `docker`
  (per-recipe image, GPU passthrough optional).
- Recipe format (JSON/YAML) with install/data/eval commands, metric regex,
  tolerances, budget, timeout, harness scripts and a declared `target` claim.
- Metric extraction with explicit-regex precedence, JSON-line and generic
  fallbacks; fraction/percentage normalisation before comparison.
- Comparison statuses `MATCH` / `CLOSE` / `MISMATCH` / `NOT_RUN` with tolerances
  in percentage points.
- Five-dimension viability score (executability, fidelity, cost, comparability,
  openness) and a `use as a baseline` / `usable with conditions` / `do not use`
  recommendation.
- Failure taxonomy: `ENV_CONFLICT`, `MISSING_WEIGHTS`, `DATA_UNAVAILABLE`,
  `OOM`, `NETWORK`, `TIMEOUT`, `NO_METRIC_PARSED`, `COMMAND_FAILED`,
  `BACKEND_UNAVAILABLE` 鈥?each with the log line that proves it.
- Repository acquisition with a tarball fallback when `git clone` fails, and
  cache isolation (`HF_HOME`, `TORCH_HOME`, ...) inside the run directory.
- First executed case: DistilBERT / SST-2 鈥?91.3 reported, 91.06 measured,
  delta -0.24, `MATCH`, viability 4.3/5 (`examples/cases/distilbert-sst2`).
- 34 new tests (125 total).

## [0.1.0] - 2026-11-19

First public release.

### Added

- `paperrepro assess PAPER --repo PATH` 鈥?end-to-end audit producing `report.md`,
  `scorecard.json` and `reproduction_plan.md`.
- Paper ingest for LaTeX, Markdown, HTML and (with the `pdf` extra) PDF.
- Claim extraction from results tables (metric columns, baseline rows kept as
  context) and from results prose.
- Static repository scanner: entry points, manifests, configs, seeds, metric and
  dataset references, absolute paths, checkpoint references, incomplete markers.
- Claim-to-code alignment with four evidence levels (E1/E2/E3/X) and actionable gaps.
- 17 deterministic risk rules, including two author-dependent blockers that drive
  verdict R1.
- Graded verdicts R0鈥揜3 with a documented, testable confidence formula.
- Optional OpenAI-compatible LLM enrichment for the summary and dataset hints,
  with evidence-citation validation and on-disk caching.
- `--smoke` compile/entry-point check, `--fail-on` for CI gating, `--json` output.
- 91 unit and end-to-end tests with no third-party dependencies.
- A deliberately imperfect demo release under `examples/demo`.

[0.1.0]: https://github.com/liaooss/paperrepro-agent/releases/tag/v0.1.0
