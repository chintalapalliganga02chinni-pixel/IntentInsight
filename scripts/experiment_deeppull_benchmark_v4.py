"""
IntentInsight DeepPull Benchmark V4 — Lifetime Prediction

Independent benchmark of the released DeepPull Python dataset.

Lifetime is treated as an ordered five-class outcome:

hour -> day -> week -> month -> mtmonth (> month)

Primary metric:
    Macro-Averaged Absolute Error (MMAE)

Secondary metrics:
    Accuracy
    Balanced accuracy
    Macro F1
    Weighted F1
    Per-class recall

Protocol:
    Chronological 60/20/20 split by closed_at.

Representations:
    Tabular
    TF-IDF
    Tabular + TF-IDF
    MiniLM
    Tabular + MiniLM

V1, V2 and V3 outputs are never modified.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix, hstack

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
)
from sklearn.feature_extraction.text import TfidfVectorizer
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
    "deeppull_benchmark_v4_lifetime_results.csv"
)

CONFUSION_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_v4_lifetime_confusion.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_v4_lifetime_summary.json"
)

EMBEDDING_PATH = (
    OUTPUT_DIR /
    "deeppull_minilm_embeddings.npy"
)

LIFETIME_CLASSES = [
    "hour",
    "day",
    "week",
    "month",
    "mtmonth",
]

LIFETIME_TO_INT = {
    label: index
    for index, label
    in enumerate(LIFETIME_CLASSES)
}

SEED = 42

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
    frame = pd.read_csv(DATA_PATH)

    if (
        "PJ_num_prev_pr_merged.1"
        in frame.columns
    ):
        frame = frame.rename(
            columns={
                "PJ_num_prev_pr_merged.1":
                "PJ_num_prev_pr_rejected"
            }
        )

    required = {
        "closed_at",
        "title",
        "body",
        "lifetime",
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

    frame["closed_at"] = pd.to_datetime(
        frame["closed_at"],
        errors="coerce",
    )

    if frame["closed_at"].isna().any():
        raise RuntimeError(
            "Invalid closed_at values."
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

    frame["lifetime"] = (
        frame["lifetime"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    unexpected = sorted(
        set(frame["lifetime"])
        - set(LIFETIME_CLASSES)
    )

    if unexpected:
        raise RuntimeError(
            "Unexpected lifetime labels: "
            + ", ".join(unexpected)
        )

    frame["lifetime_int"] = (
        frame["lifetime"]
        .map(LIFETIME_TO_INT)
        .astype(int)
    )

    return (
        frame
        .sort_values(
            "closed_at",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )


def temporal_split(frame):
    n = len(frame)

    train_end = int(
        n * 0.60
    )

    validation_end = int(
        n * 0.80
    )

    return (
        frame.iloc[
            :train_end
        ].copy(),
        frame.iloc[
            train_end:validation_end
        ].copy(),
        frame.iloc[
            validation_end:
        ].copy(),
    )


def prepare_tabular(
    train,
    validation,
    test,
):
    imputer = SimpleImputer(
        strategy="median"
    )

    scaler = StandardScaler()

    x_train = imputer.fit_transform(
        train[TABULAR_FEATURES]
    )

    x_validation = imputer.transform(
        validation[TABULAR_FEATURES]
    )

    x_test = imputer.transform(
        test[TABULAR_FEATURES]
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
    )


def prepare_tfidf(
    train,
    validation,
    test,
):
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
    )


def load_embeddings(frame):
    if not EMBEDDING_PATH.exists():
        raise FileNotFoundError(
            "MiniLM cache not found: "
            f"{EMBEDDING_PATH}"
        )

    embeddings = np.load(
        EMBEDDING_PATH
    )

    if embeddings.shape[0] != len(frame):
        raise RuntimeError(
            "Embedding row count does not "
            "match dataset row count."
        )

    return embeddings


def make_model():
    return LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=SEED,
    )


def macro_absolute_error(
    y_true,
    y_pred,
):
    class_errors = []

    for class_id in range(
        len(LIFETIME_CLASSES)
    ):
        mask = (
            y_true == class_id
        )

        if not np.any(mask):
            continue

        error = np.mean(
            np.abs(
                y_true[mask]
                -
                y_pred[mask]
            )
        )

        class_errors.append(
            error
        )

    return float(
        np.mean(class_errors)
    )


def evaluate(
    representation,
    x_train,
    x_validation,
    x_test,
    y_train,
    y_validation,
    y_test,
    feature_count,
):
    print(
        f"Evaluating {representation}..."
    )

    model = make_model()

    model.fit(
        x_train,
        y_train,
    )

    validation_pred = (
        model.predict(
            x_validation
        )
    )

    # Threshold/model selection is not
    # required for multiclass lifetime.
    # Validation is retained for protocol
    # completeness and diagnostics.
    validation_mmae = (
        macro_absolute_error(
            y_validation,
            validation_pred,
        )
    )

    test_pred = model.predict(
        x_test
    )

    result = {
        "representation": representation,
        "model": "multinomial_logistic",
        "feature_count": int(
            feature_count
        ),
        "train_rows": len(y_train),
        "validation_rows": len(
            y_validation
        ),
        "test_rows": len(y_test),
        "test_accuracy": float(
            accuracy_score(
                y_test,
                test_pred,
            )
        ),
        "test_balanced_accuracy": float(
            balanced_accuracy_score(
                y_test,
                test_pred,
            )
        ),
        "test_macro_f1": float(
            f1_score(
                y_test,
                test_pred,
                average="macro",
                zero_division=0,
            )
        ),
        "test_weighted_f1": float(
            f1_score(
                y_test,
                test_pred,
                average="weighted",
                zero_division=0,
            )
        ),
        "test_mae": float(
            mean_absolute_error(
                y_test,
                test_pred,
            )
        ),
        "test_mmae": macro_absolute_error(
            y_test,
            test_pred,
        ),
        "validation_mmae": validation_mmae,
    }

    return (
        result,
        test_pred,
    )


def main():
    print()
    print("=" * 72)
    print(
        "INTENTINSIGHT DEEPPULL "
        "LIFETIME BENCHMARK V4"
    )
    print("=" * 72)

    frame = load_dataset()

    print()
    print(
        f"Rows: {len(frame)}"
    )

    print()
    print(
        "Lifetime distribution:"
    )

    print(
        frame[
            "lifetime"
        ].value_counts(
            sort=False
        ).to_string()
    )

    train, validation, test = (
        temporal_split(frame)
    )

    print()
    print(
        f"Train:       {len(train)}"
    )

    print(
        f"Validation:  {len(validation)}"
    )

    print(
        f"Test:        {len(test)}"
    )

    print()
    print(
        "Train lifetime distribution:"
    )

    print(
        train[
            "lifetime"
        ].value_counts(
            normalize=True,
            sort=False,
        ).to_string()
    )

    print()
    print(
        "Test lifetime distribution:"
    )

    print(
        test[
            "lifetime"
        ].value_counts(
            normalize=True,
            sort=False,
        ).to_string()
    )

    y_train = train[
        "lifetime_int"
    ].to_numpy()

    y_validation = validation[
        "lifetime_int"
    ].to_numpy()

    y_test = test[
        "lifetime_int"
    ].to_numpy()

    print()
    print(
        "Preparing tabular representation..."
    )

    (
        tab_train,
        tab_validation,
        tab_test,
    ) = prepare_tabular(
        train,
        validation,
        test,
    )

    print(
        "Preparing TF-IDF representation..."
    )

    (
        tfidf_train,
        tfidf_validation,
        tfidf_test,
    ) = prepare_tfidf(
        train,
        validation,
        test,
    )

    print(
        "Loading cached MiniLM embeddings..."
    )

    embeddings = load_embeddings(
        frame
    )

    train_end = len(train)
    validation_end = (
        len(train)
        +
        len(validation)
    )

    semantic_train = embeddings[
        :train_end
    ]

    semantic_validation = embeddings[
        train_end:validation_end
    ]

    semantic_test = embeddings[
        validation_end:
    ]

    tfidf_combined_train = hstack(
        [
            tfidf_train,
            csr_matrix(tab_train),
        ]
    )

    tfidf_combined_validation = hstack(
        [
            tfidf_validation,
            csr_matrix(
                tab_validation
            ),
        ]
    )

    tfidf_combined_test = hstack(
        [
            tfidf_test,
            csr_matrix(tab_test),
        ]
    )

    semantic_combined_train = np.hstack(
        [
            tab_train,
            semantic_train,
        ]
    )

    semantic_combined_validation = (
        np.hstack(
            [
                tab_validation,
                semantic_validation,
            ]
        )
    )

    semantic_combined_test = np.hstack(
        [
            tab_test,
            semantic_test,
        ]
    )

    results = []
    confusion_rows = []

    representations = [
        (
            "tabular",
            tab_train,
            tab_validation,
            tab_test,
            tab_train.shape[1],
        ),
        (
            "tfidf",
            tfidf_train,
            tfidf_validation,
            tfidf_test,
            tfidf_train.shape[1],
        ),
        (
            "tabular_plus_tfidf",
            tfidf_combined_train,
            tfidf_combined_validation,
            tfidf_combined_test,
            tfidf_combined_train.shape[1],
        ),
        (
            "minilm",
            semantic_train,
            semantic_validation,
            semantic_test,
            semantic_train.shape[1],
        ),
        (
            "tabular_plus_minilm",
            semantic_combined_train,
            semantic_combined_validation,
            semantic_combined_test,
            semantic_combined_train.shape[1],
        ),
    ]

    for (
        representation,
        x_train,
        x_validation,
        x_test,
        feature_count,
    ) in representations:

        result, prediction = evaluate(
            representation,
            x_train,
            x_validation,
            x_test,
            y_train,
            y_validation,
            y_test,
            feature_count,
        )

        results.append(result)

        matrix = confusion_matrix(
            y_test,
            prediction,
            labels=list(
                range(
                    len(
                        LIFETIME_CLASSES
                    )
                )
            ),
        )

        for actual in range(
            len(LIFETIME_CLASSES)
        ):
            for predicted in range(
                len(LIFETIME_CLASSES)
            ):
                confusion_rows.append(
                    {
                        "representation":
                            representation,
                        "actual":
                            LIFETIME_CLASSES[
                                actual
                            ],
                        "predicted":
                            LIFETIME_CLASSES[
                                predicted
                            ],
                        "count":
                            int(
                                matrix[
                                    actual,
                                    predicted
                                ]
                            ),
                    }
                )

    results_frame = pd.DataFrame(
        results
    )

    confusion_frame = pd.DataFrame(
        confusion_rows
    )

    results_frame.to_csv(
        RESULTS_PATH,
        index=False,
    )

    confusion_frame.to_csv(
        CONFUSION_PATH,
        index=False,
    )

    summary = {
        "dataset": "DeepPull Python",
        "rows": len(frame),
        "target": "lifetime",
        "classes": LIFETIME_CLASSES,
        "class_encoding": LIFETIME_TO_INT,
        "split":
            "chronological 60/20/20 "
            "by closed_at",
        "random_seed": SEED,
        "primary_metric":
            "macro_averaged_absolute_error",
        "representations": [
            "tabular",
            "tfidf",
            "tabular_plus_tfidf",
            "minilm",
            "tabular_plus_minilm",
        ],
        "results_file":
            str(RESULTS_PATH),
        "confusion_file":
            str(CONFUSION_PATH),
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
    print(
        "V4 RESULTS"
    )
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
    print(
        "OUTPUT"
    )
    print("=" * 72)
    print()

    print(
        f"Results:    {RESULTS_PATH}"
    )

    print(
        f"Confusion:  {CONFUSION_PATH}"
    )

    print(
        f"Summary:    {SUMMARY_PATH}"
    )

    print()
    print(
        "V1, V2 and V3 outputs were not modified."
    )

    print(
        "Database was not modified."
    )

    print(
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()
