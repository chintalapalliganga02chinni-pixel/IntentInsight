import csv
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


INPUT = Path("rework_90d_analysis.csv")
OUTPUT = Path("rework_90d_model_results.csv")

TEST_FRACTION = 0.30


BASELINE_FEATURES = [
    "total_additions",
    "total_deletions",
    "total_changes",
    "changed_file_count",
    "modified_file_count",
    "added_file_count",
    "removed_file_count",
    "renamed_file_count",
    "module_count",
    "package_count",
    "cross_package_spread",
    "module_entropy",
    "module_concentration",
    "top_module_weight",
]

DIVERGENCE_FEATURES = [
    "intent_impact_divergence",
]

INTENT_FEATURES = [
    "intent_similarity",
]


def make_features(frame, feature_names):
    x = frame[feature_names].copy()

    # PR-size variables are highly skewed.
    for column in [
        "total_additions",
        "total_deletions",
        "total_changes",
        "changed_file_count",
        "modified_file_count",
        "added_file_count",
        "removed_file_count",
        "renamed_file_count",
        "module_count",
        "package_count",
        "cross_package_spread",
    ]:
        if column in x.columns:
            x[column] = np.log1p(
                x[column].astype(float)
            )

    return x


def build_model():
    return Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=5000,
                    class_weight=None,
                    random_state=42,
                ),
            ),
        ]
    )


def evaluate(name, model, x_train, y_train, x_test, y_test):

    model.fit(x_train, y_train)

    probabilities = model.predict_proba(
        x_test
    )[:, 1]

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    brier = brier_score_loss(
        y_test,
        probabilities,
    )

    loss = log_loss(
        y_test,
        probabilities,
    )

    return {
        "model": name,
        "roc_auc": auc,
        "pr_auc": pr_auc,
        "brier": brier,
        "log_loss": loss,
        "positive_predictions": int(
            predictions.sum()
        ),
    }


print("=" * 76)
print("IntentInsight 90-Day Structural Rework Prediction")
print("=" * 76)
print()

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing {INPUT}"
    )

frame = pd.read_csv(INPUT)

frame["merged_at"] = pd.to_datetime(
    frame["merged_at"],
    utc=True,
)

frame = frame.sort_values(
    "merged_at"
).reset_index(drop=True)

if frame["rework_90d"].isna().any():
    raise RuntimeError(
        "Missing outcome values."
    )

# ----------------------------------------------------------------------
# Chronological train/test split
# ----------------------------------------------------------------------

split_index = int(
    len(frame) * (1.0 - TEST_FRACTION)
)

train = frame.iloc[
    :split_index
].copy()

test = frame.iloc[
    split_index:
].copy()

y_train = train["rework_90d"].astype(int)
y_test = test["rework_90d"].astype(int)

print(f"Total observations: {len(frame)}")
print(f"Training observations: {len(train)}")
print(f"Test observations: {len(test)}")
print()

print(
    f"Train date range: "
    f"{train['merged_at'].min()} "
    f"→ "
    f"{train['merged_at'].max()}"
)

print(
    f"Test date range:  "
    f"{test['merged_at'].min()} "
    f"→ "
    f"{test['merged_at'].max()}"
)

print()

print(
    f"Train rework rate: "
    f"{y_train.mean():.4f}"
)

print(
    f"Test rework rate:  "
    f"{y_test.mean():.4f}"
)

print()

# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

models = {
    "baseline": BASELINE_FEATURES,

    "baseline_plus_divergence":
        BASELINE_FEATURES
        + DIVERGENCE_FEATURES,

    "baseline_plus_intent":
        BASELINE_FEATURES
        + INTENT_FEATURES,

    "full_intent_divergence":
        BASELINE_FEATURES
        + INTENT_FEATURES
        + DIVERGENCE_FEATURES,
}

results = []

fitted_models = {}

for name, features in models.items():

    print("-" * 76)
    print(f"MODEL: {name}")
    print("-" * 76)

    x_train = make_features(
        train,
        features,
    )

    x_test = make_features(
        test,
        features,
    )

    model = build_model()

    result = evaluate(
        name,
        model,
        x_train,
        y_train,
        x_test,
        y_test,
    )

    results.append(result)
    fitted_models[name] = model

    print(
        f"Features: {len(features)}"
    )

    print(
        f"ROC-AUC: {result['roc_auc']:.6f}"
    )

    print(
        f"PR-AUC:  {result['pr_auc']:.6f}"
    )

    print(
        f"Brier:   {result['brier']:.6f}"
    )

    print(
        f"LogLoss: {result['log_loss']:.6f}"
    )

    print()

# ----------------------------------------------------------------------
# Incremental value
# ----------------------------------------------------------------------

result_by_name = {
    row["model"]: row
    for row in results
}

baseline = result_by_name[
    "baseline"
]

with_divergence = result_by_name[
    "baseline_plus_divergence"
]

with_intent = result_by_name[
    "baseline_plus_intent"
]

full = result_by_name[
    "full_intent_divergence"
]

print("=" * 76)
print("INCREMENTAL VALUE OF INTENT–IMPACT DIVERGENCE")
print("=" * 76)
print()

roc_delta = (
    with_divergence["roc_auc"]
    - baseline["roc_auc"]
)

pr_delta = (
    with_divergence["pr_auc"]
    - baseline["pr_auc"]
)

print(
    f"Baseline ROC-AUC:              "
    f"{baseline['roc_auc']:.6f}"
)

print(
    f"+ Divergence ROC-AUC:           "
    f"{with_divergence['roc_auc']:.6f}"
)

print(
    f"ROC-AUC improvement:            "
    f"{roc_delta:+.6f}"
)

print()

print(
    f"Baseline PR-AUC:                "
    f"{baseline['pr_auc']:.6f}"
)

print(
    f"+ Divergence PR-AUC:             "
    f"{with_divergence['pr_auc']:.6f}"
)

print(
    f"PR-AUC improvement:              "
    f"{pr_delta:+.6f}"
)

print()

print("=" * 76)
print("INTENT VS DIVERGENCE")
print("=" * 76)
print()

print(
    f"Baseline ROC-AUC:                "
    f"{baseline['roc_auc']:.6f}"
)

print(
    f"+ Intent similarity:             "
    f"{with_intent['roc_auc']:.6f}"
)

print(
    f"+ Divergence:                    "
    f"{with_divergence['roc_auc']:.6f}"
)

print(
    f"+ Intent + Divergence:           "
    f"{full['roc_auc']:.6f}"
)

print()

print("=" * 76)
print("RESULTS")
print("=" * 76)
print()

results_frame = pd.DataFrame(
    results
)

print(
    results_frame.to_string(
        index=False,
        float_format=lambda value:
            f"{value:.6f}",
    )
)

results_frame.to_csv(
    OUTPUT,
    index=False,
)

print()
print(f"Output: {OUTPUT}")
print()
print("No database records were modified.")
print("No GitHub requests were made.")
print("=" * 76)
