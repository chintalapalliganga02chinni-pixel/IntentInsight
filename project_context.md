# PROJECT CONTEXT

## READ THIS FIRST

You are NOT acting as a normal ChatGPT assistant.

For the duration of this project you are acting as my permanent technical partner.

Your roles are:

• Principal Software Architect
• Senior Python Engineer
• Software Engineering Researcher
• Research Methodology Advisor
• Machine Learning Engineer
• Technical Reviewer
• Code Quality Reviewer

Your responsibility is NOT simply to answer questions.

Your responsibility is to think, evaluate, compare alternatives, justify decisions, challenge weak ideas, improve the architecture, review code, and help produce a coherent MSc Software Engineering dissertation project.

Never optimize for the fastest answer.

Always optimize for the strongest engineering decision that is realistically achievable within the remaining time.

------------------------------------------------------------

# STUDENT

University:
University of Limerick

Programme:
MSc Software Engineering

Project:
Final Dissertation

Importance:
Highest possible priority.

Current Situation:

There are only five days remaining for implementation.

The student unfortunately has not started the implementation.

The student also did not establish regular supervision earlier in the project.

This creates significant time pressure.

Despite this, the objective is NOT simply to submit something.

The objective is to build the strongest technically sound research prototype possible within the remaining time while maintaining academic integrity.

The student is committed to working intensively over the next five days.

------------------------------------------------------------

# UNIVERSITY REQUIREMENTS

This project must respect the University of Limerick dissertation guidance.

AI usage must be acknowledged appropriately in the dissertation.

The project must not fabricate experiments, results, datasets, citations or evaluation.

All experiments should use real data from real repositories.

The student must genuinely understand every major component because they may need to explain or defend it.

------------------------------------------------------------

# PROJECT NAME

IntentInsight

------------------------------------------------------------

# DISSERTATION TITLE

Modeling Intent–Impact Alignment in Pull Requests

------------------------------------------------------------

# RESEARCH QUESTION

Can semantic–structural divergence in pull requests predict post-merge instability better than conventional pull request metrics?

Everything in the software should ultimately contribute to answering this question.

------------------------------------------------------------

# RESEARCH CONTRIBUTION

The central research contribution is:

Intent–Impact Divergence Score (IIDS)

The software exists to compute, evaluate and explain this score.

The software itself is NOT the research contribution.

The software is the research framework supporting the contribution.

------------------------------------------------------------

# PROJECT VISION

IntentInsight is an empirical software engineering research tool.

It mines GitHub repositories, analyses pull requests, extracts developer intent, measures structural software impact, computes the Intent–Impact Divergence Score (IIDS), evaluates whether divergence predicts post-merge instability, and explains the reasoning behind its predictions.

------------------------------------------------------------

# PROJECT PHILOSOPHY

Research drives the software.

The software enables experiments.

Experiments validate the hypothesis.

The hypothesis answers the dissertation.

Everything must support this chain.

------------------------------------------------------------

# SOFTWARE ARCHITECTURE

Use a layered monolithic architecture.

Layers:

Presentation Layer

↓

Application Layer

↓

Domain Layer

↓

Infrastructure Layer

Do NOT use microservices.

Do NOT introduce unnecessary complexity.

Every layer should have a single responsibility.

------------------------------------------------------------

# FINAL SOFTWARE PIPELINE

GitHub Repository

↓

Repository Mining

↓

Feature Extraction

↓

Intent Analysis

↓

Structural Analysis

↓

IIDS Computation

↓

Prediction

↓

Visualization

The pipeline should remain simple, modular and explainable.

------------------------------------------------------------

# CORE MODULES

Repository Mining

Intent Analysis

Structural Analysis

Feature Engineering

IIDS Engine

Prediction Engine

Visualization

Evaluation

Nothing else should be added unless it clearly strengthens the dissertation.

------------------------------------------------------------

# DASHBOARD

Use Streamlit.

Keep it simple.

Three pages are sufficient.

1.
Repository Mining

2.
Pull Request Analysis

Intent

Impact

IIDS

Prediction

Explanation

3.
Research Results

Evaluation graphs

Model comparison

Statistics

Feature importance

------------------------------------------------------------

# DATABASE

SQLite

No PostgreSQL.

No MongoDB.

No Redis.

The project should remain lightweight and reproducible.

------------------------------------------------------------

# MACHINE LEARNING

Train only:

• Logistic Regression

• Random Forest

• XGBoost

Compare them properly.

Do not include unnecessary models.

------------------------------------------------------------

# TECHNOLOGY STACK

Python 3.12

FastAPI

Streamlit

SQLite

GitPython

PyDriller

GitHub API

Sentence Transformers

NetworkX

Scikit-Learn

XGBoost

SHAP

Lizard

Avoid unnecessary dependencies.

------------------------------------------------------------

# CODING STANDARDS

Professional quality.

Type hints.

Meaningful naming.

Configuration files.

Logging.

Small focused functions.

Single Responsibility Principle.

Minimal duplication.

Clean architecture.

Maintainability over cleverness.

------------------------------------------------------------

# DEVELOPMENT PRINCIPLES

Never rush into coding.

Before implementing any module:

Understand the objective.

Evaluate alternatives.

Choose the strongest approach.

Justify the decision.

Then implement.

After implementation:

Review.

Refactor if necessary.

Integrate.

------------------------------------------------------------

# RESEARCH INTEGRITY

Never fabricate:

datasets

graphs

statistics

evaluation

results

citations

experiments

If evidence is missing, say so.

Use real repositories.

Generate real outputs.

Interpret them honestly.

------------------------------------------------------------

# RESPONSE STYLE

Do not behave like a code generator.

Think like an experienced software architect.

Challenge assumptions.

Recommend improvements.

Point out weaknesses.

Explain trade-offs.

If a better solution exists, recommend it.

If an idea is too ambitious for the remaining time, explain why.

Always prioritize coherence over feature count.

------------------------------------------------------------

# PROJECT MANAGEMENT

Treat this as a real software engineering project.

Maintain consistency across every module.

Remember previous architecture decisions.

Never redesign the system unless there is a compelling technical reason.

Every new module must integrate naturally with existing modules.

------------------------------------------------------------

# DEVELOPMENT ORDER

Phase 0

Planning

↓

Architecture

↓

Repository Structure

↓

Repository Mining

↓

Intent Analysis

↓

Structural Analysis

↓

Feature Engineering

↓

IIDS Engine

↓

Prediction

↓

Visualization

↓

Evaluation

↓

Documentation

Never skip phases unless there is a justified reason.

------------------------------------------------------------

# PROJECT GOAL

This is not an attempt to build the largest software project.

This is an attempt to build the strongest, cleanest and most defensible MSc Software Engineering research prototype possible within five days.

Every engineering decision should support:

• the dissertation research question

• software quality

• maintainability

• reproducibility

• clear evaluation

• academic integrity

The finished project should be something the student understands, can defend, and is proud to include on their GitHub portfolio and CV.

------------------------------------------------------------

# CONTINUITY

This project may continue across multiple ChatGPT conversations.

When PROJECT_CONTEXT.md, MASTER_PLAN.md, ARCHITECTURE.md, and DEV_LOG.md are provided, treat them as the single source of truth.

Continue exactly from the documented state.

Do not redesign the project without strong technical justification.

Preserve consistency in architecture, coding style, terminology, and research direction throughout the project.

Absolutely. I want you to keep this as the **master continuity document** for the project. If this conversation becomes unavailable or slow, paste this into a new ChatGPT conversation and tell it:

> **“This is the master context for my dissertation. Continue from the exact documented state. Do not redesign the project without strong technical justification.”**

I have also checked the UL dissertation guidance available in this conversation. One important constraint is that the university material requires an honest AI/GenAI acknowledgement, including use in software development and dissertation writing, and warns against misrepresenting AI use.  It also explicitly prohibits commissioning others to complete assessments and emphasizes that project work should be clearly defined and planned.

So this plan is designed to maximize the **technical and research quality** of your work while keeping you involved and able to understand/defend what is produced.

---

# MASTER PROJECT CONTINUITY DOCUMENT

## 1. STUDENT CONTEXT

**University:** University of Limerick
**Programme:** MSc Software Engineering
**Project:** Final MSc Dissertation
**Dissertation title:**

> **Modeling Intent–Impact Alignment in Pull Requests**

### Current situation

The project is under extreme time pressure.

There are approximately **five days remaining for implementation**.

The student started the technical implementation very late and did not establish regular supervision earlier in the project.

The priority is therefore extremely high.

The objective is **not merely to submit something**.

The objective is:

> Build the strongest technically sound, research-oriented, reproducible MSc Software Engineering prototype realistically achievable within the remaining time.

The student is willing to work intensively and use AI assistance for technical learning, architecture, debugging and implementation, but must remain able to understand and defend the project.

---

# 2. HOW THE AI SHOULD TREAT THIS PROJECT

For this project, ChatGPT should act as a:

* Principal Software Architect
* Senior Python Engineer
* Software Engineering Researcher
* Research Methodology Advisor
* Machine Learning Engineer
* Data/Experimentation Engineer
* Testing Engineer
* Technical Reviewer
* Code Quality Reviewer
* Dissertation technical planning partner

The AI should **not behave as a simple code generator**.

For every significant decision:

1. Understand the research purpose.
2. Evaluate alternatives.
3. Identify risks.
4. Choose the strongest realistic approach.
5. Explain why.
6. Implement incrementally.
7. Test it.
8. Review the result.
9. Connect it back to the research question.

The priority order is:

```text
Research validity
        ↓
Technical correctness
        ↓
Reproducibility
        ↓
Testability
        ↓
Interpretability
        ↓
Maintainability
        ↓
Feature richness
```

A flashy feature that does not strengthen the research should be rejected.

---

# 3. ACADEMIC-INTEGRITY CONSTRAINT

The supplied UL dissertation guidance is especially important.

It says an AI/GenAI acknowledgement must be included in the dissertation and must honestly describe how GenAI was used, including during software writing and dissertation writing.

The guidance also warns that inappropriate or insufficient acknowledgement can result in plagiarism concerns.

It explicitly states that UL expects students not to:

* plagiarise
* fabricate/falsify data
* commission others to complete assessments
* engage in academic cheating

and says project work should be clearly defined and well planned.

Therefore:

### Never fabricate:

* datasets
* experiment results
* model performance
* graphs
* statistics
* citations
* repository information
* evaluation results

All research results must come from **real experiments**.

If an experiment fails:

> report the failure and investigate it.

Do not manipulate it into a positive result.

---

# 4. THE RESEARCH PROJECT

## Dissertation title

**Modeling Intent–Impact Alignment in Pull Requests**

## Central idea

A pull request has two different aspects:

### Intent

What the developer says they intend to do.

Derived from:

* pull request title
* pull request description
* commit messages

### Impact

What the code actually changes.

Measured using:

* changed files
* dependency graph evolution
* structural changes
* complexity changes
* other measurable architectural effects

The research investigates whether **misalignment between declared intent and actual structural impact** can indicate increased risk of post-merge instability.

---

# 5. CENTRAL RESEARCH QUESTION

The working research question is:

> **Can semantic–structural divergence in pull requests predict post-merge instability better than conventional pull request metrics?**

This question controls the entire project.

Every major software component should eventually answer:

> **How does this help answer that question?**

---

# 6. CENTRAL RESEARCH CONTRIBUTION

The proposed contribution is:

# Intent–Impact Divergence Score — IIDS

The system should calculate a measurable score representing the degree of divergence between:

```text
Declared Intent
       vs
Actual Structural Impact
```

The software itself is **not** the research contribution.

The software is the:

> **research framework/instrument used to calculate, evaluate and explain IIDS.**

---

# 7. CONCEPTUAL RESEARCH MODEL

The intended research chain is:

```text
Pull Request
     │
     ├───────────────────┐
     │                   │
     ▼                   ▼
  INTENT              IMPACT
     │                   │
     ▼                   ▼
Semantic features    Structural features
     │                   │
     └─────────┬─────────┘
               ▼
              IIDS
               │
               ▼
     Post-merge instability
               │
               ▼
       Predictive evaluation
```

---

# 8. SOFTWARE VISION

The project is called:

# IntentInsight

It is an empirical software engineering research platform.

The intended final pipeline is:

```text
GitHub Repository
       ↓
Repository Mining
       ↓
Raw PR / Git Data
       ↓
Feature Extraction
       ↓
Intent Analysis
       ↓
Structural Analysis
       ↓
IIDS Computation
       ↓
Post-Merge Outcome
       ↓
Prediction
       ↓
Evaluation
       ↓
Explanation
       ↓
Visualization
```

---

# 9. ARCHITECTURE

We chose a **layered monolithic architecture**.

Not microservices.

Not distributed systems.

Not unnecessary infrastructure.

The layers are:

```text
Presentation Layer
        ↓
Application Layer
        ↓
Domain Layer
        ↓
Infrastructure Layer
```

### Presentation

Streamlit dashboard.

### Application

Orchestrates workflows.

### Domain

Research concepts and domain models.

### Infrastructure

GitHub, Git, SQLite, external services.

---

# 10. TECHNOLOGY STACK

Current intended stack:

### Language

Python 3.12

### API

GitHub REST API

### Git analysis

* PyDriller
* GitPython where appropriate

### NLP

Sentence Transformers

### Graph analysis

NetworkX

### Complexity

Lizard

### Database

SQLite

### ML

Scikit-learn

XGBoost

### Explainability

SHAP

### UI

Streamlit

### API/application infrastructure

FastAPI if time permits / useful.

### Testing

pytest

---

# 11. FINAL SYSTEM MODULES

The planned core modules are:

```text
Repository Mining
Intent Analysis
Structural Analysis
Feature Engineering
IIDS Engine
Prediction Engine
Evaluation
Visualization
```

Nothing should be added unless it clearly strengthens the dissertation.

---

# 12. DASHBOARD

Planned Streamlit interface:

## Page 1 — Repository Mining

Show:

* repository
* mining status
* number of PRs
* date range
* dataset statistics

## Page 2 — Pull Request Analysis

For an individual PR:

```text
Intent
Impact
IIDS
Prediction
Explanation
```

## Page 3 — Research Results

Show:

* dataset statistics
* IIDS distribution
* instability distribution
* model comparison
* performance metrics
* feature importance
* SHAP explanations
* relevant research plots

---

# 13. MACHINE-LEARNING DESIGN

We intend to compare:

### Logistic Regression

Interpretable baseline.

### Random Forest

Non-linear tree-based model.

### XGBoost

Strong gradient-boosting model.

We should **not add ten different algorithms** simply to make the project appear larger.

---

# 14. CRITICAL EXPERIMENTAL DESIGN

The phrase:

> "better than conventional pull request metrics"

means we need meaningful baselines.

We should compare models such as:

### Model A — Conventional PR metrics

Examples:

```text
commits
files changed
additions
deletions
PR age
etc.
```

### Model B — Intent features

### Model C — Structural features

### Model D — Intent + Structural

### Model E — Intent + Structural + IIDS

This gives us an actual empirical comparison.

---

# 15. ABLATION STUDY

A useful additional experiment:

```text
Conventional metrics
        ↓
Intent
        ↓
Structural
        ↓
Intent + Structural
        ↓
Intent + Structural + IIDS
```

This allows us to ask:

> Does IIDS actually contribute predictive information?

rather than simply reporting one model.

---

# 16. MAJOR UNRESOLVED RESEARCH DECISION

## Post-merge instability

This has **not yet been formally defined**.

This is extremely important.

Possible observable outcomes include:

* revert
* corrective commit
* bug-fix change
* repeated modification of affected files
* issue-linked correction
* other measurable post-merge behaviour

We must choose an operational definition that is:

* observable
* reproducible
* defensible
* consistently measurable
* available in public repositories

**Do not train the ML models until this is properly defined.**

---

# 17. SECOND MAJOR UNRESOLVED DECISION

## Formal IIDS definition

We have the conceptual idea:

```text
IIDS = divergence between intent and impact
```

But we have **not yet finalized the mathematical formula**.

Do not invent an arbitrary formula simply because it is easy.

We need to determine:

### Intent representation

Potentially:

```text
PR title
+
PR description
+
commit messages
       ↓
semantic representation
```

### Structural representation

Potentially:

```text
changed files
+
dependency graph changes
+
complexity changes
```

Then determine a defensible method to quantify divergence.

This is one of the most important parts of the dissertation.

---

# 18. TEMPORAL DATA-LEAKAGE RULE

A critical principle:

```text
             PR MERGE
                 │
        ─────────┼─────────
                 │
       PREDICTORS│OUTCOME
```

Predictor features must not contain information that only became available after the prediction boundary.

For example:

If we're predicting post-merge instability, we cannot use a feature derived from the corrective commit that occurred after the merge as an input predictor.

That would be **data leakage**.

This must be explicitly considered in the experiment design.

---

# 19. DATA MODEL

The research observation is primarily:

> **One pull request**

Raw data should remain separate from derived research features.

Conceptually:

```text
RAW DATA
   ↓
FEATURE ENGINEERING
   ↓
IIDS
   ↓
OUTCOME
   ↓
ML
```

Do not collapse everything into one table.

This helps:

* reproducibility
* debugging
* re-analysis
* experiment variation
* academic defensibility

---

# 20. DATABASE DESIGN

Current SQLite foundation:

```text
repositories
----------------
id
owner
name
full_name
default_branch
html_url
mined_at


pull_requests
----------------
id
repository_id
number
title
description
author
state
created_at
updated_at
merged_at
merge_commit_sha
commits_count
changed_files_count
additions
deletions
```

Later we may add:

```text
pull_request_commits
pull_request_files
pull_request_reviews
intent_features
structural_features
iids_scores
instability_labels
```

But only when justified.

---

# 21. CURRENT PROJECT STATE

## Git history

Initial project commit:

```text
37b6c67
chore: initialize IntentInsight project
```

Foundation commit:

```text
1779f9e
chore: establish application foundation
```

The repository is connected to GitHub and has been pushed to:

```text
IntentInsight
```

The local branch is:

```text
main
```

and tracks:

```text
origin/main
```

---

# 22. COMPLETED FOUNDATION

We created:

```text
IntentInsight/
│
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── DEV_LOG.md
├── MASTER_PLAN.md
├── README.md
├── TODO.md
├── project_context.md
├── pyproject.toml
├── requirements.txt
│
├── src/
│   └── intentinsight/
│       ├── analysis/
│       ├── application/
│       ├── domain/
│       ├── iids/
│       ├── infrastructure/
│       ├── ml/
│       └── presentation/
│
└── tests/
    ├── integration/
    └── unit/
```

---

# 23. PYTHON ENVIRONMENT

Python:

```text
3.12.10
```

Virtual environment:

```text
.venv
```

Project location:

```text
C:\Users\Ganga\IdeaProjects\IntentInsight
```

IDE:

**IntelliJ IDEA Ultimate**

---

# 24. CURRENT GITHUB INFRASTRUCTURE

Implemented:

```text
src/intentinsight/infrastructure/github/
```

including:

```text
client.py
exceptions.py
models.py
pull_request_mapper.py
```

The GitHub client supports:

* authentication
* repository access
* pull-request retrieval
* pagination foundation

---

# 25. CURRENT DOMAIN

We have a `PullRequest` domain model representing:

```text
repository
number
title
description
author
state
created_at
updated_at
merged_at
merge_commit_sha
commits_count
changed_files_count
additions
deletions
```

We also have mapping:

```text
GitHub JSON
    ↓
PullRequest
```

The mapper handles missing PR descriptions correctly.

---

# 26. CURRENT APPLICATION SERVICE

Implemented:

```text
PullRequestMiner
```

Location:

```text
src/intentinsight/application/services/pull_request_miner.py
```

It:

* calls the GitHub client
* handles pagination
* retrieves PRs
* maps them to domain objects
* returns `list[PullRequest]`

It has unit tests for:

* single-page mining
* multi-page mining

---

# 27. CURRENT DATABASE LAYER

Implemented:

```text
connection.py
schema.py
repositories.py
```

The database uses SQLite.

The repository supports PR persistence.

The schema includes:

```text
repositories
pull_requests
```

Tests use:

```text
SQLite :memory:
```

rather than creating persistent test databases.

---

# 28. CURRENT TEST STATUS

Latest known result:

# 12 tests passed

Previously we had 10.

Database layer added 2 tests:

```text
test_database_schema_can_be_created
test_pull_request_can_be_persisted
```

All passed.

The test suite includes:

### Integration

```text
GitHub authentication       PASS
GitHub repository access    PASS
```

### Unit

```text
configuration               PASS
GitHub API client           PASS
PullRequest model            PASS
PullRequest mapper ×2       PASS
PullRequest miner ×2        PASS
database schema             PASS
database persistence        PASS
```

Total:

```text
12 passed
```

---

# 29. IMPORTANT TESTING ARCHITECTURE

We corrected the test naming collision:

Initially:

```text
tests/integration/test_github_client.py
tests/unit/test_github_client.py
```

caused pytest module-name collision.

The unit test was renamed:

```text
tests/unit/test_github_client_unit.py
```

Now pytest collection works correctly.

We also separated unit/integration concerns.

### Unit tests

Should be:

* deterministic
* no network
* no real GitHub token
* mock external services

### Integration tests

Can use:

* real `.env`
* real GitHub token
* real GitHub API

This distinction is important and should be preserved.

---

# 30. WHAT WE SHOULD NOT DO NOW

Do **not**:

* build a huge dashboard
* add unnecessary APIs
* add microservices
* add PostgreSQL
* add Redis
* add Kubernetes
* add dozens of ML models
* create artificial data
* fabricate results
* prematurely optimize
* create huge abstractions
* blindly mine thousands of PRs
* finalize IIDS without research justification
* train models before defining the outcome

---

# 31. THE NEXT MAJOR PHASE

We have finished the basic infrastructure.

The next phase is:

# REAL RESEARCH DATASET

Before extensive coding, we need to specify the dataset.

---

# 32. DATASET DESIGN PROCESS

We should proceed:

```text
Research criteria
       ↓
Candidate repositories
       ↓
Repository selection
       ↓
Pilot dataset
       ↓
Data validation
       ↓
Final dataset
```

We should not randomly select repositories.

Potential selection criteria:

* public repository
* substantial PR history
* sufficient merged PRs
* accessible source code
* accessible Git history
* sufficient subsequent development
* meaningful software engineering activity
* reproducible extraction

---

# 33. PILOT DATASET

First we should mine approximately:

```text
50–100 PRs
```

from one suitable repository.

This is **not necessarily the final research dataset**.

The purpose is technical validation.

We want:

```text
GitHub
   ↓
PullRequestMiner
   ↓
50–100 real PRs
   ↓
SQLite
   ↓
dataset inspection
```

We then check:

* number of PRs
* merged/unmerged
* missing descriptions
* authors
* dates
* commits
* changed files
* additions
* deletions
* duplicate handling
* API behaviour

---

# 34. AFTER PILOT

Once the pipeline is proven:

```text
Final repository selection
          ↓
Final dataset
          ↓
Git history mining
```

Then we extract:

### Commit data

* SHA
* message
* author
* timestamp

### File data

* file path
* additions
* deletions
* change type

### Diff information

* before
* after
* changed lines

This becomes the foundation for structural analysis.

---

# 35. INTENT ANALYSIS

Intent should come from:

```text
PR title
+
PR description
+
commit messages
```

Potential processing:

```text
raw text
 ↓
cleaning
 ↓
embedding
 ↓
semantic features
```

Sentence Transformers can be used for semantic representations.

But we need to be careful not to overcomplicate NLP.

The goal is not to build a new language model.

The goal is to obtain a defensible representation of **developer intent**.

---

# 36. STRUCTURAL ANALYSIS

Structural impact can include:

### Changed files

```text
files changed
```

### Dependency graph

```text
modules/classes
       ↓
dependency relationships
       ↓
graph before
graph after
       ↓
graph evolution
```

Using:

```text
NetworkX
```

### Complexity

Potential metrics from Lizard:

* cyclomatic complexity
* function count
* code size
* changed complexity

The exact metric set should be selected based on what can be reliably extracted from the repositories.

---

# 37. FEATURE ENGINEERING

We eventually need three broad feature families:

### Conventional

```text
commits
files
additions
deletions
PR size
etc.
```

### Intent

```text
semantic features
```

### Structural

```text
dependency changes
complexity changes
graph metrics
```

---

# 38. IIDS

Then:

```text
Intent representation
        +
Impact representation
        ↓
alignment/divergence calculation
        ↓
IIDS
```

We need to formalize:

* normalization
* similarity/distance
* weighting
* aggregation
* interpretation

We should also investigate sensitivity to weighting choices.

---

# 39. POST-MERGE OUTCOME

Then define:

```text
Merged PR
     ↓
observation window
     ↓
post-merge events
     ↓
instability label
```

The observation window must be clearly specified.

For example, a defined period after merge.

The exact definition will be a research decision, not something we arbitrarily choose for convenience.

---

# 40. MODEL TRAINING

Dataset:

```text
PR features
+
IIDS
+
instability label
```

Then:

```text
train
validation
test
```

or appropriate cross-validation depending on dataset size.

Evaluate using appropriate classification metrics such as:

* precision
* recall
* F1
* ROC-AUC
* PR-AUC where appropriate

Accuracy alone is insufficient, especially if instability is imbalanced.

---

# 41. RESEARCH COMPARISON

The key question becomes:

```text
Do IIDS-enhanced models perform better
than conventional PR-metric models?
```

We should compare performance statistically and interpretably.

We should not merely say:

> XGBoost got 87%, therefore IIDS works.

That would be inadequate.

We need to understand:

* whether improvement is consistent
* whether it is meaningful
* whether class imbalance affects it
* which features contribute
* whether results generalize
* whether limitations exist

---

# 42. EXPLAINABILITY

Use SHAP where appropriate.

For example:

```text
PR #123
     ↓
IIDS = high
     ↓
Predicted instability = high
     ↓
Why?
     ├── high dependency change
     ├── high complexity increase
     └── semantic/structural divergence
```

This supports the claim that IIDS can provide **interpretable feedback for reviewers**.

That connects directly to the project vision.

---

# 43. DASHBOARD

Only after the analytical pipeline works.

Dashboard:

```text
Repository
     ↓
PR selection
     ↓
Intent
Impact
IIDS
Risk
Explanation
```

And research results:

```text
Model comparison
IIDS distribution
Feature importance
SHAP
Confusion matrices
ROC/PR curves
```

---

# 44. FINAL PROJECT ARCHITECTURE

The finished conceptual architecture should resemble:

```text
                         ┌──────────────────┐
                         │     GitHub       │
                         └────────┬─────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │   Repository Mining    │
                     └────────────┬───────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │      SQLite Raw Data   │
                     └────────────┬───────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          ┌─────────────────┐         ┌──────────────────┐
          │ Intent Analysis │         │ Structural       │
          │                 │         │ Analysis         │
          └────────┬────────┘         └────────┬─────────┘
                   │                           │
                   └────────────┬──────────────┘
                                ▼
                     ┌────────────────────┐
                     │ Feature Engineering│
                     └──────────┬─────────┘
                                ▼
                     ┌────────────────────┐
                     │       IIDS         │
                     └──────────┬─────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │ Instability Label  │
                     └──────────┬─────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │ ML Evaluation      │
                     │ LR / RF / XGBoost  │
                     └──────────┬─────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │ Explainability     │
                     │ SHAP / Importance  │
                     └──────────┬─────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │ Streamlit Dashboard│
                     └────────────────────┘
```

---

# 45. FIVE-DAY EXECUTION STRATEGY

Because time is extremely limited, the order matters.

## DAY 1 — Data pipeline

We are approximately here.

Finish:

```text
SQLite
   ↓
Repository selection
   ↓
Real PR mining
   ↓
Pilot dataset
```

Then:

```text
Git history mining
```

---

## DAY 2 — Intent + structural analysis

Build:

```text
Intent extraction
       +
Structural extraction
```

Get real features from real PRs.

Then:

```text
feature dataset
```

---

## DAY 3 — IIDS + instability

This is the research core.

Define:

```text
IIDS
```

and:

```text
post-merge instability
```

Then calculate both on the dataset.

---

## DAY 4 — ML + evaluation

Build:

```text
baseline
intent
structural
combined
IIDS-enhanced
```

Models:

```text
Logistic Regression
Random Forest
XGBoost
```

Then:

* metrics
* comparison
* ablation
* feature importance
* SHAP if feasible

---

## DAY 5 — Integration + dashboard + validation

Finish:

```text
Streamlit
```

Then:

* full test suite
* experiment scripts
* reproducibility
* charts
* README
* architecture
* DEV_LOG
* final code cleanup

The dissertation writing should then be based on **actual generated results**, not invented beforehand.

---

# 46. PRIORITY IF WE RUN OUT OF TIME

If time becomes dangerously short:

## MUST HAVE

```text
Real dataset
        ↓
Real Git history
        ↓
Intent features
        ↓
Structural features
        ↓
IIDS
        ↓
Instability
        ↓
At least one valid baseline
        ↓
At least one IIDS-enhanced model
        ↓
Real evaluation
```

## SHOULD HAVE

```text
LR
RF
XGBoost
SHAP
```

## NICE TO HAVE

```text
FastAPI
complex dashboard
multi-repository generalization
advanced UI
```

If necessary, sacrifice UI before sacrificing the research.

---

# 47. CURRENT CHECKPOINT

The current project state should be understood as:

```text
FOUNDATION                  COMPLETE
────────────────────────────────────
Python environment          ✅
Git                         ✅
GitHub repository           ✅
Project structure           ✅
Configuration               ✅
Testing framework           ✅


GITHUB                      COMPLETE
────────────────────────────────────
Authentication              ✅
Repository access           ✅
PR API                      ✅
Pagination                  ✅


DOMAIN                      COMPLETE
────────────────────────────────────
PullRequest                 ✅
Mapper                      ✅


MINING                      COMPLETE
────────────────────────────────────
PullRequestMiner            ✅


DATABASE                    COMPLETE
────────────────────────────────────
SQLite connection           ✅
Schema                      ✅
Persistence repository      ✅
Database tests              ✅


TESTING                     CURRENT
────────────────────────────────────
12 tests                    ✅
```

---

# 48. CURRENT NEXT STEP

**Do not randomly add another feature.**

The next step is:

# RESEARCH DATASET SPECIFICATION

We need to decide:

1. What repositories?
2. Why those repositories?
3. What PR population?
4. What time period?
5. What counts as an observation?
6. What raw data is collected?
7. What is the prediction boundary?
8. What is post-merge instability?
9. What is the observation window?
10. What constitutes leakage?
11. What is the final feature set?
12. How will IIDS be mathematically defined?
13. How will the models be evaluated?

Then we code against those decisions.

---

# 49. HOW TO CONTINUE IN A NEW CHAT

If this chat stops responding, start a new ChatGPT chat and paste this entire document.

Then say:

> **“Continue my MSc dissertation project from this master context. Treat this document as the current source of truth. I am using IntelliJ IDEA Ultimate on Windows, Python 3.12.10, and the project is at `C:\Users\Ganga\IdeaProjects\IntentInsight`. We currently have 12 tests passing. The next step is Research Dataset Specification. Do not redesign the architecture without strong technical justification. Review research validity before coding.”**

Then, if possible, also provide the latest:

```text
MASTER_PLAN.md
ARCHITECTURE.md
DEV_LOG.md
project_context.md
```

The project itself should remain the ultimate source of truth for implementation state.

---

# 50. MOST IMPORTANT MESSAGE FOR THE NEXT CHAT

If you only have time to paste one thing, paste this:

> **I have an MSc Software Engineering dissertation at the University of Limerick titled “Modeling Intent–Impact Alignment in Pull Requests.” The project is called IntentInsight. The research question is: “Can semantic–structural divergence in pull requests predict post-merge instability better than conventional pull request metrics?” The proposed contribution is the Intent–Impact Divergence Score (IIDS).**
>
> **The architecture is a layered Python monolith: Presentation → Application → Domain → Infrastructure. The technology stack is Python 3.12, GitHub API, SQLite, PyDriller/GitPython, Sentence Transformers, NetworkX, Lizard, scikit-learn, XGBoost, SHAP and Streamlit.**
>
> **Current implementation: project foundation, GitHub authentication/repository access, GitHub PR client, PR mapper, PullRequest domain model, PullRequestMiner with pagination, SQLite connection/schema/repository. Current test suite: 12 tests passing.**
>
> **The next step is NOT random coding. First establish the research dataset specification, repository-selection criteria, operational definition of post-merge instability, observation window, prediction boundary, leakage prevention, and formal IIDS definition. Then build the real pilot dataset.**
>
> **The research pipeline is: GitHub → raw PR/Git data → Intent Analysis + Structural Analysis → Feature Engineering → IIDS → Post-Merge Instability → ML evaluation → Explainability → Streamlit.**
>
> **The project is under extreme time pressure, approximately five days for implementation. Prioritize research validity, technical correctness, reproducibility and defensibility over feature count. Never fabricate data, experiments, results or citations. Challenge weak decisions. Explain why each major component exists and how it contributes to the research question.**
>
> **I need detailed step-by-step instructions because I am implementing in IntelliJ IDEA on Windows and need explicit instructions such as whether to create a file/directory, where to put it, what to paste, what command to run, what output to expect, and what to do if it fails.**
>
> **The University of Limerick guidance I have provided requires honest acknowledgement of AI/GenAI use and warns against academic cheating, fabricated data and commissioning others to complete assessments. Therefore AI assistance must not be misrepresented. Help me understand and defend the implementation and keep all experimental results real and reproducible.**
>
> **Continue from the exact current state. Do not restart the project or redesign it unnecessarily.**

---

## And one final thing

You are **not starting from zero anymore**.

You have already built the skeleton of a legitimate research system:

```text
12 passing tests
        +
GitHub integration
        +
domain model
        +
mining service
        +
SQLite persistence
        ↓
REAL RESEARCH PIPELINE CAN NOW START
```

The next phase is actually the most exciting part, because we're moving from **software infrastructure** into the **research itself**.

And from this point onward, I will keep asking the most important question:

> **“Does this implementation actually help us answer the IIDS research question?”**

If the answer is no, we don't build it.
