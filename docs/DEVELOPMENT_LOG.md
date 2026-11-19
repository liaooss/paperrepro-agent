# Development log

Newest first. Each entry records what changed, what broke, and what is next.

## 2026-11-19 - Phase 1 engine: planning, audit, status

**Done**

- Renamed the project to PaperRepro: package `paperrepro`, CLI `paperrepro`,
  repository `paperrepro-agent`.
- `plan/infer.py`: derives a recipe from README commands and entry points,
  rejects setup lines (`python -m venv`, `pytest`) and repository chores
  (`convert_*`, `check_*`), and raises `PlanError` instead of guessing. The CLI
  requires `--yes` before executing an inferred plan.
- `audit/config_audit.py`: compares six hyperparameter families the paper states
  against config-like files in the repository, quoting both sides. Code-side
  matches are restricted to config files and config-like Python modules;
  documentation and ranges outside plausibility are ignored.
- `execute/status.py`: five-state verdict (`REPRODUCED`,
  `PARTIALLY_REPRODUCED`, `NOT_REPRODUCED`, `BLOCKED`,
  `INSUFFICIENT_EVIDENCE`), independent of the viability score.
- Reports now carry the status, the consistency audit and the plan that ran.
- 140 tests.

**Broke and fixed**

- First inference attempt on `huggingface/transformers` produced
  `python -m venv .my-env` as "the experiment". Root cause: README setup lines
  were treated as commands. Fixed by an explicit reject list plus a rule that
  an inferred entry point must look like train/eval/test.
- The audit initially read `docs/source/...` and reported six nonsense rows for
  the same repository. Fixed by restricting the code side to configuration.

**Next**

- Second case that fails honestly (a release without the assets it needs).
- Docker backend verification (daemon installed, not yet exercised).
- Multi-seed support.

## 2026-11-19 - Execution layer

**Done**

- Recipe format, three backends, command recording, metric extraction,
  comparison, viability scoring, failure taxonomy.
- First real case: DistilBERT on SST-2, 91.3 reported vs 91.06 measured,
  delta -0.24 points, `MATCH`, viability 4.3/5.
- 125 tests.

**Broke and fixed**

- `git clone` of a large repository died with `early EOF` and left a directory
  that looked present but had no working tree; the next step reported "not a
  Python project". Added working-tree validation and a codeload tarball fallback.
- Evaluation crashed with `PermissionError` writing to `~/.cache/huggingface`.
  All caches are now pinned inside the run directory, which is also what makes
  a run reproducible.
- DistilBERT's Table 2 puts datasets in the columns, so metric-column extraction
  found nothing. A recipe may now declare `target`, and must declare its paper
  location.

## 2026-11-19 - Static assessment (v0.1)

**Done**

- Paper ingest, claim ledger, repository scan, 17 deterministic rules, R0-R3
  verdict with per-claim evidence levels, Markdown/JSON/plan outputs.
- 91 tests, CI on two operating systems and three Python versions.

**Known at the time**

- The static verdict answers "could this be reproduced", not "did it". The
  execution layer was the missing half, and the roadmap said so.
