# IntentInsight

IntentInsight is an empirical software-engineering research project examining whether the structural impact implemented by a GitHub Pull Request aligns with the developer intent expressed in its title and description.

Developer intent is represented with transformer-based sentence embeddings. Implemented impact is represented from changed Python modules and structural-change information. Their cosine relationship is expressed as Intent–Impact Divergence:

```text
divergence = 1 - cosine_similarity(intent, structural_impact)
```

## Research questions

1. Can developer intent and implemented structural impact be represented consistently?
2. Does Intent–Impact Divergence capture meaningful semantic–structural characteristics?
3. Is the measure robust to historical reconstruction and structural-scope confounders?
4. Does divergence add predictive value for subsequent structural rework?

## Study population

The final analytical population contains 703 eligible Pull Requests from `pallets/flask`. All 703 have persisted semantic representations, structural representations, and divergence measurements.

The downstream 90-day analysis contains 702 fully observable Pull Requests:

- 531 with subsequent same-module structural rework;
- 171 without observed same-module structural rework;
- 1 right-censored observation excluded from the primary outcome analysis.

Structural rework means that a subsequent merged Pull Request modifies at least one Python module affected by the original Pull Request within 90 days of its merge.

## Main findings

- Observed mean intent–structure similarity: `0.307207`
- Random-pairing mean similarity: `0.241821`
- Permutation value from 10,000 permutations: approximately `0.0001`
- Historical Python module-profile equivalence: `703/703`
- Baseline downstream ROC-AUC: `0.564427`
- Baseline plus divergence ROC-AUC: `0.560606`
- Incremental ROC-AUC: `-0.003821`
- Bootstrap 95% confidence interval: `[-0.024571, +0.018007]`
- Paired permutation value: `0.72962704`

The study therefore finds non-random semantic–structural alignment, while detecting no incremental predictive benefit from divergence for the selected 90-day outcome.

## Repository structure

```text
src/intentinsight/   Authoritative Python package
tests/               Unit and integration tests
scripts/             Dataset, validation and experiment scripts
results/             Generated research artifacts (not tracked by default)
datasets/            External or generated datasets (not tracked by default)
docs/                Supporting project documentation
app.py               Streamlit launcher
```

The authoritative dashboard implementation is under `src/intentinsight/presentation/dashboard/`.

## Requirements

- Python `>=3.12,<3.13`
- A local copy of `intentinsight.db` for the read-only Research Workbench
- A GitHub token only for collection or external integration operations

## Installation

Create and activate a virtual environment on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,research]"
```

Copy `.env.example` to `.env` only when environment configuration is required:

```powershell
Copy-Item .env.example .env
```

Never commit `.env` or a real access token.

## Launch the Research Workbench

Place `intentinsight.db` in the repository root, then run:

```powershell
python -m streamlit run src/intentinsight/presentation/dashboard/app.py
```

The Workbench reads persisted database records and committed research artifacts. It does not rerun the empirical experiments during normal use.

## Validation and tests

Run the offline test suite:

```powershell
python -m pytest -q
```

Final verified result on 16 August 2026:

```text
75 passed
```

Validate database completeness:

```powershell
python check_database.py
```

Expected result:

```text
Missing research records: 0
```

Integration tests that access GitHub may require `GITHUB_TOKEN` and network access.

## Data and artifacts

`.env`, local SQLite databases, generated results, and raw datasets are ignored by Git. The coursework submission bundle may include the validated database and selected result artifacts when permitted by the submission and data-availability requirements.

The project analyses public repository data that can remain attributable to GitHub contributors. Reuse or redistribution should follow the relevant platform terms, research-ethics requirements, and institutional policy.

## Project status

The research implementation, empirical evaluation, Research Workbench, database completeness check, and 75-test offline suite are complete.

