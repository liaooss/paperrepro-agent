# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-19

Execution: reprocheck no longer only judges whether a release *could* be
reproduced, it runs it and reports what it measured.

### Added

- `reprocheck run PAPER --repo PATH|URL --recipe FILE` — acquire the release,
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
  `BACKEND_UNAVAILABLE` — each with the log line that proves it.
- Repository acquisition with a tarball fallback when `git clone` fails, and
  cache isolation (`HF_HOME`, `TORCH_HOME`, ...) inside the run directory.
- First executed case: DistilBERT / SST-2 — 91.3 reported, 91.06 measured,
  delta -0.24, `MATCH`, viability 4.3/5 (`examples/cases/distilbert-sst2`).
- 34 new tests (125 total).

## [0.1.0] - 2026-11-19

First public release.

### Added

- `reprocheck assess PAPER --repo PATH` — end-to-end audit producing `report.md`,
  `scorecard.json` and `reproduction_plan.md`.
- Paper ingest for LaTeX, Markdown, HTML and (with the `pdf` extra) PDF.
- Claim extraction from results tables (metric columns, baseline rows kept as
  context) and from results prose.
- Static repository scanner: entry points, manifests, configs, seeds, metric and
  dataset references, absolute paths, checkpoint references, incomplete markers.
- Claim-to-code alignment with four evidence levels (E1/E2/E3/X) and actionable gaps.
- 17 deterministic risk rules, including two author-dependent blockers that drive
  verdict R1.
- Graded verdicts R0–R3 with a documented, testable confidence formula.
- Optional OpenAI-compatible LLM enrichment for the summary and dataset hints,
  with evidence-citation validation and on-disk caching.
- `--smoke` compile/entry-point check, `--fail-on` for CI gating, `--json` output.
- 91 unit and end-to-end tests with no third-party dependencies.
- A deliberately imperfect demo release under `examples/demo`.

[0.1.0]: https://github.com/liaooss/reprocheck/releases/tag/v0.1.0
