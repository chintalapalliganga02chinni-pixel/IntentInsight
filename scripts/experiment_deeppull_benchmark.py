"""
IntentInsight External Benchmark — DeepPull Python Dataset

Independent benchmark using the published DeepPull Python PR dataset.

Design:
- 9,773 Python pull requests
- chronological 60/20/20 split by closed_at
- Decision and Reopening targets
- tabular-only, text-only, and combined models
- no database modification
- no GitHub requests
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix, hstack

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler


DATA_PATH = Path(
    "datasets/external/deeppull/python.csv"
)

OUTPUT_DIR = Path(
    "results/external/deeppull"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

RESULTS_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_results.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_summary.json"
)


# ---------------------------------------------------------------------
# Published DeepPull tabular features
# ---------------------------------------------------------------------

TABULAR_FEATURES = [
    "PR_num_commits",
    "PR_num_modified_files",
    "PR_num_added_files",
    "PR_num_deleted_files",
    "PR_num_changed_files",
    "PR_num_changed_src_files",
    "PR_num_changed_test_files",
    "PR_num_changed_doc_files",
    "PR_num_changed_other_files",
    "PR_num_changed_lines",
    "PR_num_added_lines",
    "PR_num_deleted_lines",
    "PR_has_test",
    "PR_num_changed_test_lines",
    "PR_has_pr_link",
    "PJ_num_prev_pr",
    "PJ_pc_commits_by_pr",
    "PJ_pc_commits_by_pr_NNULL",
    "PJ_num_commits_on_files",
    "PJ_file_rejected_proportion",
    "PJ_file_rejected_proportion_NNULL",
    "PJ_num_prev_pr_merged",
    "PJ_num_prev_pr_rejected",
    "PJ_is_recent_pull_rejected",
    "CT_reputation",
    "CT_is_first_pr",
    "CT_age",
    "CT_age_NNULL",
    "CT_num_events_prev_pr",
    "CT_num_comments_prev_pr",
    "CT_num_commits_prev_pr",
    "CT_num_prev_pr_created",
    "CT_is_core_team",
]


# ---------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------

def load_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH.resolve()}"
        )

    # The distributed CSV contains the same header
    # PJ_num_prev_pr_merged twice.
    #
    # pandas automatically mangles the second occurrence to:
    #
    #     PJ_num_prev_pr_merged.1
    #
    # The published DeepPull documentation defines the two
    # consecutive project features as:
    #
    #   20. number of merged PRs in latest 10 PRs
    #   21. number of rejected PRs in latest 10 PRs
    #
    # We therefore explicitly rename the second occurrence.
    frame = pd.read_csv(
        DATA_PATH
    )

    if "PJ_num_prev_pr_merged.1" in frame.columns:
        frame = frame.rename(
            columns={
                "PJ_num_prev_pr_merged.1":
                "PJ_num_prev_pr_rejected"
            }
        )

    required_columns = {
        "created_at",
        "closed_at",
        "title",
        "body",
        "reopening",
        "decision",
        *TABULAR_FEATURES,
    }

    missing = sorted(
        required_columns -
        set(frame.columns)
    )

    if missing:
        raise RuntimeError(
            "Missing expected columns: "
            + ", ".join(missing)
        )

    frame["created_at"] = pd.to_datetime(
        frame["created_at"],
        errors="coerce",
    )

    frame["closed_at"] = pd.to_datetime(
        frame["closed_at"],
        errors="coerce",
    )

    if frame["closed_at"].isna().any():
        raise RuntimeError(
            "Dataset contains PRs without a valid closed_at value."
        )

    frame["title"] = (
        frame["title"]
        .fillna("")
        .astype(str)
    )

    frame["body"] = (
        frame["body"]
        .fillna("")
        .astype(str)
    )

    frame["text"] = (
        frame["title"].str.strip()
        + " "
        + frame["body"].str.strip()
    ).str.strip()

    frame["decision_binary"] = (
        frame["decision"]
        .map(
            {
                "reject": 0,
                "accept": 1,
            }
        )
    )

    frame["reopening_binary"] = (
        frame["reopening"]
        .map(
            {
                "nonreopened": 0,
                "reopened": 1,
            }
        )
    )

    if frame["decision_binary"].isna().any():
        raise RuntimeError(
            "Unexpected decision target value."
        )

    if frame["reopening_binary"].isna().any():
        raise RuntimeError(
            "Unexpected reopening target value."
        )

    # Temporal ordering is essential.
    frame = (
        frame
        .sort_values(
            "closed_at",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    return frame


# ---------------------------------------------------------------------
# Chronological 60/20/20 split
# ---------------------------------------------------------------------

def temporal_split(
    frame: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:

    n = len(frame)

    train_end = int(
        n * 0.60
    )

    validation_end = int(
        n * 0.80
    )

    train = frame.iloc[
        :train_end
    ].copy()

    validation = frame.iloc[
        train_end:validation_end
    ].copy()

    test = frame.iloc[
        validation_end:
    ].copy()

    return (
        train,
        validation,
        test,
    )


# ---------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------

def evaluate(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, float]:

    return {
        "roc_auc": float(
            roc_auc_score(
                y_true,
                probabilities,
            )
        ),
        "pr_auc": float(
            average_precision_score(
                y_true,
                probabilities,
            )
        ),
        "accuracy": float(
            accuracy_score(
                y_true,
                predictions,
            )
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(
                y_true,
                predictions,
            )
        ),
        "precision": float(
            precision_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
    }


# ---------------------------------------------------------------------
# Tabular model
# ---------------------------------------------------------------------

def run_tabular(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target: str,
) -> dict[str, float]:

    features = [
        feature
        for feature in TABULAR_FEATURES
        if feature in train.columns
    ]

    x_train = train[
        features
    ]

    x_test = test[
        features
    ]

    y_train = train[
        target
    ].astype(int).to_numpy()

    y_test = test[
        target
    ].astype(int).to_numpy()

    imputer = SimpleImputer(
        strategy="median"
    )

    scaler = StandardScaler()

    x_train = imputer.fit_transform(
        x_train
    )

    x_test = imputer.transform(
        x_test
    )

    x_train = scaler.fit_transform(
        x_train
    )

    x_test = scaler.transform(
        x_test
    )

    model = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=42,
    )

    model.fit(
        x_train,
        y_train,
    )

    probabilities = model.predict_proba(
        x_test
    )[:, 1]

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    metrics = evaluate(
        y_test,
        probabilities,
        predictions,
    )

    metrics.update(
        {
            "representation": "tabular",
            "model": "logistic",
            "target": target,
            "feature_count": len(features),
            "test_rows": len(test),
        }
    )

    return metrics


# ---------------------------------------------------------------------
# Text model
# ---------------------------------------------------------------------

def run_text(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target: str,
) -> dict[str, float]:

    y_train = train[
        target
    ].astype(int).to_numpy()

    y_test = test[
        target
    ].astype(int).to_numpy()

    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
        strip_accents="unicode",
    )

    x_train = vectorizer.fit_transform(
        train["text"]
    )

    x_test = vectorizer.transform(
        test["text"]
    )

    model = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=42,
    )

    model.fit(
        x_train,
        y_train,
    )

    probabilities = model.predict_proba(
        x_test
    )[:, 1]

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    metrics = evaluate(
        y_test,
        probabilities,
        predictions,
    )

    metrics.update(
        {
            "representation": "text",
            "model": "tfidf_logistic",
            "target": target,
            "feature_count": x_train.shape[1],
            "test_rows": len(test),
        }
    )

    return metrics


# ---------------------------------------------------------------------
# Combined text + tabular model
# ---------------------------------------------------------------------

def run_combined(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target: str,
) -> dict[str, float]:

    features = [
        feature
        for feature in TABULAR_FEATURES
        if feature in train.columns
    ]

    y_train = train[
        target
    ].astype(int).to_numpy()

    y_test = test[
        target
    ].astype(int).to_numpy()

    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
        strip_accents="unicode",
    )

    train_text = vectorizer.fit_transform(
        train["text"]
    )

    test_text = vectorizer.transform(
        test["text"]
    )

    imputer = SimpleImputer(
        strategy="median"
    )

    scaler = StandardScaler()

    train_numeric = imputer.fit_transform(
        train[features]
    )

    test_numeric = imputer.transform(
        test[features]
    )

    train_numeric = scaler.fit_transform(
        train_numeric
    )

    test_numeric = scaler.transform(
        test_numeric
    )

    train_matrix = hstack(
        [
            train_text,
            csr_matrix(train_numeric),
        ]
    )

    test_matrix = hstack(
        [
            test_text,
            csr_matrix(test_numeric),
        ]
    )

    model = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=42,
    )

    model.fit(
        train_matrix,
        y_train,
    )

    probabilities = model.predict_proba(
        test_matrix
    )[:, 1]

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    metrics = evaluate(
        y_test,
        probabilities,
        predictions,
    )

    metrics.update(
        {
            "representation": "combined",
            "model": "tfidf_plus_tabular_logistic",
            "target": target,
            "feature_count": train_matrix.shape[1],
            "test_rows": len(test),
        }
    )

    return metrics


# ---------------------------------------------------------------------
# Target experiment
# ---------------------------------------------------------------------

def run_target(
    frame: pd.DataFrame,
    target: str,
) -> list[dict[str, float]]:

    train, validation, test = (
        temporal_split(frame)
    )

    print()
    print("=" * 72)
    print(
        f"TARGET: {target}"
    )
    print("=" * 72)

    print()
    print(
        f"Train:      {len(train):5d} "
        f"{train['closed_at'].min()} -> "
        f"{train['closed_at'].max()}"
    )

    print(
        f"Validation: {len(validation):5d} "
        f"{validation['closed_at'].min()} -> "
        f"{validation['closed_at'].max()}"
    )

    print(
        f"Test:       {len(test):5d} "
        f"{test['closed_at'].min()} -> "
        f"{test['closed_at'].max()}"
    )

    print()

    print(
        "Train positive rate:",
        f"{train[target].mean():.4f}",
    )

    print(
        "Validation positive rate:",
        f"{validation[target].mean():.4f}",
    )

    print(
        "Test positive rate:",
        f"{test[target].mean():.4f}",
    )

    results = []

    print()
    print("Running tabular model...")

    results.append(
        run_tabular(
            train,
            test,
            target,
        )
    )

    print("Running text model...")

    results.append(
        run_text(
            train,
            test,
            target,
        )
    )

    print("Running combined model...")

    results.append(
        run_combined(
            train,
            test,
            target,
        )
    )

    return results


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:

    print()
    print("=" * 72)
    print(
        "INTENTINSIGHT EXTERNAL PR PREDICTION BENCHMARK"
    )
    print("=" * 72)

    frame = load_dataset()

    print()
    print(
        "Rows:",
        len(frame),
    )

    print(
        "Created-at range:",
        frame["created_at"].min(),
        "->",
        frame["created_at"].max(),
    )

    print(
        "Closed-at range:",
        frame["closed_at"].min(),
        "->",
        frame["closed_at"].max(),
    )

    print()
    print("Decision distribution:")
    print(
        frame["decision"]
        .value_counts()
        .to_string()
    )

    print()
    print("Reopening distribution:")
    print(
        frame["reopening"]
        .value_counts()
        .to_string()
    )

    all_results = []

    all_results.extend(
        run_target(
            frame,
            "decision_binary",
        )
    )

    all_results.extend(
        run_target(
            frame,
            "reopening_binary",
        )
    )

    results = pd.DataFrame(
        all_results
    )

    results = results[
        [
            "target",
            "representation",
            "model",
            "feature_count",
            "test_rows",
            "roc_auc",
            "pr_auc",
            "accuracy",
            "balanced_accuracy",
            "precision",
            "recall",
            "f1",
        ]
    ]

    results.to_csv(
        RESULTS_PATH,
        index=False,
    )

    summary = {
        "dataset": "DeepPull Python",
        "rows": int(len(frame)),
        "created_at_min": str(
            frame["created_at"].min()
        ),
        "created_at_max": str(
            frame["created_at"].max()
        ),
        "closed_at_min": str(
            frame["closed_at"].min()
        ),
        "closed_at_max": str(
            frame["closed_at"].max()
        ),
        "decision_accept": int(
            (
                frame["decision"]
                == "accept"
            ).sum()
        ),
        "decision_reject": int(
            (
                frame["decision"]
                == "reject"
            ).sum()
        ),
        "reopening_reopened": int(
            (
                frame["reopening"]
                == "reopened"
            ).sum()
        ),
        "reopening_nonreopened": int(
            (
                frame["reopening"]
                == "nonreopened"
            ).sum()
        ),
        "split": "chronological 60/20/20 by closed_at",
        "random_seed": 42,
        "results_file": str(
            RESULTS_PATH
        ),
    }

    SUMMARY_PATH.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("RESULTS")
    print("=" * 72)
    print()

    print(
        results.to_string(
            index=False,
            float_format=lambda value:
            f"{value:.4f}",
        )
    )

    print()
    print("=" * 72)
    print("OUTPUT")
    print("=" * 72)
    print()

    print(
        "Results:",
        RESULTS_PATH,
    )

    print(
        "Summary:",
        SUMMARY_PATH,
    )

    print()
    print(
        "Database was not modified."
    )

    print(
        "No GitHub requests were made."
    )

    print(
        "No embeddings were generated."
    )

    print()


if __name__ == "__main__":
    main()
