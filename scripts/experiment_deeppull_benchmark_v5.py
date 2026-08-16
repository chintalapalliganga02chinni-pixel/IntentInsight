"""IntentInsight DeepPull V5 — historical structural anomaly benchmark."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

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


DATA_PATH = Path("datasets/external/deeppull/python.csv")

OUTPUT_DIR = Path(
    "results/external/deeppull/deeppull_benchmark_v5"
)
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

RESULTS_PATH = OUTPUT_DIR / "results.csv"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"

SEED = 42

STRUCTURAL_FEATURES = [
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
]


def load_dataset() -> pd.DataFrame:
    frame = pd.read_csv(DATA_PATH)

    if "PJ_num_prev_pr_merged.1" in frame.columns:
        frame = frame.rename(
            columns={
                "PJ_num_prev_pr_merged.1":
                "PJ_num_prev_pr_rejected"
            }
        )

    required = {
        "closed_at",
        "decision",
        "reopening",
        *STRUCTURAL_FEATURES,
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise RuntimeError(
            "Missing columns: "
            + ", ".join(missing)
        )

    frame["closed_at"] = pd.to_datetime(
        frame["closed_at"],
        errors="coerce",
    )

    frame = frame.dropna(
        subset=["closed_at"]
    )

    frame["decision_binary"] = (
        frame["decision"]
        .map({"accept": 1, "reject": 0})
        .astype(int)
    )

    frame["reopening_binary"] = (
        frame["reopening"]
        .map({"reopened": 1, "nonreopened": 0})
        .astype(int)
    )

    frame = frame.sort_values(
        "closed_at"
    ).reset_index(drop=True)

    return frame


def chronological_split(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    n = len(frame)

    train_end = int(0.60 * n)
    validation_end = int(0.80 * n)

    return (
        frame.iloc[:train_end].copy(),
        frame.iloc[train_end:validation_end].copy(),
        frame.iloc[validation_end:].copy(),
    )


def fit_baselines(
    train: pd.DataFrame,
) -> dict[str, tuple[float, float]]:

    baselines = {}

    for feature in STRUCTURAL_FEATURES:
        values = pd.to_numeric(
            train[feature],
            errors="coerce",
        ).to_numpy(dtype=float)

        values = values[np.isfinite(values)]

        if len(values) == 0:
            baselines[feature] = (0.0, 0.0)
            continue

        median = float(np.median(values))

        mad = float(
            np.median(
                np.abs(values - median)
            )
        )

        baselines[feature] = (
            median,
            mad,
        )

    return baselines


def make_anomaly_features(
    frame: pd.DataFrame,
    baselines: dict[str, tuple[float, float]],
) -> pd.DataFrame:

    output = {}

    for feature in STRUCTURAL_FEATURES:

        values = pd.to_numeric(
            frame[feature],
            errors="coerce",
        ).to_numpy(dtype=float)

        median, mad = baselines[feature]

        if mad <= 0:
            anomaly = np.zeros(
                len(values),
                dtype=float,
            )
        else:
            anomaly = (
                0.67448975
                * (values - median)
                / mad
            )

        anomaly = np.nan_to_num(
            anomaly,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        output[
            f"{feature}_anomaly"
        ] = np.abs(anomaly)

    return pd.DataFrame(
        output,
        index=frame.index,
    )


def evaluate(
    name: str,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict:

    imputer = SimpleImputer(
        strategy="median"
    )

    scaler = StandardScaler()

    X_train_i = imputer.fit_transform(
        X_train
    )

    X_test_i = imputer.transform(
        X_test
    )

    X_train_s = scaler.fit_transform(
        X_train_i
    )

    X_test_s = scaler.transform(
        X_test_i
    )

    model = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=SEED,
    )

    model.fit(
        X_train_s,
        y_train,
    )

    probabilities = model.predict_proba(
        X_test_s
    )[:, 1]

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    return {
        "representation": name,
        "feature_count": X_train.shape[1],
        "test_rows": len(y_test),
        "positive_rate": float(y_test.mean()),
        "roc_auc": float(
            roc_auc_score(
                y_test,
                probabilities,
            )
        ),
        "pr_auc": float(
            average_precision_score(
                y_test,
                probabilities,
            )
        ),
        "accuracy": float(
            accuracy_score(
                y_test,
                predictions,
            )
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(
                y_test,
                predictions,
            )
        ),
        "precision": float(
            precision_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
    }


def run_target(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    target: str,
    anomaly_train: pd.DataFrame,
    anomaly_test: pd.DataFrame,
) -> list[dict]:

    y_train = train[target]
    y_test = test[target]

    raw_train = train[
        STRUCTURAL_FEATURES
    ]

    raw_test = test[
        STRUCTURAL_FEATURES
    ]

    combined_train = pd.concat(
        [
            raw_train.reset_index(drop=True),
            anomaly_train.reset_index(drop=True),
        ],
        axis=1,
    )

    combined_test = pd.concat(
        [
            raw_test.reset_index(drop=True),
            anomaly_test.reset_index(drop=True),
        ],
        axis=1,
    )

    results = []

    print(
        f"\nTARGET: {target}"
    )

    print(
        "Evaluating raw structural features..."
    )

    results.append(
        {
            "target": target,
            **evaluate(
                "raw_structural",
                raw_train,
                raw_test,
                y_train,
                y_test,
            ),
        }
    )

    print(
        "Evaluating historical anomaly features..."
    )

    results.append(
        {
            "target": target,
            **evaluate(
                "historical_anomaly",
                anomaly_train,
                anomaly_test,
                y_train,
                y_test,
            ),
        }
    )

    print(
        "Evaluating combined representation..."
    )

    results.append(
        {
            "target": target,
            **evaluate(
                "raw_plus_anomaly",
                combined_train,
                combined_test,
                y_train,
                y_test,
            ),
        }
    )

    return results


def main() -> None:

    print("=" * 72)
    print(
        "INTENTINSIGHT DEEPPULL V5"
    )
    print(
        "HISTORICAL STRUCTURAL ANOMALY BENCHMARK"
    )
    print("=" * 72)

    frame = load_dataset()

    print(
        f"\nRows: {len(frame)}"
    )

    train, validation, test = (
        chronological_split(frame)
    )

    print(
        f"Train:      {len(train)}"
    )
    print(
        f"Validation: {len(validation)}"
    )
    print(
        f"Test:       {len(test)}"
    )

    baselines = fit_baselines(
        train
    )

    anomaly_train = make_anomaly_features(
        train,
        baselines,
    )

    anomaly_validation = make_anomaly_features(
        validation,
        baselines,
    )

    anomaly_test = make_anomaly_features(
        test,
        baselines,
    )

    # Validation is deliberately generated but not used
    # for fitting the test model. It is retained for
    # protocol transparency and future threshold selection.
    del anomaly_validation

    results = []

    results.extend(
        run_target(
            train,
            validation,
            test,
            "decision_binary",
            anomaly_train,
            anomaly_test,
        )
    )

    results.extend(
        run_target(
            train,
            validation,
            test,
            "reopening_binary",
            anomaly_train,
            anomaly_test,
        )
    )

    results_frame = pd.DataFrame(
        results
    )

    print("\n")
    print(
        results_frame.to_string(
            index=False
        )
    )

    results_frame.to_csv(
        RESULTS_PATH,
        index=False,
    )

    summary = {
        "dataset": "DeepPull Python",
        "rows": len(frame),
        "split": "chronological 60/20/20 by closed_at",
        "random_seed": SEED,
        "baseline_type": "training-period median/MAD",
        "structural_features": STRUCTURAL_FEATURES,
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

    print(
        f"\nResults: {RESULTS_PATH}"
    )

    print(
        f"Summary: {SUMMARY_PATH}"
    )

    print(
        "\nDatabase was not modified."
    )


if __name__ == "__main__":
    main()
