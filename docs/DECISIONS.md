# Decisions

Short records of choices that would be expensive to reverse. Each one names the
alternative that was rejected and why.

## D1 - Static assessment first, execution second

**Decision.** Ship a static, evidence-only assessment (v0.1) before any code is
executed; add execution as a second layer (v0.2).

**Rejected.** Building an execution engine first.

**Why.** A reproduction attempt costs minutes to hours and fails for mundane
reasons; a 20-second static pass tells the analyst whether the attempt is worth
starting. It also produced the claim ledger and evidence pointers that the
execution layer now consumes unchanged.

**Cost.** Two releases before the product could answer the actual question.

## D2 - Deterministic core, model at the edge

**Decision.** Rules, comparison, status and scoring are pure functions. The LLM
may write the executive summary and propose a missing dataset, and a proposal is
discarded unless it cites evidence it was shown.

**Rejected.** Agent-driven verdicts.

**Why.** Two audits of one commit must agree. A verdict produced by a sampler is
not reproducible, which is a strange property for a reproducibility tool.

**Cost.** Recall: a rule cannot recognise a novel failure mode.

## D3 - The recipe is the only executable unit

**Decision.** Nothing runs unless it came from a `Recipe`: install commands, data
commands, one eval command, a metric pattern, tolerances, budget.

**Rejected.** Letting a model write a shell command and executing it.

**Why.** A recipe is reviewable before execution, diffable between runs, and
serialisable into the report. An inferred recipe requires `--yes`; a curated one
does not.

**Cost.** Some repositories need a hand-written recipe, which is the honest state
of the art.

## D4 - Three model call sites, not nine agents

**Decision.** Paper extraction, explanation of unseen failures, and report prose.
Everything else is deterministic tooling.

**Rejected.** The nine-agent architecture.

**Why.** Every agent hand-off is a place where evidence is paraphrased or dropped,
and nine conversational agents multiply latency and cost while making the output
less reproducible. The state machine and artifacts that an agent framework would
provide already exist as files.

**Cost.** Less "autonomous" prose in intermediate steps. The report is unaffected.

## D5 - Files and SQLite before queues and object stores

**Decision.** A run is a directory: JSON manifest, JSONL command log, raw logs.
No Postgres, Redis, Celery, MinIO or MLflow in Phase 1.

**Rejected.** The full service stack.

**Why.** Hundreds of runs fit comfortably on disk, and a directory can be zipped,
diffed, attached to an issue and replayed. The storage boundary is a module, so
swapping the backend later is a day, not a redesign.

**Cost.** No concurrent task queue; parallelism is process-level.

## D6 - Reproduction status and baseline viability are separate

**Decision.** Five states (`REPRODUCED`, `PARTIALLY_REPRODUCED`,
`NOT_REPRODUCED`, `BLOCKED`, `INSUFFICIENT_EVIDENCE`) plus a five-dimension
viability score. Neither implies the other.

**Rejected.** A single score from 0 to 100.

**Why.** "We could not obtain the weights" and "we obtained them and the numbers
are wrong" are different findings with different remedies. Collapsing them into a
number loses exactly the information the analyst needs.

**Cost.** Two things to explain in the report.

## D7 - Caches live inside the run directory

**Decision.** `HF_HOME`, `HF_HUB_CACHE`, `TORCH_HOME`, `MPLCONFIGDIR` are pinned
under the run directory for every backend.

**Why.** It started as a bug fix (`PermissionError` on `~/.cache/huggingface` in
a sandboxed workspace) and turned out to be the correct default: a run that
depends on a pre-existing cache cannot be audited or replayed elsewhere.

**Cost.** Each run re-downloads weights unless the directory is reused.

## D8 - Tarball fallback for repository acquisition

**Decision.** If `git clone` fails or leaves an incomplete working tree, download
`codeload.github.com/<owner>/<repo>/tar.gz/<ref>` and record `tarball:<ref>` as
the provenance.

**Why.** Large clones fail on real networks with `early EOF`, and an interrupted
clone leaves a directory that exists but has no files - the worst kind of
failure, because it surfaces three steps later.

**Cost.** No commit hash in that case; the report states the ref instead.

## D9 - A declared target beats a guessed claim

**Decision.** When the paper's table cannot be parsed (datasets in columns), a
recipe may declare `target` - but must also declare the paper location it came
from, which the report prints next to the delta.

**Rejected.** Letting the model guess which number is being checked.

**Why.** The comparison is only meaningful if the target is anchored. A guessed
target produces a confident, wrong report.

**Cost.** Hand-written recipes for GLUE-style tables until caption parsing lands.

## D10 - Naming

**Decision.** Product: PaperRepro. Repository: `paperrepro-agent`. Python package
and CLI: `paperrepro`.

**Why.** The repository name describes what it is (an agent for reproduction); the
package name stays short because it is typed constantly. A distribution named
`paperrepro-agent` with an import called `paperrepro` is a needless mismatch.
