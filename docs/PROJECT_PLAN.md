# Project plan

PaperRepro: give it a paper and a code release; it reports whether the reported
results reproduce, and whether the paper is a defensible baseline.

Working name for the engine and CLI: `paperrepro`. Repository:
`paperrepro-agent`.

## What the project is

A reproduction agent with an evidence chain, not a paper summariser and not a
"run this repo" button. Every conclusion in a report must be reachable by
clicking through: paper location -> code location -> command -> log line ->
measured value -> comparison.

## Non-negotiable constraints

1. **No invented numbers.** A measured value exists only if a log line produced
   it. A paper value exists only if it was extracted from the paper text.
2. **Deterministic core.** The verdict, the comparison and the risk rules must
   produce identical output for identical inputs. Models may write prose and
   propose extraction; they may not decide outcomes.
3. **Execution is isolated and recorded.** No global installs, no caches outside
   the run directory, every command logged with exit code and duration.
4. **Honest failure modes.** "We could not run it" is a result, distinct from
   "we ran it and the numbers disagreed", distinct from "the authors never
   published the weights".
5. **No silent source changes.** Environment and path fixes are allowed and
   logged; changes to model or training logic are forbidden in a reproduction
   run and must become a named variant.

## Phases

| Phase | Goal | Exit criterion |
|---|---|---|
| 1 | Core reproduction engine | One real paper reproduced end to end, with committed evidence |
| 2 | Autonomous planning and repair | Plan inferred for a conventional repository; common failures repaired without a human |
| 3 | Evaluation system | Multi-seed runs, variance, consistency audit, viability report |
| 4 | Surfaces | CLI, MCP server, web UI over the same engine |
| 5 | Domains | Adapters for CV, NLP, time series, graphs, scientific ML - each with a real case |
| 6 | Release | Docs, benchmark suite, packaging, contribution guide |

Phase 1 is the only thing that matters until it is boringly reliable.

## Definition of done for Phase 1

Automated run, on a machine with a single consumer GPU, of:

```
paperrepro run <paper> --repo <release> --recipe <recipe>
```

producing a report that contains: the claim and its paper location; the
repository commit; the exact commands with exit codes; the measured value and
the log line that printed it; the delta against the paper with the tolerance
used; the five-state reproduction status; the consistency audit; and the
viability score with its five dimensions.

Two cases are required before Phase 1 is closed: one that reproduces and one
that does not, because a tool that has only ever seen success has never been
tested.

## Out of scope for now

- Judging scientific novelty. Reproduction cannot answer it; pretending otherwise
  is the main way a tool like this loses credibility.
- Full training of large models on this hardware (8 GB VRAM).
- Web UI before the engine is trustworthy.
- Nine autonomous agents. Three LLM call sites plus deterministic tools beat
  nine conversational agents on cost, latency and auditability.
