# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
