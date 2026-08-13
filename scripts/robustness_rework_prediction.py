import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

DATA = "rework_90d_analysis.csv"

SEED = 42
BOOTSTRAPS = 10000

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


def make_features(frame, names):
    x = frame[names].copy()

    log_columns = [
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
    ]

    for column in log_columns:
        if column in x.columns:
            x[column] = np.log1p(
                x[column].astype(float)
            )

    return x


def model():
    return Pipeline(
        [
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "logistic",
                LogisticRegression(
                    max_iter=5000,
                    random_state=SEED,
                ),
            ),
        ]
    )


print("=" * 76)
print("IntentInsight Predictive Incremental-Value Robustness")
print("=" * 76)
print()

df = pd.read_csv(DATA)

df["merged_at"] = pd.to_datetime(
    df["merged_at"],
    utc=True,
)

df = df.sort_values(
    "merged_at"
).reset_index(drop=True)

split = int(len(df) * 0.70)

train = df.iloc[:split].copy()
test = df.iloc[split:].copy()

y_train = train["rework_90d"].astype(int).to_numpy()
y_test = test["rework_90d"].astype(int).to_numpy()

x_train_base = make_features(
    train,
    BASELINE_FEATURES,
)

x_test_base = make_features(
    test,
    BASELINE_FEATURES,
)

x_train_div = make_features(
    train,
    BASELINE_FEATURES + DIVERGENCE_FEATURES,
)

x_test_div = make_features(
    test,
    BASELINE_FEATURES + DIVERGENCE_FEATURES,
)

baseline_model = model()
divergence_model = model()

baseline_model.fit(
    x_train_base,
    y_train,
)

divergence_model.fit(
    x_train_div,
    y_train,
)

baseline_probability = baseline_model.predict_proba(
    x_test_base
)[:, 1]

divergence_probability = divergence_model.predict_proba(
    x_test_div
)[:, 1]

baseline_auc = roc_auc_score(
    y_test,
    baseline_probability,
)

divergence_auc = roc_auc_score(
    y_test,
    divergence_probability,
)

observed_delta = (
    divergence_auc
    - baseline_auc
)

print(
    f"Baseline ROC-AUC:   {baseline_auc:.6f}"
)

print(
    f"Divergence ROC-AUC: {divergence_auc:.6f}"
)

print(
    f"Observed Δ AUC:     {observed_delta:+.6f}"
)

# ----------------------------------------------------------------------
# Bootstrap confidence interval
# ----------------------------------------------------------------------

rng = np.random.default_rng(SEED)

bootstrap_deltas = []

n = len(y_test)

for _ in range(BOOTSTRAPS):

    indices = rng.integers(
        0,
        n,
        size=n,
    )

    y = y_test[indices]

    # Bootstrap sample must contain both classes.
    if len(np.unique(y)) < 2:
        continue

    auc_base = roc_auc_score(
        y,
        baseline_probability[indices],
    )

    auc_div = roc_auc_score(
        y,
        divergence_probability[indices],
    )

    bootstrap_deltas.append(
        auc_div - auc_base
    )

bootstrap_deltas = np.asarray(
    bootstrap_deltas
)

lower = np.percentile(
    bootstrap_deltas,
    2.5,
)

upper = np.percentile(
    bootstrap_deltas,
    97.5,
)

print()
print("=" * 76)
print("BOOTSTRAP 95% CI")
print("=" * 76)
print()

print(
    f"Bootstrap samples: {len(bootstrap_deltas)}"
)

print(
    f"Mean Δ AUC:        "
    f"{bootstrap_deltas.mean():+.6f}"
)

print(
    f"95% CI lower:      "
    f"{lower:+.6f}"
)

print(
    f"95% CI upper:      "
    f"{upper:+.6f}"
)

# ----------------------------------------------------------------------
# Paired permutation test
# ----------------------------------------------------------------------

# Under the null hypothesis that the two prediction systems
# are exchangeable for each observation, randomly swap their
# predictions within each test observation.

extreme = 0

permutation_deltas = []

for _ in range(BOOTSTRAPS):

    swap = rng.integers(
        0,
        2,
        size=n,
    ).astype(bool)

    p1 = baseline_probability.copy()
    p2 = divergence_probability.copy()

    temp = p1[swap].copy()

    p1[swap] = p2[swap]
    p2[swap] = temp

    auc1 = roc_auc_score(
        y_test,
        p1,
    )

    auc2 = roc_auc_score(
        y_test,
        p2,
    )

    delta = auc2 - auc1

    permutation_deltas.append(
        delta
    )

    if abs(delta) >= abs(observed_delta):
        extreme += 1

permutation_p = (
    extreme + 1
) / (
    BOOTSTRAPS + 1
)

print()
print("=" * 76)
print("PAIRED PERMUTATION TEST")
print("=" * 76)
print()

print(
    f"Iterations:       {BOOTSTRAPS}"
)

print(
    f"Extreme results:   {extreme}"
)

print(
    f"Empirical p-value: {permutation_p:.8f}"
)

# ----------------------------------------------------------------------
# Interpretation
# ----------------------------------------------------------------------

print()
print("=" * 76)
print("INTERPRETATION")
print("=" * 76)
print()

if lower <= 0 <= upper:
    print(
        "The 95% bootstrap CI includes zero."
    )
    print(
        "There is no clear evidence that divergence "
        "changes predictive discrimination."
    )
else:
    print(
        "The 95% bootstrap CI excludes zero."
    )

if permutation_p < 0.05:
    print(
        "The paired permutation test indicates "
        "a statistically detectable difference."
    )
else:
    print(
        "The paired permutation test does not "
        "indicate a statistically detectable difference."
    )

print()
print("No database records were modified.")
print("No GitHub requests were made.")
print("=" * 76)
