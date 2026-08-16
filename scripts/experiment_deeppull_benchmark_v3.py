"""
IntentInsight External Benchmark V3 — Semantic Representation

Purpose
-------
Evaluate whether semantic PR-text representations from
all-MiniLM-L6-v2 provide incremental predictive information
beyond conventional tabular features and lexical TF-IDF features.

Protocol
--------
- DeepPull Python dataset
- Chronological 60/20/20 split by closed_at
- Validation used for threshold selection
- Test used only for final evaluation
- V1 and V2 outputs are never modified
- MiniLM embeddings are cached locally

Primary metrics
---------------
ROC-AUC
PR-AUC

Secondary metrics
-----------------
Accuracy
Balanced accuracy
Precision
Recall
F1

Statistical analysis
--------------------
10,000 bootstrap estimates of AUC differences.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix, hstack

from sentence_transformers import SentenceTransformer

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
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

EMBEDDING_PATH = (
    OUTPUT_DIR /
    "deeppull_minilm_embeddings.npy"
)

EMBEDDING_META_PATH = (
    OUTPUT_DIR /
    "deeppull_minilm_embeddings_meta.json"
)

RESULTS_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_v3_results.csv"
)

BOOTSTRAP_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_v3_bootstrap.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR /
    "deeppull_benchmark_v3_summary.json"
)

MODEL_NAME = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

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
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH.resolve()}"
        )

    frame = pd.read_csv(DATA_PATH)

    # The source CSV contains a duplicated header name.
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
            "Missing or invalid closed_at values."
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

    if frame[
        "decision_binary"
    ].isna().any():
        raise RuntimeError(
            "Unexpected decision labels."
        )

    if frame[
        "reopening_binary"
    ].isna().any():
        raise RuntimeError(
            "Unexpected reopening labels."
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
):
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
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
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
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
):
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
        strip_accents="unicode",
    )

    train_x = vectorizer.fit_transform(
        train["text"]
    )

    validation_x = vectorizer.transform(
        validation["text"]
    )

    test_x = vectorizer.transform(
        test["text"]
    )

    return (
        train_x,
        validation_x,
        test_x,
    )


def load_or_create_embeddings(
    frame: pd.DataFrame,
):
    expected_shape = (
        len(frame),
        384,
    )

    if (
        EMBEDDING_PATH.exists()
        and EMBEDDING_META_PATH.exists()
    ):
        embeddings = np.load(
            EMBEDDING_PATH
        )

        metadata = json.loads(
            EMBEDDING_META_PATH.read_text(
                encoding="utf-8"
            )
        )

        if (
            tuple(embeddings.shape)
            == expected_shape
            and metadata.get(
                "model_name"
            )
            == MODEL_NAME
            and metadata.get(
                "row_count"
            )
            == len(frame)
        ):
            print(
                "Loading cached MiniLM embeddings..."
            )

            return embeddings

        print(
            "Cached embeddings do not match "
            "the current dataset. Rebuilding."
        )

    print()
    print(
        "Loading semantic model:"
    )
    print(
        MODEL_NAME
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    texts = frame[
        "text"
    ].tolist()

    print(
        f"Encoding {len(texts)} PRs..."
    )

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32,
    )

    if tuple(
        embeddings.shape
    ) != expected_shape:
        raise RuntimeError(
            "Unexpected embedding shape: "
            f"{embeddings.shape}; expected "
            f"{expected_shape}"
        )

    np.save(
        EMBEDDING_PATH,
        embeddings,
    )

    EMBEDDING_META_PATH.write_text(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "embedding_dimension": 384,
                "row_count": len(frame),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "MiniLM embeddings cached:"
    )
    print(
        EMBEDDING_PATH
    )

    return embeddings


def metrics(
    y_true,
    probabilities,
):
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


def threshold_metrics(
    y_true,
    probabilities,
    threshold,
):
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


def select_threshold(
    y_true,
    probabilities,
):
    candidates = np.linspace(
        0.05,
        0.95,
        181,
    )

    best_threshold = 0.5
    best_f1 = -1.0

    for threshold in candidates:
        current = threshold_metrics(
            y_true,
            probabilities,
            float(threshold),
        )

        if current["f1"] > best_f1:
            best_f1 = current["f1"]
            best_threshold = float(
                threshold
            )

    return best_threshold


def fit_model(
    x_train,
    y_train,
):
    model = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=SEED,
    )

    model.fit(
        x_train,
        y_train,
    )

    return model


def evaluate(
    target,
    representation,
    model_name,
    model,
    x_train,
    x_validation,
    x_test,
    y_train,
    y_validation,
    y_test,
    feature_count,
):
    print(
        f"Evaluating {representation} "
        f"+ {model_name}..."
    )

    model.fit(
        x_train,
        y_train,
    )

    validation_probability = (
        model.predict_proba(
            x_validation
        )[:, 1]
    )

    threshold = select_threshold(
        y_validation,
        validation_probability,
    )

    test_probability = (
        model.predict_proba(
            x_test
        )[:, 1]
    )

    result = {
        "target": target,
        "representation": representation,
        "model": model_name,
        "feature_count": feature_count,
        "train_rows": len(y_train),
        "validation_rows": len(
            y_validation
        ),
        "test_rows": len(y_test),
        "validation_positive_rate": float(
            y_validation.mean()
        ),
        "test_positive_rate": float(
            y_test.mean()
        ),
        "selected_threshold": threshold,
        **metrics(
            y_test,
            test_probability,
        ),
        **threshold_metrics(
            y_test,
            test_probability,
            threshold,
        ),
    }

    return result, test_probability


def bootstrap_difference(
    y_true,
    baseline_probability,
    improved_probability,
    iterations=10000,
):
    rng = np.random.default_rng(
        SEED
    )

    observed = (
        roc_auc_score(
            y_true,
            improved_probability,
        )
        -
        roc_auc_score(
            y_true,
            baseline_probability,
        )
    )

    differences = []

    n = len(y_true)

    for _ in range(iterations):
        indices = rng.integers(
            0,
            n,
            size=n,
        )

        y_sample = y_true[
            indices
        ]

        if (
            np.unique(
                y_sample
            ).size < 2
        ):
            continue

        baseline_auc = (
            roc_auc_score(
                y_sample,
                baseline_probability[
                    indices
                ],
            )
        )

        improved_auc = (
            roc_auc_score(
                y_sample,
                improved_probability[
                    indices
                ],
            )
        )

        differences.append(
            improved_auc - baseline_auc
        )

    differences = np.asarray(
        differences
    )

    return {
        "observed_delta_auc": float(
            observed
        ),
        "bootstrap_iterations": int(
            len(differences)
        ),
        "mean_delta_auc": float(
            differences.mean()
        ),
        "median_delta_auc": float(
            np.median(differences)
        ),
        "ci_lower": float(
            np.percentile(
                differences,
                2.5,
            )
        ),
        "ci_upper": float(
            np.percentile(
                differences,
                97.5,
            )
        ),
    }


def main():
    print()
    print("=" * 72)
    print(
        "INTENTINSIGHT DEEPPULL "
        "SEMANTIC BENCHMARK V3"
    )
    print("=" * 72)

    frame = load_dataset()

    print()
    print(
        f"Rows: {len(frame)}"
    )

    train, validation, test = (
        temporal_split(frame)
    )

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

    embeddings = (
        load_or_create_embeddings(
            frame
        )
    )

    train_end = len(train)
    validation_end = (
        len(train)
        + len(validation)
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

    # Combined semantic representation.
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

    # TF-IDF combined representation.
    tfidf_combined_train = hstack(
        [
            tfidf_train,
            csr_matrix(tab_train),
        ]
    )

    tfidf_combined_validation = hstack(
        [
            tfidf_validation,
            csr_matrix(tab_validation),
        ]
    )

    tfidf_combined_test = hstack(
        [
            tfidf_test,
            csr_matrix(tab_test),
        ]
    )

    all_results = []
    probability_store = {}
    bootstrap_results = []

    for target in [
        "decision_binary",
        "reopening_binary",
    ]:
        print()
        print("=" * 72)
        print(
            f"TARGET: {target}"
        )
        print("=" * 72)

        y_train = train[
            target
        ].astype(int).to_numpy()

        y_validation = validation[
            target
        ].astype(int).to_numpy()

        y_test = test[
            target
        ].astype(int).to_numpy()

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

        # Tabular.
        result, probability = evaluate(
            target,
            "tabular",
            "logistic",
            fit_model(
                tab_train,
                y_train,
            ),
            tab_train,
            tab_validation,
            tab_test,
            y_train,
            y_validation,
            y_test,
            len(TABULAR_FEATURES),
        )

        all_results.append(result)

        probability_store[
            target,
            "tabular"
        ] = probability

        # TF-IDF.
        result, probability = evaluate(
            target,
            "tfidf",
            "logistic",
            fit_model(
                tfidf_train,
                y_train,
            ),
            tfidf_train,
            tfidf_validation,
            tfidf_test,
            y_train,
            y_validation,
            y_test,
            tfidf_train.shape[1],
        )

        all_results.append(result)

        probability_store[
            target,
            "tfidf"
        ] = probability

        # Tabular + TF-IDF.
        result, probability = evaluate(
            target,
            "tabular_plus_tfidf",
            "logistic",
            fit_model(
                tfidf_combined_train,
                y_train,
            ),
            tfidf_combined_train,
            tfidf_combined_validation,
            tfidf_combined_test,
            y_train,
            y_validation,
            y_test,
            tfidf_combined_train.shape[1],
        )

        all_results.append(result)

        probability_store[
            target,
            "tabular_plus_tfidf"
        ] = probability

        # MiniLM semantic.
        result, probability = evaluate(
            target,
            "minilm",
            "logistic",
            fit_model(
                semantic_train,
                y_train,
            ),
            semantic_train,
            semantic_validation,
            semantic_test,
            y_train,
            y_validation,
            y_test,
            semantic_train.shape[1],
        )

        all_results.append(result)

        probability_store[
            target,
            "minilm"
        ] = probability

        # Tabular + MiniLM.
        result, probability = evaluate(
            target,
            "tabular_plus_minilm",
            "logistic",
            fit_model(
                semantic_combined_train,
                y_train,
            ),
            semantic_combined_train,
            semantic_combined_validation,
            semantic_combined_test,
            y_train,
            y_validation,
            y_test,
            semantic_combined_train.shape[1],
        )

        all_results.append(result)

        probability_store[
            target,
            "tabular_plus_minilm"
        ] = probability

        # Semantic incremental value over tabular.
        bootstrap_results.append(
            {
                "target": target,
                "comparison": (
                    "tabular_plus_minilm"
                    " - tabular"
                ),
                **bootstrap_difference(
                    y_test,
                    probability_store[
                        target,
                        "tabular"
                    ],
                    probability_store[
                        target,
                        "tabular_plus_minilm"
                    ],
                ),
            }
        )

        # Semantic versus lexical combined representation.
        bootstrap_results.append(
            {
                "target": target,
                "comparison": (
                    "tabular_plus_minilm"
                    " - tabular_plus_tfidf"
                ),
                **bootstrap_difference(
                    y_test,
                    probability_store[
                        target,
                        "tabular_plus_tfidf"
                    ],
                    probability_store[
                        target,
                        "tabular_plus_minilm"
                    ],
                ),
            }
        )

    results_frame = pd.DataFrame(
        all_results
    )

    bootstrap_frame = pd.DataFrame(
        bootstrap_results
    )

    results_frame.to_csv(
        RESULTS_PATH,
        index=False,
    )

    bootstrap_frame.to_csv(
        BOOTSTRAP_PATH,
        index=False,
    )

    summary = {
        "dataset": "DeepPull Python",
        "rows": len(frame),
        "model": MODEL_NAME,
        "embedding_dimension": 384,
        "split": (
            "chronological 60/20/20 "
            "by closed_at"
        ),
        "random_seed": SEED,
        "bootstrap_iterations": 10000,
        "embedding_cache": str(
            EMBEDDING_PATH
        ),
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
    print(
        "V3 RESULTS"
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
        "SEMANTIC INCREMENTAL AUC"
    )
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
    print(
        "OUTPUT"
    )
    print("=" * 72)
    print()

    print(
        f"Embeddings: {EMBEDDING_PATH}"
    )

    print(
        f"Results:    {RESULTS_PATH}"
    )

    print(
        f"Bootstrap:  {BOOTSTRAP_PATH}"
    )

    print(
        f"Summary:    {SUMMARY_PATH}"
    )

    print()
    print(
        "V1 and V2 outputs were not modified."
    )

    print(
        "Database was not modified."
    )

    print(
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()
