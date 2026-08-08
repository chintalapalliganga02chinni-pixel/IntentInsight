# IntentInsight — System Architecture

## 1. Overview

IntentInsight is an empirical software engineering research tool designed to investigate whether semantic–structural divergence in GitHub pull requests can predict post-merge instability.

The system analyses three primary dimensions:

1. Declared developer intent
2. Observed structural impact
3. Post-merge outcome

These dimensions are combined to compute the Intent–Impact Divergence Score (IIDS) and evaluate its predictive value.

---

## 2. Research Pipeline

The complete system follows the following pipeline:

GitHub Repository
|
v
Repository Mining
|
v
Pull Request Dataset
|
+----------------------+
|                      |
v                      v
Intent Analysis        Structural Analysis
|                      |
v                      v
Intent Features        Impact Features
|                      |
+----------+-----------+
|
v
Feature Engineering
|
v
IIDS Engine
|
v
Post-Merge Outcome
|
v
Machine Learning
|
v
Model Evaluation
|
v
Dashboard

---

## 3. Architectural Style

IntentInsight uses a layered monolithic architecture.

The system is divided into four primary layers:

### Presentation Layer

Responsible for interaction with the user and visualization of analysis results.

Primary technology:

- Streamlit

### Application Layer

Responsible for orchestrating use cases and coordinating domain operations.

Examples:

- repository analysis
- pull request analysis
- dataset generation
- experiment execution

### Domain Layer

Contains the core concepts and business/research logic of the system.

Examples:

- PullRequest
- Intent
- StructuralImpact
- IIDSResult
- InstabilityOutcome
- PredictionResult

The domain layer should remain independent of external frameworks where practical.

### Infrastructure Layer

Provides implementations for external dependencies.

Examples:

- GitHub API
- Git repositories
- SQLite
- NLP models
- static analysis tools
- file storage

---

## 4. High-Level Components

### 4.1 Repository Mining

Responsible for obtaining real-world pull request data.

Responsibilities:

- retrieve repositories
- retrieve pull requests
- retrieve commits
- retrieve changed files
- retrieve reviews where available
- identify merge information
- collect relevant post-merge activity

The mining component must support reproducible data collection.

---

### 4.2 Intent Analysis

Responsible for representing the semantic intent expressed by developers.

Potential input:

- pull request title
- pull request description
- commit messages

Potential outputs:

- normalized intent text
- semantic embedding
- intent category
- intent confidence
- text-quality indicators

The final feature set will be determined after exploratory analysis.

---

### 4.3 Structural Analysis

Responsible for measuring the actual software changes introduced by a pull request.

Potential measurements include:

- files changed
- lines added
- lines deleted
- complexity change
- affected modules
- dependency changes
- coupling-related measures
- dependency graph evolution

Structural analysis should compare the relevant pre-change and post-change states where technically feasible.

---

### 4.4 Feature Engineering

Combines intent, structural, repository and pull-request characteristics into a research dataset.

Feature categories include:

#### Pull Request Features

- PR size
- number of commits
- number of files changed
- review activity
- time-related characteristics

#### Intent Features

- semantic representation
- intent category
- intent text characteristics

#### Structural Features

- complexity delta
- dependency delta
- graph metrics
- affected modules
- coupling indicators

---

### 4.5 IIDS Engine

The IIDS engine is the central research component.

It transforms intent and structural impact features into an interpretable Intent–Impact Divergence Score.

The final mathematical formulation must be justified using:

- relevant literature
- exploratory analysis
- available data
- normalization requirements
- sensitivity analysis where feasible

The implementation must not use arbitrary weights without justification.

---

### 4.6 Post-Merge Outcome Analysis

Responsible for determining whether a pull request exhibits an operational definition of post-merge instability.

Candidate signals include:

- explicit revert
- corrective follow-up work
- bug-related follow-up activity
- issue-linked corrective changes
- subsequent changes affecting the same components

The final instability label must be defined before model evaluation and applied consistently.

---

### 4.7 Machine Learning

The predictive component evaluates whether IIDS provides useful information for predicting post-merge instability.

Models:

- Logistic Regression
- Random Forest
- XGBoost

Two principal feature configurations should be compared:

#### Baseline

Conventional pull request features.

#### IIDS-enhanced

Baseline features + IIDS-related features.

Evaluation metrics may include:

- Precision
- Recall
- F1-score
- ROC-AUC
- confusion matrix

The exact evaluation protocol will depend on the final dataset size and class distribution.

---

### 4.8 Explainability

The system should provide interpretable explanations of model predictions.

SHAP may be used where appropriate.

The explanation must be derived from actual model features and predictions.

The system must never generate hard-coded explanations that do not correspond to the underlying analysis.

---

### 4.9 Dashboard

The dashboard provides three primary views.

#### Repository Analysis

- repository information
- mining status
- number of PRs analysed

#### Pull Request Analysis

- declared intent
- structural impact
- IIDS
- predicted instability
- prediction confidence
- contributing factors

#### Research Results

- dataset statistics
- IIDS distribution
- model comparison
- evaluation metrics
- ROC curves
- feature importance
- explainability results

---

## 5. Project Structure

```text
IntentInsight/
│
├── src/
│   └── intentinsight/
│       ├── domain/
│       │   ├── models/
│       │   └── services/
│       │
│       ├── application/
│       │   ├── services/
│       │   └── pipelines/
│       │
│       ├── infrastructure/
│       │   ├── github/
│       │   ├── git/
│       │   ├── database/
│       │   └── configuration/
│       │
│       ├── analysis/
│       │   ├── intent/
│       │   ├── structural/
│       │   ├── graph/
│       │   └── features/
│       │
│       ├── iids/
│       │
│       ├── ml/
│       │   ├── models/
│       │   ├── evaluation/
│       │   └── explainability/
│       │
│       └── presentation/
│           └── dashboard/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/
├── config/
│
├── datasets/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── experiments/
├── results/
├── docs/
│
├── README.md
├── MASTER_PLAN.md
├── ARCHITECTURE.md
├── TODO.md
├── DEV_LOG.md
├── project_context.md
├── pyproject.toml
├── .env.example
└── .gitignore