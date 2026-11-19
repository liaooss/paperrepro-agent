# reprocheck

**Give it a paper and the code that claims to implement it. It tells you whether the results can actually be reproduced — and shows its work.**

Every sentence in the output is anchored to a page, a table, or a `path:line`. No vibes, no "looks good to me".

```bash
pip install reprocheck
reprocheck assess paper.tex --repo ./code --smoke
```

```
verdict   R2  reproducible after engineering work  (confidence 0.41)
paper     examples/demo/paper.md
repo      examples/demo/code
claims    E2:1, E3:1, X:1
  major   RC02 Dependencies are not version-pinned
  major   RC03 Absolute filesystem paths in source
  major   RC13 Imports not declared in any manifest
```

---

## Why

Reading a paper tells you what the authors claim. Reading the repo tells you what they released. Neither tells you whether the two meet, and the gap between them is exactly where replication fails:

- the number in Table 2 has no code path that produces it,
- the evaluation script needs a checkpoint that was never published,
- the dataset must be requested by email,
- `requirements.txt` contains four unpinned packages,
- the metric is macro-F1 in the paper and micro-F1 in the code.

Existing tools answer adjacent questions. Reproducibility checklists record what authors *assert*. Linters judge code quality. Chat assistants produce a confident summary you cannot verify. `reprocheck` is built around one constraint: **a claim you cannot trace is not a finding.**

## What it does

```
paper (.tex/.md/.html/.pdf) ──┐
                              ├─► ingest ─► claims ─► align ─► rules ─► verdict
repo (any language) ──────────┘                │          │        │
                                              ▼          ▼        ▼
                                        claim ledger  findings  R0–R3 + confidence
```

1. **Extract claims** — every quantitative result becomes a ledger entry: metric, value, dataset, split, and the exact table row and column it came from. Baseline rows are kept as context, not counted as the paper's claims.
2. **Scan the repository** — entry points, dependency manifests, config files, seed handling, metric implementations, dataset loaders, absolute paths, checkpoint references, unfinished code.
3. **Align** — link each claim to code evidence: a metric definition anywhere in the repo beats an import; a literal copy of the reported number is the strongest signal of all.
4. **Apply rules** — 17 deterministic checks, no LLM, byte-for-byte reproducible between runs.
5. **Grade** — a verdict plus a per-claim evidence level, every gap phrased as an action.

## Verdicts

| Verdict | Meaning | Typical cause |
|---|---|---|
| **R3** | Directly reproducible | Every claim reached executable evidence |
| **R2** | Reproducible after engineering work | Unpinned deps, hard-coded paths, missing config — fixable without the authors |
| **R1** | Needs author-supplied assets | Checkpoints or data that only the authors can publish |
| **R0** | Not reproducible from this release | The paper's results have no counterpart in the code |

Per-claim evidence levels: **E1** executable, **E2** strong static, **E3** name-level match, **X** nothing found. See [docs/RUBRIC.md](docs/RUBRIC.md) for the exact decision procedure.

## Risk rules

`reprocheck rules` lists them all:

| ID | Severity | Check |
|---|---|---|
| RC01 | major | No dependency manifest |
| RC02 | major | Dependencies are not version-pinned |
| RC03 | major | Absolute filesystem paths in source |
| RC04 | blocker | Checkpoints referenced but not released |
| RC05 | blocker | Dataset requires manual or restricted acquisition |
| RC06 | minor | No random-seed control |
| RC07 | major | No executable entry point |
| RC08 | minor | README does not say how to install or run |
| RC09 | minor | No configuration file; hyperparameters hard-coded |
| RC10 | info | No tests |
| RC11 | minor | Incomplete code markers on the execution path |
| RC12 | minor | GPU requirement undocumented |
| RC13 | major | Imports not declared in any manifest |
| RC14 | major | Pipeline exists only as notebooks |
| RC15 | info | No licence file |
| RC16 | major | No README |
| RC17 | major | Paper claims with no code counterpart |

`RC04` and `RC05` are the only rules that can force **R1**: they describe assets a reader cannot obtain. Everything else is work a competent engineer can do, hence **R2**.

## What gets written

`reprocheck assess` writes three files into `--out` (default `reproduction-assessment/`):

- `report.md` — the human report: verdict, why, claim ledger, per-claim evidence, findings, next actions, limitations.
- `scorecard.json` — the same content as a stable schema (`reprocheck/scorecard/v1`) for CI, dashboards or meta-analysis.
- `reproduction_plan.md` — a checklist someone can actually work through, including the assets to request and the claims to check.

## Install

```bash
pip install reprocheck            # core, standard-library only
pip install "reprocheck[pdf]"     # optional: PDF papers
```

Python 3.10+. The analysis core has **zero runtime dependencies** on purpose: it must run in a bare CI container and on a reviewer's laptop with nothing installed.

## Usage

```bash
# one paper, one repo
reprocheck assess paper.tex --repo ./their-code --smoke

# CI gate: fail the job unless the release is at least R2
reprocheck assess paper.pdf --repo ./code --smoke --fail-on R2

# machine-readable only
reprocheck assess paper.md --repo ./code --json --no-llm

# what do the rule IDs mean?
reprocheck rules
```

`--smoke` compiles every Python file and requires an entry point to exist. It is the only way a claim can reach **E1**, and it never downloads data or trains anything.

## Optional LLM enrichment

Off by default unless configured. Any OpenAI-compatible endpoint works:

```bash
export REPROCHECK_BASE_URL=https://api.deepseek.com/v1
export REPROCHECK_API_KEY=...
export REPROCHECK_MODEL=deepseek-chat
```

With a model configured, reprocheck may write the executive summary and suggest a missing dataset. Both are constrained: the model only sees evidence identifiers that already exist, and a dataset suggestion is discarded unless the model cites evidence it was actually shown. Facts always come from the deterministic pipeline — a hallucinating model can make the prose worse, never the verdict wrong.

## Deliberate limits

- **Static.** No data downloaded, no weights fetched, no training run. E1 means "compiles and has an entry point", not "numbers match".
- **Tables and results prose.** A number stated only inside a figure is invisible.
- **Single-paper scope.** It audits one (paper, release) pair; it does not compare across papers or time.
- **No verdict on scientific validity.** A reproducible result can still be wrong; this tool only judges whether you *can* attempt the reproduction.

These are constraints, not omissions: each one is what makes the output trustworthy enough to cite.

## Development

```bash
git clone https://github.com/liaooss/reprocheck
cd reprocheck
python -m unittest discover -s tests -t tests   # 91 tests, no third-party deps
python -m reprocheck assess examples/demo/paper.md --repo examples/demo/code --smoke
```

The demo is a deliberately imperfect release: one claim that is well covered, one that is only name-matched, one that is missing entirely — which is what a real release looks like.

See [docs/DESIGN.md](docs/DESIGN.md) for the architecture and the trade-offs behind it.

## 中文简介

**输入一篇论文和一份代码，输出「能否复现」的分级结论，且每句话都能追溯到具体位置。**

- 论文侧抽取**结论台账**（指标、数值、数据集、表格行列定位），基线数字只作参照、不参与评级。
- 代码侧静态扫描入口、依赖、配置、随机种子、指标实现、数据加载、绝对路径、缺失权重。
- 两侧对齐后给出**每条结论的证据等级**（E1 可执行 / E2 强静态 / E3 弱匹配 / X 无对应），再汇总成 **R0–R3** 判定与置信度。
- 17 条确定性规则，同一份输入每次跑出的结论完全一致；LLM 只负责写摘要，且不许引入新事实。

```bash
reprocheck assess 论文.tex --repo ./代码 --smoke
```

局限同样明确：纯静态、不下载数据、不训练；只判断「有没有条件尝试复现」，不判断结论本身是否正确。

## Licence

MIT. See [LICENSE](LICENSE).
