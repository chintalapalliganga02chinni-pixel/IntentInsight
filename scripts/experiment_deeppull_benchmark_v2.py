"""
IntentInsight External Benchmark V2 — DeepPull Python Dataset

Research question
-----------------
Does textual pull-request information provide incremental predictive
value beyond conventional PR/project/contributor features under a
strict chronological evaluation?

V2 improvements over V1
------------------------
- Proper chronological 60/20/20 train/validation/test protocol.
- Validation-based model/threshold selection.
- Majority-class baseline.
- Linear and nonlinear tabular models.
- TF-IDF text model.
- Combined tabular + text model.
- ROC-AUC and PR-AUC as primary discrimination metrics.
- Bootstrap confidence interval for incremental AUC.
- Test set is locked until final evaluation.

The V1 benchmark is not modified.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix, hstack

from sklearn.ensemble import HistGradientBoostingClassifier
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
    "deeppull_benchmark_v2_results.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_v2_summary.json"
)

BOOTSTRAP_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_v2_bootstrap.csv"
)


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


def load_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH.resolve()}"
        )

    frame = pd.read_csv(DATA_PATH)

    if "PJ_num_prev_pr_merged.1" in frame.columns:
        frame = frame.rename(
            columns={
                "PJ_num_prev_pr_merged.1":
                "PJ_num_prev_pr_rejected"
            }
        )

    required = {
        "created_at",
        "closed_at",
        "title",
        "body",
        "decision",
        "reopening",
        *TABULAR_FEATURES,
    }

    missing = sorted(
        required - set(frame.columns)
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
            "Invalid or missing closed_at values."
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
            "Unexpected decision target values."
        )

    if frame["reopening_binary"].isna().any():
        raise RuntimeError(
            "Unexpected reopening target values."
        )

    return (
        frame
        .sort_values(
            "closed_at",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )


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

    return (
        frame.iloc[:train_end].copy(),
        frame.iloc[
            train_end:validation_end
        ].copy(),
        frame.iloc[
            validation_end:
        ].copy(),
    )


def metrics_at_threshold(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, float]:

    predictions = (
        probabilities >= threshold
    ).astype(int)

    return {
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


def discrimination_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
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
    }


def select_threshold(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> float:

    candidates = np.linspace(
        0.05,
        0.95,
        181,
    )

    best_threshold = 0.5
    best_score = -np.inf

    for threshold in candidates:
        metrics = metrics_at_threshold(
            y_true,
            probabilities,
            float(threshold),
        )

        score = metrics["f1"]

        if score > best_score:
            best_score = score
            best_threshold = float(
                threshold
            )

    return best_threshold


def prepare_tabular(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
):
    features = [
        feature
        for feature in TABULAR_FEATURES
        if feature in train.columns
    ]

    imputer = SimpleImputer(
        strategy="median"
    )

    scaler = StandardScaler()

    x_train = imputer.fit_transform(
        train[features]
    )

    x_validation = imputer.transform(
        validation[features]
    )

    x_test = imputer.transform(
        test[features]
    )

    x_train = scaler.fit_transform(
        x_train
    )

    x_validation = scaler.transform(
        x_validation
    )

    x_test = scaler.transform(
        x_test
    )

    return (
        x_train,
        x_validation,
        x_test,
        len(features),
    )


def prepare_text(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    max_features: int = 20000,
):
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
        strip_accents="unicode",
    )

    x_train = vectorizer.fit_transform(
        train["text"]
    )

    x_validation = vectorizer.transform(
        validation["text"]
    )

    x_test = vectorizer.transform(
        test["text"]
    )

    return (
        x_train,
        x_validation,
        x_test,
        x_train.shape[1],
    )


def prepare_combined(
    tabular_train,
    tabular_validation,
    tabular_test,
    text_train,
    text_validation,
    text_test,
):
    return (
        hstack(
            [
                text_train,
                csr_matrix(
                    tabular_train
                ),
            ]
        ),
        hstack(
            [
                text_validation,
                csr_matrix(
                    tabular_validation
                ),
            ]
        ),
        hstack(
            [
                text_test,
                csr_matrix(
                    tabular_test
                ),
            ]
        ),
    )


def fit_logistic(
    x_train,
    y_train,
):
    model = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=42,
    )

    model.fit(
        x_train,
        y_train,
    )

    return model


def fit_hist_gradient_boosting(
    x_train,
    y_train,
):
    model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )

    model.fit(
        x_train,
        y_train,
    )

    return model


def run_model(
    model_name: str,
    representation: str,
    model,
    x_train,
    x_validation,
    x_test,
    y_train,
    y_validation,
    y_test,
    target: str,
    feature_count: int,
):
    model.fit(
        x_train,
        y_train,
    )

    validation_probabilities = (
        model.predict_proba(
            x_validation
        )[:, 1]
    )

    threshold = select_threshold(
        y_validation,
        validation_probabilities,
    )

    test_probabilities = (
        model.predict_proba(
            x_test
        )[:, 1]
    )

    discrimination = (
        discrimination_metrics(
            y_test,
            test_probabilities,
        )
    )

    threshold_metrics = (
        metrics_at_threshold(
            y_test,
            test_probabilities,
            threshold,
        )
    )

    result = {
        "target": target,
        "representation": representation,
        "model": model_name,
        "feature_count": feature_count,
        "train_rows": len(y_train),
        "validation_rows": len(y_validation),
        "test_rows": len(y_test),
        "validation_positive_rate": float(
            y_validation.mean()
        ),
        "test_positive_rate": float(
            y_test.mean()
        ),
        "selected_threshold": threshold,
        **discrimination,
        **threshold_metrics,
    }

    return (
        result,
        test_probabilities,
    )


def majority_baseline(
    y_train: np.ndarray,
    y_test: np.ndarray,
    target: str,
):
    probability = float(
        y_train.mean()
    )

    probabilities = np.full(
        len(y_test),
        probability,
    )

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    result = {
        "target": target,
        "representation": "baseline",
        "model": "majority_class",
        "feature_count": 0,
        "train_rows": len(y_train),
        "validation_rows": 0,
        "test_rows": len(y_test),
        "validation_positive_rate": np.nan,
        "test_positive_rate": float(
            y_test.mean()
        ),
        "selected_threshold": 0.5,
        **discrimination_metrics(
            y_test,
            probabilities,
        ),
        **metrics_at_threshold(
            y_test,
            probabilities,
            0.5,
        ),
    }

    return result, probabilities


def bootstrap_auc_difference(
    y_true: np.ndarray,
    baseline_probabilities: np.ndarray,
    improved_probabilities: np.ndarray,
    iterations: int = 10000,
    seed: int = 42,
):
    rng = np.random.default_rng(
        seed
    )

    n = len(y_true)

    observed = (
        roc_auc_score(
            y_true,
            improved_probabilities,
        )
        -
        roc_auc_score(
            y_true,
            baseline_probabilities,
        )
    )

    differences = []

    for _ in range(iterations):
        indices = rng.integers(
            0,
            n,
            size=n,
        )

        y_sample = y_true[
            indices
        ]

        # AUC is undefined if a bootstrap sample contains only
        # one class, so retry through the next iteration.
        if (
            np.unique(
                y_sample
            ).size < 2
        ):
            continue

        baseline_auc = roc_auc_score(
            y_sample,
            baseline_probabilities[
                indices
            ],
        )

        improved_auc = roc_auc_score(
            y_sample,
            improved_probabilities[
                indices
            ],
        )

        differences.append(
            improved_auc - baseline_auc
        )

    differences = np.asarray(
        differences
    )

    lower = float(
        np.percentile(
            differences,
            2.5,
        )
    )

    upper = float(
        np.percentile(
            differences,
            97.5,
        )
    )

    return {
        "observed_delta_auc": float(
            observed
        ),
        "bootstrap_iterations": int(
            len(differences)
        ),
        "ci_lower": lower,
        "ci_upper": upper,
        "mean_delta_auc": float(
            differences.mean()
        ),
        "median_delta_auc": float(
            np.median(differences)
        ),
    }


def run_target(
    frame: pd.DataFrame,
    target: str,
):
    train, validation, test = (
        temporal_split(frame)
    )

    y_train = train[
        target
    ].astype(int).to_numpy()

    y_validation = validation[
        target
    ].astype(int).to_numpy()

    y_test = test[
        target
    ].astype(int).to_numpy()

    print()
    print("=" * 72)
    print(
        f"TARGET: {target}"
    )
    print("=" * 72)

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
        f"Train positive rate:      "
        f"{y_train.mean():.4f}"
    )

    print(
        f"Validation positive rate: "
        f"{y_validation.mean():.4f}"
    )

    print(
        f"Test positive rate:       "
        f"{y_test.mean():.4f}"
    )

    print()
    print("Preparing tabular features...")

    (
        tab_train,
        tab_validation,
        tab_test,
        tab_count,
    ) = prepare_tabular(
        train,
        validation,
        test,
    )

    print("Preparing TF-IDF features...")

    (
        text_train,
        text_validation,
        text_test,
        text_count,
    ) = prepare_text(
        train,
        validation,
        test,
    )

    (
        combined_train,
        combined_validation,
        combined_test,
    ) = prepare_combined(
        tab_train,
        tab_validation,
        tab_test,
        text_train,
        text_validation,
        text_test,
    )

    results = []
    probabilities = {}

    print("Evaluating majority baseline...")

    baseline_result, baseline_probability = (
        majority_baseline(
            y_train,
            y_test,
            target,
        )
    )

    results.append(
        baseline_result
    )

    probabilities[
        "majority"
    ] = baseline_probability

    print("Evaluating tabular logistic...")

    result, probability = run_model(
        "logistic",
        "tabular",
        fit_logistic(
            tab_train,
            y_train,
        ),
        tab_train,
        tab_validation,
        tab_test,
        y_train,
        y_validation,
        y_test,
        target,
        tab_count,
    )

    results.append(result)
    probabilities[
        "tabular_logistic"
    ] = probability

    print("Evaluating tabular gradient boosting...")

    result, probability = run_model(
        "hist_gradient_boosting",
        "tabular",
        fit_hist_gradient_boosting(
            tab_train,
            y_train,
        ),
        tab_train,
        tab_validation,
        tab_test,
        y_train,
        y_validation,
        y_test,
        target,
        tab_count,
    )

    results.append(result)
    probabilities[
        "tabular_boosting"
    ] = probability

    print("Evaluating TF-IDF text...")

    result, probability = run_model(
        "tfidf_logistic",
        "text",
        fit_logistic(
            text_train,
            y_train,
        ),
        text_train,
        text_validation,
        text_test,
        y_train,
        y_validation,
        y_test,
        target,
        text_count,
    )

    results.append(result)
    probabilities[
        "text"
    ] = probability

    print("Evaluating combined model...")

    result, probability = run_model(
        "tfidf_plus_tabular_logistic",
        "combined",
        fit_logistic(
            combined_train,
            y_train,
        ),
        combined_train,
        combined_validation,
        combined_test,
        y_train,
        y_validation,
        y_test,
        target,
        combined_train.shape[1],
    )

    results.append(result)
    probabilities[
        "combined"
    ] = probability

    print("Evaluating combined gradient boosting...")

    # HistGradientBoosting requires dense matrices. The combined
    # TF-IDF representation is intentionally too large to densify.
    # Therefore this model is only applied to tabular data above.
    print(
        "Skipped: dense boosting of combined TF-IDF representation."
    )

    return (
        results,
        probabilities,
        y_test,
    )


def main() -> None:
    print()
    print("=" * 72)
    print(
        "INTENTINSIGHT DEEPPULL BENCHMARK V2"
    )
    print("=" * 72)

    frame = load_dataset()

    print()
    print(
        "Rows:",
        len(frame),
    )

    print(
        "Closed-at range:",
        frame["closed_at"].min(),
        "->",
        frame["closed_at"].max(),
    )

    all_results = []
    bootstrap_results = []

    for target in [
        "decision_binary",
        "reopening_binary",
    ]:
        (
            results,
            probabilities,
            y_test,
        ) = run_target(
            frame,
            target,
        )

        all_results.extend(
            results
        )

        if (
            "tabular_logistic" in probabilities
            and "combined" in probabilities
        ):
            bootstrap = (
                bootstrap_auc_difference(
                    y_test,
                    probabilities[
                        "tabular_logistic"
                    ],
                    probabilities[
                        "combined"
                    ],
                    iterations=10000,
                    seed=42,
                )
            )

            bootstrap[
                "target"
            ] = target

            bootstrap_results.append(
                bootstrap
            )

    results_frame = pd.DataFrame(
        all_results
    )

    results_frame.to_csv(
        RESULTS_PATH,
        index=False,
    )

    bootstrap_frame = pd.DataFrame(
        bootstrap_results
    )

    bootstrap_frame.to_csv(
        BOOTSTRAP_PATH,
        index=False,
    )

    summary = {
        "dataset": "DeepPull Python",
        "rows": int(len(frame)),
        "split": (
            "chronological 60/20/20 "
            "by closed_at"
        ),
        "random_seed": 42,
        "bootstrap_iterations": 10000,
        "results_file": str(
            RESULTS_PATH
        ),
        "bootstrap_file": str(
            BOOTSTRAP_PATH
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
    print("V2 RESULTS")
    print("=" * 72)
    print()

    print(
        results_frame.to_string(
            index=False,
            float_format=lambda x:
            f"{x:.4f}",
        )
    )

    print()
    print("=" * 72)
    print("INCREMENTAL AUC")
    print("=" * 72)
    print()

    print(
        bootstrap_frame.to_string(
            index=False,
            float_format=lambda x:
            f"{x:.6f}",
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
        "Bootstrap:",
        BOOTSTRAP_PATH,
    )

    print(
        "Summary:",
        SUMMARY_PATH,
    )

    print()
    print(
        "V1 results were not modified."
    )

    print(
        "Database was not modified."
    )

    print(
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()
