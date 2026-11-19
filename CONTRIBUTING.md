# Contributing

Thanks for looking. The most valuable contribution to this project is **a release that fools it**: a (paper, code) pair where the verdict is wrong, with enough detail to see why.

## Ways to help

- **Report a false verdict.** Open an issue with the paper, the commit, the verdict you got, and the evidence that contradicts it.
- **Add a rule.** A new static check is ~20 lines and one test.
- **Improve recall on parsing.** LaTeX tables with merged cells, `\multirow`, spans; HTML from ar5iv; PDF layouts.
- **Add metric/dataset aliases** for your field. `textutil.METRIC_SYNONYMS` is a plain dict.

## Development setup

```bash
git clone https://github.com/liaooss/paperrepro-agent
cd paperrepro
python -m pip install -e .
python -m unittest discover -s tests -t tests -v
```

No third-party runtime dependencies, by design. If a change needs one, it belongs behind an optional extra.

## Adding a rule

1. Write a pure function in `src/paperrepro/risk/rules.py` that takes what it needs from `RepoScan` and returns `list[Finding]`. No network, no clock, no randomness.
2. Register it in `RULES` with `(id, title, severity)` and call it from `run_rules`.
3. Give it a test in `tests/test_rules.py` that builds the smallest repository that fires it, and one that proves it stays quiet on the demo release.
4. Document it in `docs/RUBRIC.md` 鈥?the rubric is normative and a rule that is not in it does not exist.

Severity is a promise: `blocker` means a reader cannot fix it, `major` means the release is materially incomplete, `minor` means friction, `info` means context.

## Changing the verdict logic

`docs/RUBRIC.md` and `verdict/score.py` must change in the same commit, plus `tests/test_score.py`. If a new outcome cannot be expressed by R0鈥揜3, argue for a new level first in an issue.

## Style

- Python 3.10+, `from __future__ import annotations`, type hints on public functions.
- Standard library only in `src/`.
- Tests use `unittest`; no fixtures beyond `tests/fixtures/` and `tests/helpers.py`.
- Every user-visible string should name a *thing* the reader can look up: a file, a line, a rule id.

## Pull requests

Small and focused. Include a test that fails before the change. Describe the behaviour change in terms of a report a user would read.

## Licence

By contributing you agree your work is released under the MIT licence.
