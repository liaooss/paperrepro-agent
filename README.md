# PaperRepro

[![CI](https://github.com/liaooss/paperrepro-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/liaooss/paperrepro-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**Give it a paper and the code that claims to implement it. It runs the release, compares what it measured with what the paper reports, and tells you whether the paper is defensible as a baseline — with every number traceable to a log line.**

```bash
paperrepro run paper.tex --repo https://github.com/author/release --recipe recipe.json
```

```
status    REPRODUCED  all 1 compared claim(s) match within tolerance
metrics   accuracy=0.9106
claims    MATCH:1
viability 4.3/5  use as a baseline
audit     6 parameter(s) checked, 1 mismatch(es)
```

---

## The chain this project exists to build

```
paper claim  ->  code location  ->  command that ran  ->  log line
             ->  measured value  ->  delta  ->  status  ->  recommendation
```

Every arrow is openable. A report that cannot be walked backwards is a press
release, not an audit.

## Two halves

**Static assessment** (`paperrepro assess`) reads a paper and a checkout without
executing anything, and answers *is this even worth attempting*: claim ledger,
17 deterministic risk rules, per-claim evidence levels (E1/E2/E3/X), verdict
R0–R3. Seconds, zero dependencies, works on a laptop.

**Execution** (`paperrepro run`) answers *did it actually reproduce*: isolated
environment, real commands, parsed metrics, comparison against the paper,
five-state status, consistency audit, viability score.

## Quickstart

```bash
git clone https://github.com/liaooss/paperrepro-agent
cd paperrepro-agent
pip install -e .            # standard library only; no third-party runtime deps
```

```bash
# static: should this be reproduced at all?
paperrepro assess examples/demo/paper.md --repo examples/demo/code --smoke

# execution: a curated plan, real numbers
paperrepro run https://ar5iv.labs.arxiv.org/html/1910.01108 \
  --repo https://github.com/huggingface/transformers \
  --recipe examples/cases/distilbert-sst2/recipe.json

# execution: infer the plan, review it, then confirm
paperrepro run https://arxiv.org/abs/2010.01412 --repo https://github.com/google-research/sam --auto --plan-only
paperrepro run https://arxiv.org/abs/2010.01412 --repo https://github.com/google-research/sam --auto --yes
```

## What a run produces

| File | Content |
|---|---|
| `run_report.md` | status, claim comparison, consistency audit, command log, viability, limits |
| `results.json` | the same as a stable schema (`paperrepro/run/v1`) |
| `artifacts/*.log` | the raw output of every command, with exit code and duration |
| `commands.jsonl` | one line per command, for diffing two runs |

## Reproduction status

| Status | Meaning |
|---|---|
| **REPRODUCED** | every compared claim matches within tolerance |
| **PARTIALLY_REPRODUCED** | some match, some do not |
| **NOT_REPRODUCED** | nothing matches |
| **BLOCKED** | a missing asset only the authors can supply (weights, gated data) |
| **INSUFFICIENT_EVIDENCE** | the run produced no comparable measurement |

Deliberately separate from the **viability** score (executability, fidelity,
cost, comparability, openness → *use as a baseline* / *usable with conditions* /
*do not use*). "We could not run it" is not "the numbers are wrong".

## Consistency audit

The report compares what the paper states with what the code configures, quoting
both sides:

| Parameter | Paper says | Code says | Result |
|---|---|---|---|
| batch_size | 64 | 32 | MISMATCH |
| learning_rate | 1e-3 | 0.001 | MATCH |

A mismatch is a question for the authors — a stale README, a different experiment
in the same repository, or a real discrepancy.

## First case

**DistilBERT / SST-2** — paper says 91.3 (Table 2), measured **91.06**,
delta **-0.24 points**, status **REPRODUCED**, viability **4.3/5**.

A second case fails honestly and says why: MIMIC-III benchmarks cannot be
verified at all — credential-gated PhysioNet data, plus a 	ensorflow==1.15.0
pin that has no wheel on a current interpreter. The static verdict is R1, the
executed status is `INSUFFICIENT_EVIDENCE`, and the recommendation is *do not
use as a baseline yet*. Failure is reported as a finding, not as a verdict on
the paper: [`examples/cases/mimic3-benchmarks`](examples/cases/mimic3-benchmarks/README.md).

Full report, including the three things that broke before the number appeared:
[`examples/cases/distilbert-sst2`](examples/cases/distilbert-sst2/README.md) ·
[`docs/REPRODUCTION_REPORT.md`](docs/REPRODUCTION_REPORT.md).

## Failure taxonomy

A run that fails says *how*: `ENV_CONFLICT`, `MISSING_WEIGHTS`,
`DATA_UNAVAILABLE`, `OOM`, `NETWORK`, `TIMEOUT`, `NO_METRIC_PARSED`,
`COMMAND_FAILED`, `BACKEND_UNAVAILABLE`. Each maps to a different remedy, and
the report quotes the log line that proves it.

## Optional LLM enrichment

Off unless configured. Any OpenAI-compatible endpoint:

```bash
export PAPERREPRO_BASE_URL=https://api.deepseek.com/v1
export PAPERREPRO_API_KEY=...
export PAPERREPRO_MODEL=deepseek-chat
```

The model may rewrite the summary and propose a missing dataset label; a
proposal is discarded unless it cites evidence it was shown. Facts come from the
deterministic pipeline.

## Deliberate limits

- **One machine, one seed.** A match is evidence, not proof.
- **Protocol equality is not verified automatically.** Split and preprocessing
  are checked by hand, and the comparability dimension says so.
- **No novelty judgement.** Reproduction cannot answer whether a method is
  interesting; pretending otherwise is how a tool like this loses credibility.
- **Planning is conservative.** On a large library with no experiment-shaped
  entry point, inference refuses and asks for a recipe.

## Documentation

| | |
|---|---|
| [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) | goals, constraints, phase exit criteria |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | layers, module map, data flow |
| [docs/RUBRIC.md](docs/RUBRIC.md) | normative evidence levels and verdicts |
| [docs/DECISIONS.md](docs/DECISIONS.md) | choices that would be expensive to reverse |
| [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md) | what changed, what broke |
| [docs/TEST_REPORT.md](docs/TEST_REPORT.md) | 140 tests, coverage and gaps |
| [docs/ROADMAP.md](docs/ROADMAP.md) | phases and status |
| [docs/REPRODUCTION_REPORT.md](docs/REPRODUCTION_REPORT.md) | the first executed case |

## 中文简介

**输入一篇论文和一份代码，输出「能不能复现」以及「值不值得当基线」，每个数字都能追到日志行。**

- 静态层：论文抽取结论台账 → 代码扫描 → 17 条确定性规则 → R0–R3 判定，秒级完成、零依赖。
- 执行层：recipe → 隔离环境 → 真实命令 → 指标解析 → 与原文比对 → 五态结论（REPRODUCED / PARTIALLY / NOT / BLOCKED / INSUFFICIENT）+ 五维基线可行性。
- 一致性审计：论文写的超参 vs 代码里的配置，两边都引用出处。
- 首个真实案例：DistilBERT / SST-2，论文 91.3，实测 91.06，差 −0.24 点，判定 REPRODUCED。

明确不做：不判断论文创新性，不做「一键跑一切」，推断出的计划必须人工确认后再执行。

## Licence

MIT. See [LICENSE](LICENSE).
