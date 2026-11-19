# Reproducibility assessment — [1703.07771] Multitask learning and benchmarking with clinical time series data

> **Verdict: R1 — needs author-supplied assets**  
> Confidence: 0.38 · claims examined: 1 (+25 baseline numbers)

Verdict R1 (needs author-supplied assets): 1 quantitative claim(s) from the paper were checked against the code. Top blocker: RC05 dataset requires manual or restricted acquisition. 2 major issue(s) remain, starting with RC02 dependencies are not version-pinned. 1 claim(s) still need execution before any number can be called reproduced.

| | |
|---|---|
| Paper | `C:\Users\l\AppData\Local\Temp\paperrepro-paper-2jc8m75x\paper.html` (html, 10 table(s)) |
| Repository | `E:\Projects\new-project\.scratch\mimic3` — 101 files, python:66, other:22, docs:9, config:3 |
| Generated | 2026-11-19T10:52:13+00:00 |
| Tool | paperrepro 0.3.0 · rules-only (no LLM) |

## Why this verdict

- Missing assets that only the authors can supply: RC05 dataset requires manual or restricted acquisition
- 1 claim(s) rest on name-level matches only.
- Smoke check was not run (--smoke), so no claim can reach E1.

## Claim ledger

| ID | Claim | Reported | Dataset | Evidence | Strongest code evidence |
|----|-------|----------|---------|----------|-------------------------|
| C01 | AUC | 0.91 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C02 | AUC-ROC _(baseline)_ | 0.043 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C03 | AUC-ROC _(baseline)_ | 0.057 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C04 | AUC-ROC _(baseline)_ | 0.066 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C05 | AUC-ROC _(baseline)_ | 0.071 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C06 | AUC-ROC _(baseline)_ | 0.079 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C07 | AUC-ROC _(baseline)_ | 0.082 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C08 | AUC-ROC _(baseline)_ | 0.089 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C09 | AUC-ROC _(baseline)_ | 0.091 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C10 | AUC-ROC _(baseline)_ | 0.094 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C11 | AUC-ROC _(baseline)_ | 0.108 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C12 | AUC-ROC _(baseline)_ | 0.126 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C13 | AUC-ROC _(baseline)_ | 0.130 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C14 | AUC-ROC _(baseline)_ | 0.132 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C15 | AUC-ROC _(baseline)_ | 0.135 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C16 | AUC-ROC _(baseline)_ | 0.139 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C17 | AUC-ROC _(baseline)_ | 0.177 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C18 | AUC-ROC _(baseline)_ | 0.192 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C19 | AUC-ROC _(baseline)_ | 0.212 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C20 | AUC-ROC _(baseline)_ | 0.213 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C21 | AUC-ROC _(baseline)_ | 0.265 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C22 | AUC-ROC _(baseline)_ | 0.268 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C23 | AUC-ROC _(baseline)_ | 0.289 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C24 | AUC-ROC _(baseline)_ | 0.323 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C25 | AUC-ROC _(baseline)_ | 0.331 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |
| C26 | AUC-ROC _(baseline)_ | 0.423 | — | E3 | `mimic3benchmark/evaluation/evaluate_decomp.py:27` |

## Claim detail

### C01 · AUC = 0.91 · `E3`

- **Paper:** `Decompensation prediction (prose)` — "This figure shows that even a model with 0.91 AUC-ROC can make trivial mistakes and there is a lot of room for improvement."
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.91 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect
- **Note:** Extracted from prose, not from a table; verify the surrounding protocol.

### C02 · AUC-ROC = 0.043 · `E3`

- **Paper:** `Table 2 / row 'Other upper respiratory disease' / column 'AUC-ROC'` — "Other upper respiratory disease: AUC-ROC = 0.043"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.043 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C03 · AUC-ROC = 0.057 · `E3`

- **Paper:** `Table 2 / row 'Other lower respiratory disease' / column 'AUC-ROC'` — "Other lower respiratory disease: AUC-ROC = 0.057"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.057 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C04 · AUC-ROC = 0.066 · `E3`

- **Paper:** `Table 2 / row 'Acute cerebrovascular disease' / column 'AUC-ROC'` — "Acute cerebrovascular disease: AUC-ROC = 0.066"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.066 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C05 · AUC-ROC = 0.071 · `E3`

- **Paper:** `Table 2 / row 'Conduction disorders' / column 'AUC-ROC'` — "Conduction disorders: AUC-ROC = 0.071"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.071 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C06 · AUC-ROC = 0.079 · `E3`

- **Paper:** `Table 2 / row 'Gastrointestinal hemorrhage' / column 'AUC-ROC'` — "Gastrointestinal hemorrhage: AUC-ROC = 0.079"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.079 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C07 · AUC-ROC = 0.082 · `E3`

- **Paper:** `Table 2 / row 'Shock' / column 'AUC-ROC'` — "Shock: AUC-ROC = 0.082"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.082 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C08 · AUC-ROC = 0.089 · `E3`

- **Paper:** `Table 2 / row 'Other liver diseases' / column 'AUC-ROC'` — "Other liver diseases: AUC-ROC = 0.089"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.089 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C09 · AUC-ROC = 0.091 · `E3`

- **Paper:** `Table 2 / row 'Pleurisy; pneumothorax; pulmonary collapse' / column 'AUC-ROC'` — "Pleurisy; pneumothorax; pulmonary collapse: AUC-ROC = 0.091"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.091 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C10 · AUC-ROC = 0.094 · `E3`

- **Paper:** `Table 2 / row 'Diabetes mellitus with complications' / column 'AUC-ROC'` — "Diabetes mellitus with complications: AUC-ROC = 0.094"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.094 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C11 · AUC-ROC = 0.108 · `E3`

- **Paper:** `Table 2 / row 'Acute myocardial infarction' / column 'AUC-ROC'` — "Acute myocardial infarction: AUC-ROC = 0.108"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.108 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C12 · AUC-ROC = 0.126 · `E3`

- **Paper:** `Table 2 / row 'Chronic obstructive pulmonary disease' / column 'AUC-ROC'` — "Chronic obstructive pulmonary disease: AUC-ROC = 0.126"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.126 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C13 · AUC-ROC = 0.130 · `E3`

- **Paper:** `Table 2 / row 'Hypertension with complications' / column 'AUC-ROC'` — "Hypertension with complications: AUC-ROC = 0.130"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.130 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C14 · AUC-ROC = 0.132 · `E3`

- **Paper:** `Table 2 / row 'Chronic kidney disease' / column 'AUC-ROC'` — "Chronic kidney disease: AUC-ROC = 0.132"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.132 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C15 · AUC-ROC = 0.135 · `E3`

- **Paper:** `Table 2 / row 'Pneumonia' / column 'AUC-ROC'` — "Pneumonia: AUC-ROC = 0.135"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.135 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C16 · AUC-ROC = 0.139 · `E3`

- **Paper:** `Table 2 / row 'Septicemia (except in labor)' / column 'AUC-ROC'` — "Septicemia (except in labor): AUC-ROC = 0.139"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.139 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C17 · AUC-ROC = 0.177 · `E3`

- **Paper:** `Table 2 / row 'Respiratory failure; insufficiency; arrest' / column 'AUC-ROC'` — "Respiratory failure; insufficiency; arrest: AUC-ROC = 0.177"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.177 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C18 · AUC-ROC = 0.192 · `E3`

- **Paper:** `Table 2 / row 'Diabetes mellitus without complication' / column 'AUC-ROC'` — "Diabetes mellitus without complication: AUC-ROC = 0.192"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.192 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C19 · AUC-ROC = 0.212 · `E3`

- **Paper:** `Table 2 / row 'Acute and unspecified renal failure' / column 'AUC-ROC'` — "Acute and unspecified renal failure: AUC-ROC = 0.212"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.212 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C20 · AUC-ROC = 0.213 · `E3`

- **Paper:** `Table 2 / row 'Complications of surgical/medical care' / column 'AUC-ROC'` — "Complications of surgical/medical care: AUC-ROC = 0.213"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.213 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C21 · AUC-ROC = 0.265 · `E3`

- **Paper:** `Table 2 / row 'Fluid and electrolyte disorders' / column 'AUC-ROC'` — "Fluid and electrolyte disorders: AUC-ROC = 0.265"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.265 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C22 · AUC-ROC = 0.268 · `E3`

- **Paper:** `Table 2 / row 'Congestive heart failure; nonhypertensive' / column 'AUC-ROC'` — "Congestive heart failure; nonhypertensive: AUC-ROC = 0.268"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.268 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C23 · AUC-ROC = 0.289 · `E3`

- **Paper:** `Table 2 / row 'Disorders of lipid metabolism' / column 'AUC-ROC'` — "Disorders of lipid metabolism: AUC-ROC = 0.289"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.289 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C24 · AUC-ROC = 0.323 · `E3`

- **Paper:** `Table 2 / row 'Cardiac dysrhythmias' / column 'AUC-ROC'` — "Cardiac dysrhythmias: AUC-ROC = 0.323"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.323 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C25 · AUC-ROC = 0.331 · `E3`

- **Paper:** `Table 2 / row 'Coronary atherosclerosis and related' / column 'AUC-ROC'` — "Coronary atherosclerosis and related: AUC-ROC = 0.331"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.331 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

### C26 · AUC-ROC = 0.423 · `E3`

- **Paper:** `Table 2 / row 'Essential hypertension' / column 'AUC-ROC'` — "Essential hypertension: AUC-ROC = 0.423"
- **Code:**
  - `mimic3benchmark/evaluation/evaluate_decomp.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
  - `mimic3benchmark/evaluation/evaluate_ihm.py:27` — `metrics = [('AUC of ROC', 'auroc'),`
- **Gaps:**
  - the reported value 0.423 appears nowhere in the code or result files
  - the link between this implementation and the reported number is indirect

## Risk findings

### Blockers (1)

#### RC05 · Dataset requires manual or restricted acquisition

The README mentions 'physionet'. Data that must be requested, registered for or downloaded by hand cannot be part of an automated reproduction, and may not be redistributable.

_Only the authors can resolve this._
- `README.md:41` — `Here we present four public benchmarks for machine learning researchers interested in health care, built using data from the publicly available Medical Information Mart for Intensi`

### Major issues (2)

#### RC02 · Dependencies are not version-pinned

1 requirement(s) carry no version constraint, so a fresh install can resolve to versions the authors never tested. Example: tqdm
- `requirements.txt` — `tqdm`

#### RC13 · Imports not declared in any manifest

2 module(s) are imported but absent from every dependency file (imp, scipy). A clean environment will fail at import time.
- `mimic3models/feature_extractor.py:2` — `from scipy.stats import skew`
- `mimic3models/decompensation/main.py:4` — `import imp`

### Minor issues (1)

#### RC11 · Incomplete code markers on the execution path

1 TODO/FIXME/NotImplementedError marker(s) remain in the code; any of them may sit on the path that produces the reported numbers.
- `mimic3benchmark/scripts/validate_events.py:50` — `# TODO: maybe we can recover HADM_ID by looking at ICUSTAY_ID`

## What to do next

1. [RC05] Dataset requires manual or restricted acquisition — README.md:41
2. [RC02] Dependencies are not version-pinned — requirements.txt
3. [RC13] Imports not declared in any manifest — mimic3models/feature_extractor.py:2
4. Run again with --smoke to compile-check the code and allow claims to reach E1.

## Reproduce this assessment

```bash
paperrepro assess C:\Users\l\AppData\Local\Temp\paperrepro-paper-2jc8m75x\paper.html --repo E:\Projects\new-project\.scratch\mimic3
```

## Limits of this report

- The analysis is static: no dependency was installed, no dataset downloaded, no model trained. E1 requires `--smoke`; without it the ceiling is E2.
- Claim extraction reads tables and results prose. A number stated only in a figure is invisible to it.
- A reproduced number can still differ for statistical reasons (seeds, hardware); this report judges whether the *evidence to attempt* a reproduction exists, not whether a re-run will land within 0.1.
