"""Statistical confounder analysis for structural-scope divergence.

READ-ONLY.

Input:
    structural_scope_analysis.csv

The analysis asks:

    Does non-Python scope remain associated with the change in
    divergence after accounting for PR size and structural scope?

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


def load_rows() -> list[dict[str, float]]:
    with INPUT.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)

        rows = []

        for raw in reader:
            rows.append(
                {
                    key: float(value)
                    for key, value in raw.items()
                    if key not in {
                        "repository_id",
                        "pull_request_number",
                    }
                }
            )

    return rows


def pearson(
    x: np.ndarray,
    y: np.ndarray,
) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    x = x - x.mean()
    y = y - y.mean()

    denominator = math.sqrt(
        float(np.sum(x * x))
        * float(np.sum(y * y))
    )

    if denominator == 0:
        return float("nan")

    return float(
        np.sum(x * y) / denominator
    )


def partial_correlation(
    target: np.ndarray,
    predictor: np.ndarray,
    controls: list[np.ndarray],
) -> float:
    """Correlation after removing linear effects of controls."""

    X = np.column_stack(
        [
            np.ones(len(target)),
            *controls,
        ]
    )

    beta_target, *_ = np.linalg.lstsq(
        X,
        target,
        rcond=None,
    )

    beta_predictor, *_ = np.linalg.lstsq(
        X,
        predictor,
        rcond=None,
    )

    residual_target = (
        target
        - X @ beta_target
    )

    residual_predictor = (
        predictor
        - X @ beta_predictor
    )

    return pearson(
        residual_target,
        residual_predictor,
    )


def regression(
    y: np.ndarray,
    predictors: dict[str, np.ndarray],
) -> dict[str, object]:
    """Ordinary least-squares regression."""

    names = list(predictors)

    X = np.column_stack(
        [
            np.ones(len(y)),
            *[
                predictors[name]
                for name in names
            ],
        ]
    )

    beta, residuals, rank, singular_values = (
        np.linalg.lstsq(
            X,
            y,
            rcond=None,
        )
    )

    fitted = X @ beta
    residual = y - fitted

    n = len(y)
    p = X.shape[1]

    sse = float(
        np.sum(residual ** 2)
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

    covariance = (
        mse
        * np.linalg.pinv(
            X.T @ X
        )
    )

    standard_errors = np.sqrt(
        np.maximum(
            np.diag(covariance),
            0.0,
        )
    )

    t_values = (
        beta
        / standard_errors
    )

    return {
        "names": names,
        "beta": beta,
        "standard_errors": standard_errors,
        "t_values": t_values,
        "r_squared": r_squared,
        "adjusted_r_squared": adjusted_r_squared,
        "residual": residual,
        "rank": rank,
        "singular_values": singular_values,
    }


def standardise(
    values: np.ndarray,
) -> np.ndarray:
    std = float(
        np.std(values)
    )

    if std == 0:
        return np.zeros_like(values)

    return (
        values - values.mean()
    ) / std


def describe_group(
    name: str,
    mask: np.ndarray,
    delta: np.ndarray,
) -> None:
    values = delta[mask]

    if len(values) == 0:
        return

    print()
    print(name)
    print("-" * 72)
    print(f"n:                 {len(values)}")
    print(f"mean delta:        {values.mean():.6f}")
    print(f"median delta:      {np.median(values):.6f}")
    print(
        f"mean |delta|:     "
        f"{np.mean(np.abs(values)):.6f}"
    )
    print(
        f"Python-only higher: "
        f"{np.sum(values > 0)}"
    )
    print(
        f"Full higher:        "
        f"{np.sum(values < 0)}"
    )
    print(
        f"Identical:          "
        f"{np.sum(np.isclose(values, 0.0))}"
    )


def main() -> None:
    print("=" * 72)
    print(
        "IntentInsight Structural Scope "
        "Confounder Analysis"
    )
    print("=" * 72)
    print()

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing {INPUT}"
        )

    rows = load_rows()

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
        ]
    )

    non_python_files = np.array(
        [
            row["non_python_files"]
            for row in rows
        ]
    )

    non_python_ratio = np.array(
        [
            row["non_python_ratio"]
            for row in rows
        ]
    )

    non_python_changes = np.array(
        [
            row["non_python_changes"]
            for row in rows
        ]
    )

    non_python_change_ratio = np.array(
        [
            row["non_python_change_ratio"]
            for row in rows
        ]
    )

    total_files = np.array(
        [
            row["total_files"]
            for row in rows
        ]
    )

    total_changes = np.array(
        [
            row["total_changes"]
            for row in rows
        ]
    )

    python_files = np.array(
        [
            row["python_files"]
            for row in rows
        ]
    )

    python_changes = np.array(
        [
            row["python_changes"]
            for row in rows
        ]
    )

    module_count = np.array(
        [
            row["module_count"]
            for row in rows
        ]
    )

    documentation_files = np.array(
        [
            row["documentation_files"]
            for row in rows
        ]
    )

    configuration_files = np.array(
        [
            row["configuration_files"]
            for row in rows
        ]
    )

    test_files = np.array(
        [
            row["test_files"]
            for row in rows
        ]
    )

    assets_files = np.array(
        [
            row["assets_files"]
            for row in rows
        ]
    )

    other_files = np.array(
        [
            row["other_files"]
            for row in rows
        ]
    )

    # ---------------------------------------------------------------
    # Basic groups
    # ---------------------------------------------------------------

    describe_group(
        "NO NON-PYTHON FILES",
        non_python_files == 0,
        delta,
    )

    describe_group(
        "HAS NON-PYTHON FILES",
        non_python_files > 0,
        delta,
    )

    # ---------------------------------------------------------------
    # Raw correlations
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "RAW CORRELATIONS WITH DIVERGENCE DELTA"
    )
    print("=" * 72)

    raw_predictors = {
        "non_python_files": non_python_files,
        "non_python_ratio": non_python_ratio,
        "non_python_changes": non_python_changes,
        "non_python_change_ratio": (
            non_python_change_ratio
        ),
        "total_files": total_files,
        "total_changes": total_changes,
        "python_files": python_files,
        "python_changes": python_changes,
        "module_count": module_count,
    }

    for name, values in raw_predictors.items():
        print(
            f"{name:28s} "
            f"r = {pearson(delta, values):+.6f}"
        )

    # ---------------------------------------------------------------
    # Partial correlations
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "PARTIAL CORRELATIONS"
    )
    print("=" * 72)

    print()
    print(
        "Target: divergence delta"
    )
    print(
        "Controls: total PR size + Python structural scope"
    )

    controls = [
        np.log1p(total_changes),
        np.log1p(total_files),
        np.log1p(python_files),
        np.log1p(module_count),
    ]

    partial_predictors = {
        "non_python_files": non_python_files,
        "non_python_ratio": non_python_ratio,
        "non_python_changes": non_python_changes,
        "non_python_change_ratio": (
            non_python_change_ratio
        ),
    }

    for name, values in partial_predictors.items():
        value = partial_correlation(
            delta,
            values,
            controls,
        )

        print(
            f"{name:28s} "
            f"partial r = {value:+.6f}"
        )

    # ---------------------------------------------------------------
    # Regression model
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "MULTIVARIABLE REGRESSION"
    )
    print("=" * 72)

    print()
    print(
        "Dependent variable:"
    )
    print(
        "    delta = Python-only divergence "
        "- full divergence"
    )

    print()
    print(
        "Predictors:"
    )
    print(
        "    non-Python change ratio"
    )
    print(
        "    log(total changes)"
    )
    print(
        "    log(total files)"
    )
    print(
        "    log(Python files)"
    )
    print(
        "    log(module count)"
    )

    predictors = {
        "non_python_change_ratio": (
            non_python_change_ratio
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
    }

    model = regression(
        delta,
        predictors,
    )

    print()
    print(
        f"R²:             "
        f"{model['r_squared']:.6f}"
    )

    print(
        f"Adjusted R²:    "
        f"{model['adjusted_r_squared']:.6f}"
    )

    print()

    names = model["names"]
    beta = model["beta"]
    se = model["standard_errors"]
    t = model["t_values"]

    print(
        f"{'Predictor':32s}"
        f"{'Coefficient':>14s}"
        f"{'Std.Error':>14s}"
        f"{'t':>12s}"
    )

    print("-" * 72)

    print(
        f"{'Intercept':32s}"
        f"{beta[0]:14.6f}"
        f"{se[0]:14.6f}"
        f"{t[0]:12.4f}"
    )

    for index, name in enumerate(
        names,
        start=1,
    ):
        print(
            f"{name:32s}"
            f"{beta[index]:14.6f}"
            f"{se[index]:14.6f}"
            f"{t[index]:12.4f}"
        )

    # ---------------------------------------------------------------
    # Standardised regression
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "STANDARDISED REGRESSION"
    )
    print("=" * 72)

    standardized_predictors = {
        name: standardise(values)
        for name, values in predictors.items()
    }

    standardized_model = regression(
        standardise(delta),
        standardized_predictors,
    )

    beta = standardized_model["beta"]

    print()
    print(
        f"{'Predictor':32s}"
        f"{'Standardised beta':>20s}"
    )

    print("-" * 72)

    for index, name in enumerate(
        standardized_model["names"],
        start=1,
    ):
        print(
            f"{name:32s}"
            f"{beta[index]:20.6f}"
        )

    # ---------------------------------------------------------------
    # Category effects
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "CATEGORY EFFECTS"
    )
    print("=" * 72)

    categories = {
        "documentation": documentation_files,
        "configuration/build": (
            configuration_files
        ),
        "tests": test_files,
        "assets/frontend": assets_files,
        "other": other_files,
    }

    for name, counts in categories.items():

        present = counts > 0
        absent = counts == 0

        if not np.any(present):
            continue

        print()
        print(name)
        print(
            f"Present: n={np.sum(present)}, "
            f"mean delta={delta[present].mean():+.6f}"
        )
        print(
            f"Absent:  n={np.sum(absent)}, "
            f"mean delta={delta[absent].mean():+.6f}"
        )
        print(
            f"Difference: "
            f"{delta[present].mean() - delta[absent].mean():+.6f}"
        )

    # ---------------------------------------------------------------
    # Sensitivity: remove extreme deltas
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "SENSITIVITY TO EXTREME DELTAS"
    )
    print("=" * 72)

    thresholds = [
        0.40,
        0.30,
        0.25,
        0.20,
        0.15,
        0.10,
    ]

    for threshold in thresholds:

        mask = (
            np.abs(delta)
            <= threshold
        )

        if np.sum(mask) < 20:
            continue

        r = pearson(
            delta[mask],
            non_python_change_ratio[mask],
        )

        print(
            f"|delta| <= {threshold:.2f}: "
            f"n={np.sum(mask):3d}, "
            f"mean delta={delta[mask].mean():+.6f}, "
            f"r={r:+.6f}"
        )

    # ---------------------------------------------------------------
    # Direction
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "DIRECTION"
    )
    print("=" * 72)

    print(
        f"Python-only higher: "
        f"{np.sum(delta > 0)}"
    )

    print(
        f"Full higher:        "
        f"{np.sum(delta < 0)}"
    )

    print(
        f"Identical:          "
        f"{np.sum(np.isclose(delta, 0.0))}"
    )

    print()
    print("=" * 72)
    print(
        "ANALYSIS COMPLETE"
    )
    print("=" * 72)
    print()
    print(
        "No database records were modified."
    )


if __name__ == "__main__":
    main()