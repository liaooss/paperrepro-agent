# Development log

Newest first. Each entry records what changed, what broke, and what is next.

## 2026-11-20 - Phase 2: bounded repair and config-driven plans

**Done**

- `execute/repair.py`: two deterministic strategies, `unpin` (a `pkg==version`
  that no longer resolves) and `mkdir` (a directory the release expects).
  Anything else stops the loop.
- Repair is bounded to two attempts, writes the patch and a backup under
  `repairs/`, runs each attempt in its own `attempt-N/` directory, and restores
  the checkout afterwards so a repair cannot leave an untracked edit.
- The report has a **Repair attempts** table and states that the numbers come
  from the repaired attempt.
- Config-driven plan inference: `run.py` plus `--config configs/x.yaml` now
  beats a bare `run.py`, and a config-driven candidate displaces the plain
  entry-point candidate for the same file.
- 11 new tests (154 total), including an end-to-end repair that fails, creates a
  directory, and measures a metric on the second attempt.

**Broke and fixed**

- The first version of `mkdir` created the *file path* as a directory
  (`results/out.txt/`), so the retry failed again. It now creates the parent
  when the missing path carries a suffix.
- `restore` resolved the backup relative to the wrong root and left
  `requirements.txt` modified in the checkout. Caught by checking
  `git status` in the cloned repository after a repair run, which is now part of
  how the feature is verified by hand.

**Blocked**

- Docker remains unexercised: WSL2 has no distribution on this machine. The user
  chose to continue with the venv backend and install WSL2 later.

**Next**

- API-rename repair behind an explicit allow-list.
- A real case that reaches `BLOCKED` at runtime.

## 2026-11-19 - Phase 1 close-out: the failing case

**Done**

- Second case, chosen because it *cannot* be verified: MIMIC-III benchmarks.
  Static verdict **R1** (`RC05`, credential-gated PhysioNet data); executed
  attempt **INSUFFICIENT_EVIDENCE** (`ENV_CONFLICT`, `tensorflow==1.15.0` has no
  wheel for the current interpreter). Artifacts committed under
  `examples/cases/mimic3-benchmarks/`.
- `assess` now accepts paper URLs, like `run` does.
- `RC05` recognises credential-gated data (`physionet`, data use agreements,
  "acquire the data yourself"), which is what makes R1 correct here.
- Viability can no longer recommend a run that produced no measurement.
- The report distinguishes "every parameter agrees" from "no parameter could be
  compared"; the `Level` row is no longer hardcoded to L2.
- Learning-rate parsing rejects bare integers.

**Broke and fixed**

- The first version of the failing case reported "Every parameter the paper
  states agrees with the code" while zero parameters had a code value.
- It also recommended the paper "usable with conditions" at exactly 2.5/5 for a
  run that never measured anything. A run without a measurement is now always
  `do not use as a baseline yet`.
- The audit extracted `learning_rate = 1` from the phrase "learning rate and
  beta 1". Rates must now contain a decimal point or exponent.

**Blocked**

- Docker backend cannot be exercised: Docker Desktop is installed, but WSL2 has
  no distribution, so the Linux engine returns 500. Fixing this needs
  `wsl --install` with administrator rights and a reboot - a user action, not a
  code change. The `local` (venv) backend is the fallback and is what both cases
  used.

**Next**

- Phase 2: bounded repair loop for environment and path failures, plus plan
  inference for config-driven repositories.
- A real case that reaches `BLOCKED` (missing checkpoint at runtime).

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
