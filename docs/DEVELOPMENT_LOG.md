# Development log

Newest first. Each entry records what changed, what broke, and what is next.

## 2026-11-22 - Phase 3 complete: split and normalisation audit

**Done**

- `split`: compares the split the paper reports on with the `split=` the code
  configures, using the same spelling normalisation as the other enums.
- `norm_mean`: compares the per-channel normalisation triple, captured as three
  groups and compared component-wise, with a 0..1.5 plausibility guard so the
  word "mean" in ordinary prose does not produce a false positive.
- 4 new tests (183 total).
- Releases v0.3.0 through v0.8.0 created, with tags, so the CHANGELOG and GitHub
  finally agree.

**Why these two**

A validation number compared against a test number, and a different input
normalisation, both produce a plausible-looking number that is simply not the
same measurement. They were the last common causes we had no evidence for.

**Next**

- Phase 4: MCP server and a read-only web viewer over run directories.

## 2026-11-21 - Docker backend verified on a real case

**Done**

- WSL2 was installed by the user and Docker Desktop's Linux engine came up. The
  DistilBERT/SST-2 case then ran under `--backend docker` and produced
  **accuracy 0.9106 - identical to the venv backend** - in a 3.26 GB image,
  600 s cold (198 s of that was the build).
- Fixed three DockerBackend defects found by actually running it:
  `{pip}`/`{python}` placeholders were pasted into the Dockerfile unsubstituted;
  the image name used Python's salted `hash()` so every run rebuilt; and the
  build context included `.git` and the 1.7 GB venv, now excluded by a
  `.dockerignore` written for the build.
- Added a legacy-builder fallback: BuildKit resolves the base image over its own
  network stack, which failed here with `failed to fetch oauth token ... dial tcp
  [2a03:...]` while `docker pull` worked. On a registry-shaped failure the build
  is retried once with `DOCKER_BUILDKIT=0`.
- 2 new tests (179 total) for the deterministic image name and the
  registry-failure detector.

**Evidence**

`examples/cases/distilbert-sst2/result/docker_report.md` and
`docker_results.json`, next to the venv run of the same recipe.

## 2026-11-20 - Phase 3: the recommendation, with conditions

**Done**

- `execute/recommendation.py`: four outcomes only - `USE`,
  `USE_WITH_CONDITIONS`, `DO_NOT_USE`, `CANNOT_ASSESS` - each with the
  conditions attached and a cost note ("about N min per run; a 3-seed comparison
  costs ~X machine-hours").
- `CANNOT_ASSESS` is the default for `BLOCKED` and `INSUFFICIENT_EVIDENCE`: the
  tool makes no claim about a paper it could not measure.
- A reproduced number with a configuration mismatch in the audit becomes
  `USE_WITH_CONDITIONS`, naming the mismatched parameters rather than silently
  recommending the paper.
- The recommendation leads the report and appears in the console summary.
- 8 new tests (177 total).

**Evidence refreshed**

- DistilBERT/SST-2 -> "use as a baseline", 0.6 min per run.
- MIMIC-III -> "cannot be assessed", with the unblock condition quoted.

**Next**

- Dataset splits and normalisation constants in the audit.
- Docker still blocked on WSL2.

## 2026-11-20 - Phase 3: the audit learns preprocessing and metric definitions

**Done**

- Two new auditable families: `image_size` (crop/resize) and `f1_average`
  (macro / micro / weighted / binary). Both are quoted from the paper and the
  config with their locations.
- Enum comparison normalises spelling (`val`/`validation`, `train`/`training`)
  so a wording difference is not reported as a discrepancy.
- 4 new tests (169 total), including macro-in-paper versus micro-in-code.

**Why these two**

They are the two mismatches that produce a different number while every
hyperparameter looks identical: a 224 vs 256 crop, and macro vs micro F1. Both
are stated in prose, which is exactly where the extractor previously stopped.

**Next**

- Dataset splits and normalisation constants.
- Docker still blocked on WSL2 (fourth round).

## 2026-11-20 - Phase 3: multi-seed runs and spread

**Done**

- `execute/seeds.py`: a recipe with `seeds: [1, 2, 3]` repeats the evaluation
  (the seed goes into `{seed}` or is appended via `seed_flag`), aggregates mean
  and population standard deviation, and keeps every seed's artifacts under
  `seed-<n>/`.
- The report gains **Stability across seeds**: mean, std, runs, per-seed values,
  plus a sentence on whether the spread is small relative to the tolerance.
- On DistilBERT/SST-2 with seeds 1-3 the spread is 0.0000, which is the honest
  answer for a deterministic evaluation: the -0.24 delta is protocol, not
  sampling noise. Archived as `result/multiseed_report.md`.
- 6 new tests (165 total), including a failing seed that must not poison the
  others.

**Decisions**

- Multi-seed runs bypass the repair loop: a repaired environment that differs
  between seeds would make the spread meaningless.
- A single failed seed is kept in the denominator of `ok/total` but excluded from
  the mean; the report shows both numbers rather than hiding the loss.

**Next**

- Consistency audit for splits, preprocessing and metric definitions.
- Docker remains blocked on WSL2.

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
- `execute_recipe` only caught `BackendError` when *selecting* a backend; a
  backend that failed during `prepare()` (no daemon, no interpreter) escaped as
  a traceback. It now returns `status=error / BACKEND_UNAVAILABLE` with the
  actionable message, which is also how `--backend docker` behaves on a machine
  without WSL2.
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
