# Test report

Last run: 2026-11-19, local Windows 11 / Python 3.14.8, and GitHub Actions
(Ubuntu + Windows, Python 3.10 / 3.12 / 3.13).

## Summary

```
Ran 140 tests in ~21s
OK
```

No network, no GPU and no external service is required for the suite. Tests that
need an interpreter create a throw-away virtualenv.

## Coverage by area

| Area | Tests | What is pinned |
|---|---|---|
| Text and metric vocabulary | 12 | header -> canonical metric, aliases, number parsing, word boundaries |
| Paper ingest | 9 | LaTeX tables and sections, Markdown tables, HTML headings/tables, error paths |
| Claim extraction | 8 | table claims, roles (paper vs baseline), dataset from caption, prose claims, de-duplication |
| Repository scan | 11 | entry points, manifests, readme, seeds, absolute paths, checkpoint references, notebook-only |
| Claim alignment | 6 | E1/E2/E3/X decisions, actionable gaps, literal-value evidence |
| Risk rules | 12 | catalogue integrity, individual rules, no false blockers on the demo release |
| Static verdict | 8 | R0-R3 mapping, author-dependent blockers, confidence bounds |
| Report rendering | 8 | sections present, evidence pointers, JSON schema, plan checkboxes |
| CLI | 11 | exit codes, three output files, `--fail-on`, `--json`, `--quiet`, error paths |
| Recipe | 7 | validation, defaults, shipped recipe |
| Execution runner | 8 | command recording, log paths, failure classification, no-metric-is-a-failure |
| Metric parsing | 6 | regex precedence, JSON lines, generic scan, percent conversion |
| Comparison | 9 | fraction/point normalisation, MATCH/CLOSE/MISMATCH/NOT_RUN, alias metrics |
| Viability | 6 | dimension completeness, penalties, missing-asset verdict |
| Planning | 4 | README command chosen, setup lines rejected, converter scripts rejected, metric from paper |
| Consistency audit | 5 | match, mismatch with both sides, scientific notation, paper-only, code-only |
| Reproduction status | 6 | five states and their boundaries |

## Not covered

| Gap | Why | Consequence |
|---|---|---|
| Docker success path | no daemon in CI and no WSL2 on the dev machine | implemented, unexecuted |
| Docker failure path | covered | `tests/test_backends.py` pins the actionable message for a missing CLI, an unreachable daemon, and `status=error / BACKEND_UNAVAILABLE` from the runner |
| GPU execution | no GPU in CI | CUDA code paths untested |
| Real-network acquisition | CI is offline by design | tarball fallback tested only manually |
| LLM enrichment | needs a key | client tested for degradation and JSON robustness only |

## Reproduce

```bash
python -m unittest discover -s tests -t tests -v
```

CI additionally runs the demo end to end and fails the job below verdict R2:

```bash
python -m paperrepro assess examples/demo/paper.md --repo examples/demo/code --smoke --fail-on R1
```
