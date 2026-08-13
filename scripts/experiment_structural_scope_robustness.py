"""
IntentInsight Structural Scope Robustness Analysis

Read-only statistical validation of the relationship between
non-Python scope and the divergence difference.

delta = Python-only divergence - current full-file divergence

Analyses:
1. Multiple regression specifications
2. Variance Inflation Factors (VIF)
3. Bootstrap confidence intervals
4. Permutation test
5. Sensitivity to extreme observations
6. Simple group comparison

No database access.
No GitHub requests.
No database modifications.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np


INPUT = Path("structural_scope_analysis.csv")

RANDOM_SEED = 20260811
BOOTSTRAP_ITERATIONS = 5000
PERMUTATION_ITERATIONS = 10000


def load_dataset() -> list[dict[str, float]]:
    with INPUT.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)

        rows: list[dict[str, float]] = []

        for raw in reader:
            row: dict[str, float] = {}

            for key, value in raw.items():
                if key in {
                    "repository_id",
                    "pull_request_number",
                }:
                    continue

                row[key] = float(value)

            rows.append(row)

    return rows


def pearson(
    x: np.ndarray,
    y: np.ndarray,
) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    x_centered = x - x.mean()
    y_centered = y - y.mean()

    denominator = math.sqrt(
        float(np.sum(x_centered ** 2))
        * float(np.sum(y_centered ** 2))
    )

    if denominator == 0:
        return float("nan")

    return float(
        np.sum(x_centered * y_centered)
        / denominator
    )


def standardise(
    values: np.ndarray,
) -> np.ndarray:
    mean_value = float(values.mean())
    std_value = float(values.std())

    if std_value == 0:
        return np.zeros_like(values)

    return (
        values - mean_value
    ) / std_value


def design_matrix(
    predictors: dict[str, np.ndarray],
) -> tuple[np.ndarray, list[str]]:
    names = list(predictors)

    X = np.column_stack(
        [
            np.ones(len(next(iter(predictors.values())))),
            *[
                predictors[name]
                for name in names
            ],
        ]
    )

    return X, names


def regression(
    y: np.ndarray,
    predictors: dict[str, np.ndarray],
) -> dict[str, object]:
    X, names = design_matrix(predictors)

    beta, *_ = np.linalg.lstsq(
        X,
        y,
        rcond=None,
    )

    fitted = X @ beta
    residuals = y - fitted

    n = len(y)
    p = X.shape[1]

    sse = float(
        np.sum(residuals ** 2)
    )

    sst = float(
        np.sum(
            (y - y.mean()) ** 2
        )
    )

    r_squared = (
        1.0 - sse / sst
        if sst > 0
        else float("nan")
    )

    adjusted_r_squared = (
        1.0
        - (
            (1.0 - r_squared)
            * (n - 1)
            / (n - p)
        )
        if n > p
        else float("nan")
    )

    degrees_of_freedom = n - p

    mse = (
        sse / degrees_of_freedom
        if degrees_of_freedom > 0
        else float("nan")
    )

    xtx_inverse = np.linalg.pinv(
        X.T @ X
    )

    covariance = (
        mse
        * xtx_inverse
    )

    standard_errors = np.sqrt(
        np.maximum(
            np.diag(covariance),
            0.0,
        )
    )

    t_values = np.divide(
        beta,
        standard_errors,
        out=np.full_like(
            beta,
            np.nan,
        ),
        where=standard_errors != 0,
    )

    return {
        "names": names,
        "beta": beta,
        "standard_errors": standard_errors,
        "t_values": t_values,
        "r_squared": r_squared,
        "adjusted_r_squared": (
            adjusted_r_squared
        ),
        "residuals": residuals,
    }


def t_distribution_two_sided_p(
    t_value: float,
    degrees_of_freedom: int,
) -> float:
    """
    Two-sided t-test p-value.

    Uses scipy if available. Falls back to NaN rather than
    silently approximating significance.
    """

    try:
        from scipy.stats import t

        return float(
            2.0
            * t.sf(
                abs(t_value),
                degrees_of_freedom,
            )
        )

    except ImportError:
        return float("nan")


def vif(
    predictors: dict[str, np.ndarray],
) -> dict[str, float]:
    """
    Calculate variance inflation factors.

    VIF = 1 / (1 - R²)
    from regressing each predictor on all others.
    """

    names = list(predictors)

    result: dict[str, float] = {}

    for target_name in names:

        target = predictors[target_name]

        controls = {
            name: predictors[name]
            for name in names
            if name != target_name
        }

        if not controls:
            result[target_name] = 1.0
            continue

        model = regression(
            target,
            controls,
        )

        r_squared = float(
            model["r_squared"]
        )

        if r_squared >= 0.999999:
            result[target_name] = float("inf")
        else:
            result[target_name] = (
                1.0
                / (1.0 - r_squared)
            )

    return result


def bootstrap_mean(
    values: np.ndarray,
    iterations: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    estimates = np.empty(iterations)

    n = len(values)

    for i in range(iterations):
        sample = rng.choice(
            values,
            size=n,
            replace=True,
        )

        estimates[i] = float(
            np.mean(sample)
        )

    return (
        float(np.mean(values)),
        float(np.percentile(estimates, 2.5)),
        float(np.percentile(estimates, 97.5)),
    )


def bootstrap_regression_coefficient(
    y: np.ndarray,
    predictor: np.ndarray,
    controls: dict[str, np.ndarray],
    iterations: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    n = len(y)

    predictors = {
        "non_python_change_ratio": predictor,
        **controls,
    }

    observed = regression(
        y,
        predictors,
    )

    observed_beta = float(
        observed["beta"][1]
    )

    estimates = np.empty(iterations)

    for i in range(iterations):

        indices = rng.integers(
            0,
            n,
            size=n,
        )

        sample_y = y[indices]

        sample_predictors = {
            name: values[indices]
            for name, values in predictors.items()
        }

        model = regression(
            sample_y,
            sample_predictors,
        )

        estimates[i] = float(
            model["beta"][1]
        )

    return (
        observed_beta,
        float(
            np.percentile(
                estimates,
                2.5,
            )
        ),
        float(
            np.percentile(
                estimates,
                97.5,
            )
        ),
    )


def permutation_test(
    delta: np.ndarray,
    predictor: np.ndarray,
    iterations: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    """
    Permutation test for the Pearson correlation.

    Null hypothesis:
        There is no association between predictor and delta.
    """

    observed = pearson(
        delta,
        predictor,
    )

    absolute_observed = abs(observed)

    count = 0

    for _ in range(iterations):

        shuffled = rng.permutation(
            predictor
        )

        statistic = abs(
            pearson(
                delta,
                shuffled,
            )
        )

        if statistic >= absolute_observed:
            count += 1

    p_value = (
        (count + 1)
        / (iterations + 1)
    )

    return (
        observed,
        p_value,
        count,
    )


def print_regression(
    name: str,
    model: dict[str, object],
    n: int,
) -> None:

    names = model["names"]
    beta = model["beta"]
    se = model["standard_errors"]
    t_values = model["t_values"]

    print()
    print(name)
    print("-" * 72)

    print(
        f"R²:          "
        f"{model['r_squared']:.6f}"
    )

    print(
        f"Adjusted R²: "
        f"{model['adjusted_r_squared']:.6f}"
    )

    print()

    print(
        f"{'Predictor':32s}"
        f"{'Beta':>12s}"
        f"{'SE':>12s}"
        f"{'t':>12s}"
        f"{'p':>12s}"
    )

    print("-" * 80)

    degrees_of_freedom = (
        n
        - len(names)
        - 1
    )

    print(
        f"{'Intercept':32s}"
        f"{beta[0]:12.6f}"
        f"{se[0]:12.6f}"
        f"{t_values[0]:12.4f}"
        f"{'':>12s}"
    )

    for index, predictor in enumerate(
        names,
        start=1,
    ):
        p_value = (
            t_distribution_two_sided_p(
                float(t_values[index]),
                degrees_of_freedom,
            )
        )

        print(
            f"{predictor:32s}"
            f"{beta[index]:12.6f}"
            f"{se[index]:12.6f}"
            f"{t_values[index]:12.4f}"
            f"{p_value:12.6g}"
        )


def main() -> None:
    print("=" * 72)
    print(
        "IntentInsight Structural Scope "
        "Robustness Analysis"
    )
    print("=" * 72)
    print()
    print("READ-ONLY")
    print("No database access.")
    print("No GitHub requests.")
    print("No database modifications.")
    print()

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing {INPUT}"
        )

    rows = load_dataset()

    print(
        f"Rows loaded: {len(rows)}"
    )

    if len(rows) != 703:
        raise RuntimeError(
            f"Expected 703 rows, "
            f"found {len(rows)}."
        )

    delta = np.array(
        [
            row["delta"]
            for row in rows
        ],
        dtype=float,
    )

    non_python_ratio = np.array(
        [
            row["non_python_change_ratio"]
            for row in rows
        ],
        dtype=float,
    )

    total_changes = np.array(
        [
            row["total_changes"]
            for row in rows
        ],
        dtype=float,
    )

    total_files = np.array(
        [
            row["total_files"]
            for row in rows
        ],
        dtype=float,
    )

    python_files = np.array(
        [
            row["python_files"]
            for row in rows
        ],
        dtype=float,
    )

    module_count = np.array(
        [
            row["module_count"]
            for row in rows
        ],
        dtype=float,
    )

    # ================================================================
    # BASIC ASSOCIATION
    # ================================================================

    print()
    print("=" * 72)
    print("BASIC ASSOCIATION")
    print("=" * 72)

    observed_r = pearson(
        delta,
        non_python_ratio,
    )

    print(
        f"Pearson r: "
        f"{observed_r:+.6f}"
    )

    print(
        f"Mean delta: "
        f"{delta.mean():+.6f}"
    )

    print(
        f"Median delta: "
        f"{np.median(delta):+.6f}"
    )

    # ================================================================
    # MODEL SPECIFICATIONS
    # ================================================================

    print()
    print("=" * 72)
    print("REGRESSION SPECIFICATIONS")
    print("=" * 72)

    models = [
        (
            "MODEL A: non-Python scope only",
            {
                "non_python_change_ratio": (
                    non_python_ratio
                )
            },
        ),
        (
            "MODEL B: + total changes",
            {
                "non_python_change_ratio": (
                    non_python_ratio
                ),
                "log_total_changes": np.log1p(
                    total_changes
                ),
            },
        ),
        (
            "MODEL C: + total files",
            {
                "non_python_change_ratio": (
                    non_python_ratio
                ),
                "log_total_files": np.log1p(
                    total_files
                ),
            },
        ),
        (
            "MODEL D: + Python scope",
            {
                "non_python_change_ratio": (
                    non_python_ratio
                ),
                "log_total_changes": np.log1p(
                    total_changes
                ),
                "log_python_files": np.log1p(
                    python_files
                ),
            },
        ),
        (
            "MODEL E: full structural controls",
            {
                "non_python_change_ratio": (
                    non_python_ratio
                ),
                "log_total_changes": np.log1p(
                    total_changes
                ),
                "log_total_files": np.log1p(
                    total_files
                ),
                "log_python_files": np.log1p(
                    python_files
                ),
                "log_module_count": np.log1p(
                    module_count
                ),
            },
        ),
    ]

    fitted_models = []

    for name, predictors in models:

        model = regression(
            delta,
            predictors,
        )

        fitted_models.append(
            (
                name,
                predictors,
                model,
            )
        )

        print_regression(
            name,
            model,
            len(delta),
        )

    # ================================================================
    # VIF
    # ================================================================

    print()
    print("=" * 72)
    print("MULTICOLLINEARITY — VIF")
    print("=" * 72)

    full_predictors = fitted_models[-1][1]

    vifs = vif(
        full_predictors
    )

    for name, value in vifs.items():

        print(
            f"{name:32s}"
            f"VIF = {value:.6f}"
        )

    print()
    print(
        "Reference guide:"
    )
    print(
        "VIF < 5   generally acceptable"
    )
    print(
        "VIF 5–10  potentially problematic"
    )
    print(
        "VIF > 10  substantial multicollinearity"
    )

    # ================================================================
    # STANDARDISED EFFECT
    # ================================================================

    print()
    print("=" * 72)
    print("STANDARDISED EFFECTS — MODEL D")
    print("=" * 72)

    model_d_predictors = fitted_models[3][1]

    standardised_predictors = {
        name: standardise(values)
        for name, values
        in model_d_predictors.items()
    }

    standardised_model = regression(
        standardise(delta),
        standardised_predictors,
    )

    for index, name in enumerate(
        standardised_model["names"],
        start=1,
    ):
        print(
            f"{name:32s}"
            f"beta = "
            f"{standardised_model['beta'][index]:+.6f}"
        )

    # ================================================================
    # BOOTSTRAP MEAN
    # ================================================================

    print()
    print("=" * 72)
    print("BOOTSTRAP 95% CI — MEAN DELTA")
    print("=" * 72)

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    mean_value, mean_lower, mean_upper = (
        bootstrap_mean(
            delta,
            BOOTSTRAP_ITERATIONS,
            rng,
        )
    )

    print(
        f"Observed mean: "
        f"{mean_value:+.6f}"
    )

    print(
        f"95% CI lower: "
        f"{mean_lower:+.6f}"
    )

    print(
        f"95% CI upper: "
        f"{mean_upper:+.6f}"
    )

    # ================================================================
    # BOOTSTRAP NON-PYTHON COEFFICIENT
    # ================================================================

    print()
    print("=" * 72)
    print(
        "BOOTSTRAP 95% CI — "
        "NON-PYTHON EFFECT"
    )
    print("=" * 72)

    bootstrap_controls = {
        "log_total_changes": np.log1p(
            total_changes
        ),
        "log_python_files": np.log1p(
            python_files
        ),
    }

    (
        observed_beta,
        beta_lower,
        beta_upper,
    ) = bootstrap_regression_coefficient(
        delta,
        non_python_ratio,
        bootstrap_controls,
        BOOTSTRAP_ITERATIONS,
        rng,
    )

    print(
        f"Observed coefficient: "
        f"{observed_beta:+.6f}"
    )

    print(
        f"95% CI lower: "
        f"{beta_lower:+.6f}"
    )

    print(
        f"95% CI upper: "
        f"{beta_upper:+.6f}"
    )

    # ================================================================
    # PERMUTATION TEST
    # ================================================================

    print()
    print("=" * 72)
    print(
        "PERMUTATION TEST — "
        "NON-PYTHON ASSOCIATION"
    )
    print("=" * 72)

    (
        permutation_r,
        permutation_p,
        extreme_count,
    ) = permutation_test(
        delta,
        non_python_ratio,
        PERMUTATION_ITERATIONS,
        rng,
    )

    print(
        f"Observed r: "
        f"{permutation_r:+.6f}"
    )

    print(
        f"Permutation iterations: "
        f"{PERMUTATION_ITERATIONS}"
    )

    print(
        f"Extreme permutations: "
        f"{int(extreme_count)}"
    )

    print(
        f"Two-sided empirical p: "
        f"{permutation_p:.8f}"
    )

    # ================================================================
    # SENSITIVITY TO EXTREMES
    # ================================================================

    print()
    print("=" * 72)
    print("SENSITIVITY TO EXTREME DELTAS")
    print("=" * 72)

    for threshold in [
        0.40,
        0.30,
        0.25,
        0.20,
        0.15,
        0.10,
    ]:

        mask = (
            np.abs(delta)
            <= threshold
        )

        if np.sum(mask) < 30:
            continue

        r = pearson(
            delta[mask],
            non_python_ratio[mask],
        )

        print(
            f"|delta| <= {threshold:.2f}: "
            f"n={np.sum(mask):3d}, "
            f"mean={delta[mask].mean():+.6f}, "
            f"r={r:+.6f}"
        )

    # ================================================================
    # ZERO-SCOPE CHECK
    # ================================================================

    print()
    print("=" * 72)
    print("ZERO NON-PYTHON SCOPE CHECK")
    print("=" * 72)

    zero_scope = (
        non_python_ratio == 0
    )

    nonzero_scope = (
        non_python_ratio > 0
    )

    print(
        f"No non-Python scope: "
        f"n={np.sum(zero_scope)}, "
        f"mean delta="
        f"{delta[zero_scope].mean():+.6f}"
    )

    print(
        f"Non-Python scope present: "
        f"n={np.sum(nonzero_scope)}, "
        f"mean delta="
        f"{delta[nonzero_scope].mean():+.6f}"
    )

    print()
    print("=" * 72)
    print("ROBUSTNESS ANALYSIS COMPLETE")
    print("=" * 72)
    print()
    print(
        "No database records were modified."
    )
    print(
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()