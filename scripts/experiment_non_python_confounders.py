"""
IntentInsight Non-Python Confounder Analysis

Read-only experiment.

Tests whether the change in divergence between:
    - current full-file representation
    - Python-only representation

is associated with non-Python scope after accounting for PR size
and structural scope.

No database records are modified.
"""

from __future__ import annotations

import math
import sqlite3
from statistics import mean, median

import numpy as np


DB_PATH = "intentinsight.db"


def pearson(x: list[float], y: list[float]) -> float:
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    if len(x_arr) < 2:
        return float("nan")

    x_centered = x_arr - x_arr.mean()
    y_centered = y_arr - y_arr.mean()

    denominator = math.sqrt(
        float(np.sum(x_centered**2))
        * float(np.sum(y_centered**2))
    )

    if denominator == 0:
        return float("nan")

    return float(
        np.sum(x_centered * y_centered) / denominator
    )


def partial_correlation(
    x: list[float],
    y: list[float],
    controls: list[list[float]],
) -> float:
    """
    Correlation between x and y after linearly removing controls.
    """

    X = np.column_stack(
        [
            np.ones(len(x)),
            *controls,
        ]
    )

    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    beta_x, *_ = np.linalg.lstsq(X, x_arr, rcond=None)
    beta_y, *_ = np.linalg.lstsq(X, y_arr, rcond=None)

    residual_x = x_arr - X @ beta_x
    residual_y = y_arr - X @ beta_y

    return pearson(
        residual_x.tolist(),
        residual_y.tolist(),
    )


def standardise(values: list[float]) -> list[float]:
    arr = np.asarray(values, dtype=float)

    std = float(arr.std())

    if std == 0:
        return [0.0] * len(values)

    return (
        ((arr - float(arr.mean())) / std)
        .astype(float)
        .tolist()
    )


def print_stat(label: str, values: list[float]) -> None:
    print(f"{label}")
    print(f"Min:    {min(values):.6f}")
    print(f"Median: {median(values):.6f}")
    print(f"Mean:   {mean(values):.6f}")
    print(f"Max:    {max(values):.6f}")
    print()


def main() -> None:
    print("=" * 72)
    print("IntentInsight Non-Python Confounder Analysis")
    print("=" * 72)
    print()
    print("READ-ONLY EXPERIMENT")
    print("No database records will be modified.")
    print()

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            d.repository_id,
            d.pull_request_number,
            d.intent_similarity,
            d.intent_impact_divergence,

            d.module_count,
            d.changed_file_count,
            d.total_additions,
            d.total_deletions,
            d.total_changes,

            rr.source_file_count,
            rr.test_file_count,
            rr.documentation_file_count,
            rr.configuration_file_count,
            rr.other_file_count,

            rr.total_files,
            rr.additions AS pr_additions,
            rr.deletions AS pr_deletions

        FROM intent_impact_divergence AS d

        JOIN research_records AS rr
          ON rr.repository_id = d.repository_id
         AND rr.pull_request_number = d.pull_request_number

        WHERE rr.eligible = 1

        ORDER BY
            d.repository_id,
            d.pull_request_number
        """
    ).fetchall()

    print(f"PRs analysed: {len(rows)}")
    print()

    # ------------------------------------------------------------------
    # Reconstruct non-Python scope.
    # ------------------------------------------------------------------

    observations: list[dict[str, float]] = []

    for row in rows:
        total_files = int(row["total_files"] or 0)
        source_files = int(row["source_file_count"] or 0)

        non_python_files = max(
            total_files - source_files,
            0,
        )

        total_changes = int(row["total_changes"] or 0)

        non_python_changes = max(
            int(row["pr_additions"] or 0)
            + int(row["pr_deletions"] or 0)
            - (
                int(row["total_additions"] or 0)
                + int(row["total_deletions"] or 0)
            ),
            0,
        )

        if total_files > 0:
            non_python_ratio = (
                non_python_files / total_files
            )
        else:
            non_python_ratio = 0.0

        if (
            int(row["pr_additions"] or 0)
            + int(row["pr_deletions"] or 0)
        ) > 0:
            non_python_change_ratio = (
                non_python_changes
                / (
                    int(row["pr_additions"] or 0)
                    + int(row["pr_deletions"] or 0)
                )
            )
        else:
            non_python_change_ratio = 0.0

        observations.append(
            {
                "delta": 0.0,
                "non_python_files": float(non_python_files),
                "non_python_ratio": non_python_ratio,
                "non_python_changes": float(
                    non_python_changes
                ),
                "non_python_change_ratio": (
                    non_python_change_ratio
                ),
                "total_files": float(total_files),
                "total_changes": float(total_changes),
                "module_count": float(
                    row["module_count"] or 0
                ),
                "python_files": float(source_files),
            }
        )

    # ------------------------------------------------------------------
    # IMPORTANT:
    #
    # We need the Python-only divergence from the existing experiment.
    # It is reconstructed from the existing structural embedding after
    # excluding non-Python modules.
    #
    # Rather than silently inventing it here, require the experiment
    # output table to exist.
    # ------------------------------------------------------------------

    print(
        "This analysis requires the per-PR Python-only divergence "
        "values from the previous experiment."
    )
    print()
    print(
        "Before running this script, we need to expose those values "
        "in a read-only CSV."
    )
    print()
    print(
        "NEXT COMMAND:"
    )
    print(
        r"python scripts\experiment_historical_divergence.py"
    )
    print()
    print(
        "Do NOT modify the database."
    )

    connection.close()


if __name__ == "__main__":
    main()