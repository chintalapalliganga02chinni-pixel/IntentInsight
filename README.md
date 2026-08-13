***# IntentInsight***



***## Semantic–Structural Divergence in Pull Requests***



***IntentInsight is an empirical Software Engineering research project investigating whether the structural impact of a Pull Request is aligned with the intent expressed in its title and description.***



***Developer intent is represented using transformer-based sentence embeddings. Implemented impact is represented using structural information extracted from changed Python modules. These representations are compared using an Intent–Impact Divergence measure.***



***## Research Questions***



***1. Can developer intent and implemented structural impact be represented consistently?***

***2. Does Intent–Impact Divergence capture meaningful semantic–structural characteristics of Pull Requests?***

***3. Is the divergence measure robust to historical reconstruction and structural-scope confounders?***

***4. Does Intent–Impact Divergence provide incremental predictive value for subsequent structural rework?***



***## Dataset***



***The main analysis contains 703 eligible Pull Requests with 703 semantic representations, 703 structural representations, and 703 divergence measurements.***



***The downstream 90-day analysis contains 702 fully observable Pull Requests:***



***- 531 with subsequent same-module structural rework***

***- 171 without observed same-module structural rework***

***- 1 right-censored observation excluded from the primary outcome analysis***



***Structural rework is defined as a subsequent merged Pull Request, within 90 days of the original merge, modifying at least one Python module affected by the original Pull Request.***



***## Method***



***The pipeline represents:***



***- developer intent using transformer-based sentence embeddings***

***- implemented impact using Python module and structural-change information***

***- semantic–structural mismatch using Intent–Impact Divergence***



***The empirical evaluation includes historical reconstruction, structural-scope analysis, robustness testing, random controls, statistical inference, and downstream predictive evaluation.***



***## Validation***



***Historical Python structural reconstruction achieved exact module-profile equivalence for all 703 analysed Pull Requests.***



***The study also evaluates:***



***- full versus Python-only divergence***

***- structural-scope confounding***

***- bootstrap confidence intervals***

***- permutation tests***

***- random structural controls***

***- chronological predictive evaluation***

***- 90-day structural rework***



***## Predictive Finding***



***A chronological train/test evaluation was used to avoid temporal leakage.***



***Baseline ROC-AUC:***



&#x20;   ***0.564427***



***Baseline + Intent–Impact Divergence ROC-AUC:***



&#x20;   ***0.560606***



***Observed difference:***



&#x20;   ***-0.003821***



***The 10,000-sample bootstrap 95% confidence interval was:***



&#x20;   ***\[-0.024571, +0.018007]***



***The paired permutation test produced:***



&#x20;   ***p = 0.72962704***



***Therefore, the study found no statistically detectable incremental predictive value of divergence for the selected 90-day structural-rework outcome.***



***This negative result is retained as an empirical finding.***



***## Reproducibility***



***Python version:***



&#x20;   ***>= 3.12, < 3.13***



***Install dependencies:***



&#x20;   ***python -m pip install -r requirements.txt***



***Run tests:***



&#x20;   ***python -m pytest -q***



***The local SQLite database and environment secrets are excluded from version control.***



***## Project Structure***



&#x20;   ***src/intentinsight/***

&#x20;       ***analysis/***

&#x20;       ***application/***

&#x20;       ***domain/***

&#x20;       ***infrastructure/***

&#x20;       ***ml/***

&#x20;       ***presentation/***



&#x20;   ***tests/***

&#x20;       ***unit/***

&#x20;       ***integration/***



&#x20;   ***scripts/***

&#x20;       ***research and validation experiments***



***## Engineering Quality***



***The project uses layered architecture, domain models, application services, database infrastructure, typed Python models, automated testing, reproducible research scripts, explicit dependency management, and an isolated development environment.***



***The automated test suite contains 73 passing tests.***



***## Status***



***Research implementation and empirical evaluation complete.***



***Final thesis preparation is in progress.***
