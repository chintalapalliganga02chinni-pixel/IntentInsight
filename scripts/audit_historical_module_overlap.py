"""Audit overlap between current and historical module representations."""

from __future__ import annotations

import json
import sqlite3
from statistics import mean, median

from intentinsight.domain.services.historical_impact_mapper import (
    path_to_module,
)


DATABASE = "intentinsight.db"


def jaccard(
    left: set[str],
    right: set[str],
) -> float:
    """Return Jaccard similarity between two sets."""
    union = left | right

    if not union:
        return 1.0

    return len(left & right) / len(union)


def main() -> None:
    """Compare current and historical module identities."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            repository_id,
            pull_request_number,
            module_profile_json
        FROM pull_request_structures
        ORDER BY pull_request_number
        """
    ).fetchall()

    print("=" * 72)
    print("IntentInsight Historical Module Overlap Audit")
    print("=" * 72)

    print()
    print("PRs analysed:", len(rows))

    jaccard_scores: list[float] = []
    current_counts: list[int] = []
    historical_counts: list[int] = []

    identical = 0
    historical_subset = 0
    current_subset = 0

    python_only_total = 0
    current_only_total = 0

    largest_differences: list[
        tuple[int, int, int, float]
    ] = []

    for row in rows:
        files = connection.execute(
            """
            SELECT filename
            FROM pull_request_files
            WHERE repository_id = ?
              AND pull_request_number = ?
            ORDER BY id
            """,
            (
                row["repository_id"],
                row["pull_request_number"],
            ),
        ).fetchall()

        current_profile = json.loads(
            row["module_profile_json"]
        )

        current_modules = {
            str(item["module"])
            for item in current_profile
        }

        historical_modules = {
            module
            for module in (
                path_to_module(
                    str(file["filename"])
                )
                for file in files
            )
            if module is not None
        }

        similarity = jaccard(
            current_modules,
            historical_modules,
        )

        jaccard_scores.append(similarity)

        current_counts.append(
            len(current_modules)
        )

        historical_counts.append(
            len(historical_modules)
        )

        if current_modules == historical_modules:
            identical += 1

        if historical_modules <= current_modules:
            historical_subset += 1

        if current_modules <= historical_modules:
            current_subset += 1

        python_only = (
            historical_modules
            - current_modules
        )

        current_only = (
            current_modules
            - historical_modules
        )

        python_only_total += len(
            python_only
        )

        current_only_total += len(
            current_only
        )

        largest_differences.append(
            (
                len(
                    current_modules
                )
                - len(
                    historical_modules
                ),
                int(
                    row["pull_request_number"]
                ),
                len(
                    current_only
                ),
                similarity,
            )
        )

    connection.close()

    print()
    print("=" * 72)
    print("MODULE COUNTS")
    print("=" * 72)

    print()
    print(
        "Current mean:",
        f"{mean(current_counts):.4f}",
    )

    print(
        "Historical mean:",
        f"{mean(historical_counts):.4f}",
    )

    print(
        "Current median:",
        f"{median(current_counts):.4f}",
    )

    print(
        "Historical median:",
        f"{median(historical_counts):.4f}",
    )

    print()
    print("=" * 72)
    print("SET RELATIONSHIPS")
    print("=" * 72)

    print()
    print(
        "Identical module sets:",
        f"{identical} "
        f"({identical / len(rows):.2%})",
    )

    print(
        "Historical is subset of current:",
        f"{historical_subset} "
        f"({historical_subset / len(rows):.2%})",
    )

    print(
        "Current is subset of historical:",
        f"{current_subset} "
        f"({current_subset / len(rows):.2%})",
    )

    print()
    print("=" * 72)
    print("JACCARD SIMILARITY")
    print("=" * 72)

    print()
    print(
        "Min:",
        f"{min(jaccard_scores):.4f}",
    )

    print(
        "Median:",
        f"{median(jaccard_scores):.4f}",
    )

    print(
        "Mean:",
        f"{mean(jaccard_scores):.4f}",
    )

    print(
        "Max:",
        f"{max(jaccard_scores):.4f}",
    )

    print()
    print(
        "Perfect overlap:",
        sum(
            score == 1.0
            for score in jaccard_scores
        ),
    )

    print(
        "Zero overlap:",
        sum(
            score == 0.0
            for score in jaccard_scores
        ),
    )

    print()
    print("=" * 72)
    print("MODULE DIFFERENCE")
    print("=" * 72)

    print()
    print(
        "Total historical-only module memberships:",
        python_only_total,
    )

    print(
        "Total current-only module memberships:",
        current_only_total,
    )

    print()
    print("=" * 72)
    print("LOWEST JACCARD OVERLAP")
    print("=" * 72)

    worst = sorted(
        (
            (
                similarity,
                pr_number,
                current_only,
            )
            for (
                _,
                pr_number,
                current_only,
                similarity,
            ) in largest_differences
        )
    )

    for (
        similarity,
        pr_number,
        current_only,
    ) in worst[:20]:
        print(
            f"PR #{pr_number}: "
            f"Jaccard={similarity:.4f}, "
            f"current-only={current_only}"
        )

    print()
    print("=" * 72)
    print("AUDIT COMPLETE")
    print("=" * 72)

    print()
    print(
        "No database records were modified."
    )


if __name__ == "__main__":
    main()