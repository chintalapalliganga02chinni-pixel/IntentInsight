"""Compare existing and historical structural representations."""

from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from statistics import mean, median, stdev

from intentinsight.domain.models.historical_impact import (
    HistoricalImpact,
    HistoricalImpactFile,
)
from intentinsight.domain.services.historical_impact_profile_builder import (
    build_historical_impact_profile,
)


DATABASE = "intentinsight.db"


def percentile(
        values: list[float],
        p: float,
) -> float:
    """Return a linearly interpolated percentile."""
    ordered = sorted(values)

    if not ordered:
        raise ValueError(
            "Cannot calculate percentile of empty data."
        )

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * p

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower

    return (
            ordered[lower]
            + fraction
            * (
                    ordered[upper]
                    - ordered[lower]
            )
    )


def pearson(
        x: list[float],
        y: list[float],
) -> float:
    """Calculate Pearson correlation."""
    if len(x) != len(y):
        raise ValueError(
            "Correlation requires equal-length inputs."
        )

    if len(x) < 2:
        raise ValueError(
            "Correlation requires at least two observations."
        )

    x_mean = mean(x)
    y_mean = mean(y)

    numerator = sum(
        (a - x_mean) * (b - y_mean)
        for a, b in zip(x, y)
    )

    x_variance = sum(
        (a - x_mean) ** 2
        for a in x
    )

    y_variance = sum(
        (b - y_mean) ** 2
        for b in y
    )

    denominator = math.sqrt(
        x_variance * y_variance
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator


def summarize(
        name: str,
        values: list[float],
) -> None:
    """Print descriptive statistics."""
    print()
    print(name)
    print(
        f"  Min:    {min(values):.4f}"
    )
    print(
        f"  Q1:     {percentile(values, 0.25):.4f}"
    )
    print(
        f"  Median: {median(values):.4f}"
    )
    print(
        f"  Mean:   {mean(values):.4f}"
    )
    print(
        f"  Q3:     {percentile(values, 0.75):.4f}"
    )
    print(
        f"  Max:    {max(values):.4f}"
    )

    if len(values) > 1:
        print(
            f"  Std:    {stdev(values):.4f}"
        )


def load_historical_profiles(
        connection: sqlite3.Connection,
        structural_rows: list[sqlite3.Row],
) -> dict[int, dict[str, float]]:
    """Build historical profiles for all research PRs."""
    historical_by_pr: dict[
        int,
        dict[str, float],
    ] = {}

    for row in structural_rows:
        files = connection.execute(
            """
            SELECT
                filename,
                status,
                additions,
                deletions,
                changes,
                sha
            FROM pull_request_files
            WHERE repository_id = ?
              AND pull_request_number = ?
            ORDER BY filename
            """,
            (
                row["repository_id"],
                row["pull_request_number"],
            ),
        ).fetchall()

        impact = HistoricalImpact(
            repository="pallets/flask",
            pull_request_number=int(
                row["pull_request_number"]
            ),
            base_sha="",
            head_sha="",
            merge_base_sha=None,
            comparison_status="stored",
            ahead_by=0,
            behind_by=0,
            files=tuple(
                HistoricalImpactFile(
                    filename=str(
                        file["filename"]
                    ),
                    status=str(
                        file["status"]
                    ),
                    additions=int(
                        file["additions"]
                    ),
                    deletions=int(
                        file["deletions"]
                    ),
                    changes=int(
                        file["changes"]
                    ),
                    sha=str(
                        file["sha"]
                    ),
                )
                for file in files
            ),
        )

        profile = (
            build_historical_impact_profile(
                impact
            )
        )

        historical_by_pr[
            int(row["pull_request_number"])
        ] = {
            "module_count": float(
                profile.module_count
            ),
            "changed_file_count": float(
                profile.total_files
            ),
            "total_additions": float(
                profile.additions
            ),
            "total_deletions": float(
                profile.deletions
            ),
            "total_changes": float(
                profile.total_changes
            ),
            "package_count": float(
                profile.package_count
            ),
        }

    return historical_by_pr


def main() -> None:
    """Run the current-vs-historical structural audit."""
    print("=" * 72)
    print(
        "IntentInsight Current vs Historical "
        "Structural Comparison"
    )
    print("=" * 72)

    connection = sqlite3.connect(
        DATABASE
    )
    connection.row_factory = sqlite3.Row

    structural_rows = connection.execute(
        """
        SELECT
            repository_id,
            pull_request_number,
            module_count,
            changed_file_count,
            total_additions,
            total_deletions,
            total_changes,
            modified_file_count,
            added_file_count,
            removed_file_count,
            renamed_file_count
        FROM pull_request_structures
        ORDER BY pull_request_number
        """
    ).fetchall()

    if len(structural_rows) != 703:
        raise RuntimeError(
            f"Expected 703 structural records, "
            f"found {len(structural_rows)}."
        )

    print()
    print(
        "Current structural records:",
        len(structural_rows),
    )

    historical_by_pr = load_historical_profiles(
        connection,
        structural_rows,
    )

    print(
        "Historical profiles:",
        len(historical_by_pr),
    )

    current: dict[
        str,
        list[float],
    ] = defaultdict(list)

    historical: dict[
        str,
        list[float],
    ] = defaultdict(list)

    differences: dict[
        str,
        list[float],
    ] = defaultdict(list)

    metrics = (
        "module_count",
        "changed_file_count",
        "total_additions",
        "total_deletions",
        "total_changes",
    )

    for row in structural_rows:
        pr_number = int(
            row["pull_request_number"]
        )

        historical_row = historical_by_pr[
            pr_number
        ]

        for metric in metrics:
            current_value = float(
                row[metric]
            )

            historical_value = historical_row[
                metric
            ]

            current[metric].append(
                current_value
            )

            historical[metric].append(
                historical_value
            )

            differences[metric].append(
                historical_value
                - current_value
            )

    connection.close()

    print()
    print("=" * 72)
    print("DESCRIPTIVE COMPARISON")
    print("=" * 72)

    for metric in metrics:
        summarize(
            f"CURRENT {metric.upper()}",
            current[metric],
        )

        summarize(
            f"HISTORICAL {metric.upper()}",
            historical[metric],
        )

    print()
    print("=" * 72)
    print("HISTORICAL - CURRENT")
    print("=" * 72)

    for metric in metrics:
        values = differences[metric]

        identical = sum(
            value == 0
            for value in values
        )

        historical_higher = sum(
            value > 0
            for value in values
        )

        historical_lower = sum(
            value < 0
            for value in values
        )

        print()
        print(metric)

        print(
            "  Mean difference:",
            f"{mean(values):.4f}",
        )

        print(
            "  Median difference:",
            f"{median(values):.4f}",
        )

        print(
            "  Min difference:",
            f"{min(values):.4f}",
        )

        print(
            "  Max difference:",
            f"{max(values):.4f}",
        )

        print(
            "  Identical:",
            f"{identical} "
            f"({identical / len(values):.2%})",
        )

        print(
            "  Historical higher:",
            f"{historical_higher} "
            f"({historical_higher / len(values):.2%})",
        )

        print(
            "  Historical lower:",
            f"{historical_lower} "
            f"({historical_lower / len(values):.2%})",
        )

    print()
    print("=" * 72)
    print("CORRELATION")
    print("=" * 72)

    for metric in metrics:
        correlation = pearson(
            current[metric],
            historical[metric],
        )

        print(
            f"{metric:20} "
            f"r = {correlation:.6f}"
        )

    print()
    print("=" * 72)
    print("HISTORICAL PACKAGE COUNT")
    print("=" * 72)

    package_counts = [
        profile["package_count"]
        for profile in historical_by_pr.values()
    ]

    summarize(
        "HISTORICAL PACKAGE COUNT",
        package_counts,
    )

    print()
    print("=" * 72)
    print("LARGEST HISTORICAL DIFFERENCES")
    print("=" * 72)

    for metric in metrics:
        ranked = sorted(
            (
                (
                    abs(difference),
                    difference,
                    int(
                        row[
                            "pull_request_number"
                        ]
                    ),
                )
                for row, difference in zip(
                structural_rows,
                differences[metric],
            )
            ),
            reverse=True,
        )

        print()
        print(metric)

        for (
                _,
                difference,
                pr_number,
        ) in ranked[:10]:
            print(
                f"  PR #{pr_number}: "
                f"historical-current = "
                f"{difference:+.2f}"
            )

    print()
    print("=" * 72)
    print("AUDIT COMPLETE")
    print("=" * 72)

    print()
    print(
        "No database records were modified."
    )

    print(
        "No embeddings were generated."
    )

    print(
        "No divergence calculations were performed."
    )


if __name__ == "__main__":
    main()