"""Audit the empirical distribution of intent-impact divergence."""

from __future__ import annotations

import sqlite3
import statistics


DATABASE = "intentinsight.db"


def percentile(values: list[float], percentage: float) -> float:
    """Calculate a simple linear-interpolated percentile."""

    if not values:
        raise ValueError("Cannot calculate percentile of empty data.")

    ordered = sorted(values)

    position = (len(ordered) - 1) * percentage
    lower = int(position)
    upper = min(lower + 1, len(ordered))

    fraction = position - lower

    return (
        ordered[lower]
        + (ordered[upper] - ordered[lower]) * fraction
    )


def correlation(
    left: list[float],
    right: list[float],
) -> float:
    """Calculate Pearson correlation."""

    if len(left) != len(right):
        raise ValueError("Vectors must have equal lengths.")

    left_mean = statistics.mean(left)
    right_mean = statistics.mean(right)

    numerator = sum(
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left, right)
    )

    left_variance = sum(
        (x - left_mean) ** 2
        for x in left
    )

    right_variance = sum(
        (y - right_mean) ** 2
        for y in right
    )

    denominator = (
        left_variance * right_variance
    ) ** 0.5

    if denominator == 0:
        return 0.0

    return numerator / denominator


def describe(
    name: str,
    values: list[float],
) -> None:
    """Print descriptive statistics."""

    print(name)
    print("-" * len(name))

    print(f"Count:       {len(values)}")
    print(f"Min:         {min(values):.6f}")
    print(f"Q1:          {percentile(values, 0.25):.6f}")
    print(f"Median:      {percentile(values, 0.50):.6f}")
    print(f"Mean:        {statistics.mean(values):.6f}")
    print(f"Q3:          {percentile(values, 0.75):.6f}")
    print(f"Max:         {max(values):.6f}")

    if len(values) > 1:
        print(
            f"Std dev:     {statistics.stdev(values):.6f}"
        )

    print()


def main() -> None:
    """Audit divergence and structural relationships."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT
                intent_similarity,
                intent_impact_divergence,

                module_count,
                changed_file_count,
                module_entropy,
                module_concentration,
                top_module_weight,
                package_count,
                cross_package_spread,

                total_additions,
                total_deletions,
                total_changes
            FROM intent_impact_divergence
            ORDER BY id
            """
        ).fetchall()

        if not rows:
            raise RuntimeError(
                "No divergence records found."
            )

        divergence = [
            float(row["intent_impact_divergence"])
            for row in rows
        ]

        similarity = [
            float(row["intent_similarity"])
            for row in rows
        ]

        changed_files = [
            float(row["changed_file_count"])
            for row in rows
        ]

        module_count = [
            float(row["module_count"])
            for row in rows
        ]

        module_entropy = [
            float(row["module_entropy"])
            for row in rows
        ]

        package_count = [
            float(row["package_count"])
            for row in rows
        ]

        total_changes = [
            float(row["total_changes"])
            for row in rows
        ]

        print()
        print("=" * 64)
        print("INTENTINSIGHT DIVERGENCE EMPIRICAL AUDIT")
        print("=" * 64)
        print()

        print(
            f"Records analysed: {len(rows)}"
        )
        print()

        describe(
            "INTENT–IMPACT DIVERGENCE",
            divergence,
        )

        describe(
            "INTENT SIMILARITY",
            similarity,
        )

        describe(
            "MODULE COUNT",
            module_count,
        )

        describe(
            "CHANGED FILE COUNT",
            changed_files,
        )

        describe(
            "MODULE ENTROPY",
            module_entropy,
        )

        describe(
            "PACKAGE COUNT",
            package_count,
        )

        describe(
            "TOTAL CHANGES",
            total_changes,
        )

        print("CORRELATION WITH DIVERGENCE")
        print("---------------------------")

        print(
            "Changed files:   "
            f"{correlation(divergence, changed_files):.4f}"
        )

        print(
            "Module count:    "
            f"{correlation(divergence, module_count):.4f}"
        )

        print(
            "Module entropy:  "
            f"{correlation(divergence, module_entropy):.4f}"
        )

        print(
            "Package count:   "
            f"{correlation(divergence, package_count):.4f}"
        )

        print(
            "Total changes:   "
            f"{correlation(divergence, total_changes):.4f}"
        )

        print()

        print("DIVERGENCE BANDS")
        print("---------------")

        bands = [
            ("Very low", 0.00, 0.20),
            ("Low", 0.20, 0.40),
            ("Moderate", 0.40, 0.60),
            ("High", 0.60, 0.80),
            ("Very high", 0.80, 2.01),
        ]

        for name, lower, upper in bands:
            count = sum(
                lower <= value < upper
                for value in divergence
            )

            percentage = (
                count / len(divergence) * 100
            )

            print(
                f"{name:<12} "
                f"{count:>4} "
                f"({percentage:>6.2f}%)"
            )

        print()

        print("EXTREME DIVERGENCE")
        print("------------------")

        threshold = percentile(
            divergence,
            0.90,
        )

        print(
            f"90th percentile threshold: "
            f"{threshold:.6f}"
        )

        high_rows = [
            row
            for row in rows
            if float(
                row["intent_impact_divergence"]
            ) >= threshold
        ]

        print(
            f"PRs at/above threshold: "
            f"{len(high_rows)}"
        )

        print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()