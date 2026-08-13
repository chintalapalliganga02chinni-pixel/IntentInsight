import pandas as pd
import numpy as np

from scipy.stats import (
    mannwhitneyu,
    spearmanr,
    pearsonr,
)

DATA = "rework_90d_analysis.csv"

df = pd.read_csv(DATA)

print("=" * 76)
print("IntentInsight Rework / Divergence Diagnostic")
print("=" * 76)

print()
print(f"Rows: {len(df)}")

# ----------------------------------------------------------------------
# 1. Basic outcome distributions
# ----------------------------------------------------------------------

print()
print("=" * 76)
print("OUTCOME")
print("=" * 76)

print(
    df["rework_90d"]
    .value_counts()
    .sort_index()
)

# ----------------------------------------------------------------------
# 2. Divergence by outcome
# ----------------------------------------------------------------------

yes = df.loc[
    df["rework_90d"] == 1,
    "intent_impact_divergence"
]

no = df.loc[
    df["rework_90d"] == 0,
    "intent_impact_divergence"
]

print()
print("=" * 76)
print("DIVERGENCE BY REWORK OUTCOME")
print("=" * 76)

print(
    f"Rework = 1: n={len(yes)}, "
    f"mean={yes.mean():.6f}, "
    f"median={yes.median():.6f}"
)

print(
    f"Rework = 0: n={len(no)}, "
    f"mean={no.mean():.6f}, "
    f"median={no.median():.6f}"
)

print(
    f"Mean difference: "
    f"{yes.mean() - no.mean():+.6f}"
)

u, p = mannwhitneyu(
    yes,
    no,
    alternative="two-sided",
)

print(
    f"Mann-Whitney U: {u:.6f}"
)

print(
    f"Mann-Whitney p: {p:.8g}"
)

# ----------------------------------------------------------------------
# 3. Divergence relationship with rework intensity
# ----------------------------------------------------------------------

print()
print("=" * 76)
print("DIVERGENCE VS REWORK INTENSITY")
print("=" * 76)

for column in [
    "rework_pr_count_90d",
    "reworked_module_count_90d",
]:

    rho, p = spearmanr(
        df["intent_impact_divergence"],
        df[column],
    )

    print()
    print(column)
    print(f"Spearman rho: {rho:+.6f}")
    print(f"p-value:      {p:.8g}")

# ----------------------------------------------------------------------
# 4. Divergence vs time to rework
# ----------------------------------------------------------------------

reworked = df[
    df["days_to_first_rework"].notna()
].copy()

if len(reworked) > 2:

    rho, p = spearmanr(
        reworked["intent_impact_divergence"],
        reworked["days_to_first_rework"],
    )

    print()
    print("=" * 76)
    print("DIVERGENCE VS TIME TO FIRST REWORK")
    print("=" * 76)
    print()
    print(
        f"n:            {len(reworked)}"
    )
    print(
        f"Spearman rho: {rho:+.6f}"
    )
    print(
        f"p-value:      {p:.8g}"
    )

# ----------------------------------------------------------------------
# 5. Correlation / redundancy
# ----------------------------------------------------------------------

print()
print("=" * 76)
print("INTENT / DIVERGENCE RELATIONSHIP")
print("=" * 76)

pearson_r, pearson_p = pearsonr(
    df["intent_similarity"],
    df["intent_impact_divergence"],
)

spearman_r, spearman_p = spearmanr(
    df["intent_similarity"],
    df["intent_impact_divergence"],
)

print(
    f"Pearson r:  {pearson_r:+.8f}"
)

print(
    f"Pearson p:  {pearson_p:.8g}"
)

print(
    f"Spearman:   {spearman_r:+.8f}"
)

print(
    f"Spearman p: {spearman_p:.8g}"
)

# ----------------------------------------------------------------------
# 6. Divergence correlations with conventional structure
# ----------------------------------------------------------------------

print()
print("=" * 76)
print("DIVERGENCE VS STRUCTURAL FEATURES")
print("=" * 76)

features = [
    "total_changes",
    "changed_file_count",
    "module_count",
    "package_count",
    "module_entropy",
    "module_concentration",
    "top_module_weight",
]

for feature in features:

    rho, p = spearmanr(
        df["intent_impact_divergence"],
        df[feature],
    )

    print(
        f"{feature:28} "
        f"rho={rho:+.6f} "
        f"p={p:.6g}"
    )

# ----------------------------------------------------------------------
# 7. Quartile analysis
# ----------------------------------------------------------------------

print()
print("=" * 76)
print("REWORK RATE BY DIVERGENCE QUARTILE")
print("=" * 76)

df["divergence_quartile"] = pd.qcut(
    df["intent_impact_divergence"],
    q=4,
    labels=False,
    duplicates="drop",
)

quartiles = (
    df.groupby("divergence_quartile")
    .agg(
        n=("rework_90d", "size"),
        mean_divergence=(
            "intent_impact_divergence",
            "mean",
        ),
        rework_rate=(
            "rework_90d",
            "mean",
        ),
        mean_rework_count=(
            "rework_pr_count_90d",
            "mean",
        ),
    )
)

print(
    quartiles.to_string(
        float_format=lambda x:
            f"{x:.6f}"
    )
)

print()
print("=" * 76)
print("DIAGNOSTIC COMPLETE")
print("=" * 76)
print()
print("No database records were modified.")
print("No GitHub requests were made.")
