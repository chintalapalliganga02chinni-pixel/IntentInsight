"""Audit equivalence between current and historical Python module mappings.

READ-ONLY AUDIT.

For every research PR, derive Python modules from the same persisted
pull_request_files records using:

1. The current filename_to_module() mapping.
2. The historical path_to_module() mapping.

This audit does not modify the database.
It does not generate embeddings.
It does not call GitHub.
"""

from __future__ import annotations

import sqlite3
from statistics import mean, median

from intentinsight.analysis.structural.module_path import (
    filename_to_module,
)
from intentinsight.domain.services.historical_impact_mapper import (
    path_to_module,
)


DATABASE = "intentinsight.db"


def is_python_file(filename: str) -> bool:
    """Return whether a file is a Python source file."""

    normalized = filename.replace("\\", "/")

    return normalized.endswith(
        (".py", ".pyi")
    )


def main() -> None:
    """Run the Python-module mapping equivalence audit."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    prs = connection.execute(
        """
        SELECT
            repository_id,
            pull_request_number
        FROM research_records
        WHERE eligible = 1
        ORDER BY
            repository_id,
            pull_request_number
        """
    ).fetchall()

    print()
    print("=" * 72)
    print("IntentInsight Historical Python Equivalence Audit")
    print("=" * 72)
    print()
    print("PRs analysed:", len(prs))

    identical = 0
    current_subset = 0
    historical_subset = 0
    true_divergence = 0

    current_counts: list[int] = []
    historical_counts: list[int] = []
    jaccard_scores: list[float] = []

    total_current_only = 0
    total_historical_only = 0

    discrepancies: list[dict[str, object]] = []

    for index, pr in enumerate(prs, start=1):
        repository_id = int(
            pr["repository_id"]
        )

        pull_request_number = int(
            pr["pull_request_number"]
        )

        rows = connection.execute(
            """
            SELECT
                filename
            FROM pull_request_files
            WHERE repository_id = ?
              AND pull_request_number = ?
            ORDER BY id
            """,
            (
                repository_id,
                pull_request_number,
            ),
        ).fetchall()

        current_modules: set[str] = set()
        historical_modules: set[str] = set()

        for row in rows:
            filename = str(
                row["filename"]
            )

            if not is_python_file(filename):
                continue

            # Current structural mapping.
            current_module = filename_to_module(
                filename
            )

            # Historical mapping.
            historical_module = path_to_module(
                filename
            )

            current_modules.add(
                current_module
            )

            if historical_module is not None:
                historical_modules.add(
                    historical_module
                )

        current_counts.append(
            len(current_modules)
        )

        historical_counts.append(
            len(historical_modules)
        )

        current_only = (
                current_modules
                - historical_modules
        )

        historical_only = (
                historical_modules
                - current_modules
        )

        total_current_only += len(
            current_only
        )

        total_historical_only += len(
            historical_only
        )

        union = (
                current_modules
                | historical_modules
        )

        intersection = (
                current_modules
                & historical_modules
        )

        if not union:
            jaccard = 1.0
        else:
            jaccard = (
                    len(intersection)
                    / len(union)
            )

        jaccard_scores.append(
            jaccard
        )

        if current_modules == historical_modules:
            identical += 1

        elif historical_modules <= current_modules:
            historical_subset += 1

        elif current_modules <= historical_modules:
            current_subset += 1

        else:
            true_divergence += 1

        if current_modules != historical_modules:
            discrepancies.append(
                {
                    "repository_id": repository_id,
                    "pull_request_number": (
                        pull_request_number
                    ),
                    "current_modules": sorted(
                        current_modules
                    ),
                    "historical_modules": sorted(
                        historical_modules
                    ),
                    "current_only": sorted(
                        current_only
                    ),
                    "historical_only": sorted(
                        historical_only
                    ),
                    "jaccard": jaccard,
                }
            )

        if index % 100 == 0:
            print(
                f"{index}/{len(prs)} PRs audited"
            )

    connection.close()

    total = len(prs)

    print()
    print("=" * 72)
    print("EXACT MODULE EQUIVALENCE")
    print("=" * 72)

    print(
        "Identical module sets:",
        identical,
        f"({identical / total:.2%})",
    )

    print(
        "Non-identical module sets:",
        total - identical,
        f"({(total - identical) / total:.2%})",
        )

    print()
    print("=" * 72)
    print("SET RELATIONSHIPS")
    print("=" * 72)

    print(
        "Historical subset of current:",
        historical_subset,
        f"({historical_subset / total:.2%})",
    )

    print(
        "Current subset of historical:",
        current_subset,
        f"({current_subset / total:.2%})",
    )

    print(
        "True set divergence:",
        true_divergence,
        f"({true_divergence / total:.2%})",
    )

    print()
    print("=" * 72)
    print("CURRENT PYTHON MODULE COUNT")
    print("=" * 72)

    print(
        "Min:",
        min(current_counts),
    )

    print(
        "Median:",
        f"{median(current_counts):.4f}",
    )

    print(
        "Mean:",
        f"{mean(current_counts):.4f}",
    )

    print(
        "Max:",
        max(current_counts),
    )

    print()
    print("=" * 72)
    print("HISTORICAL PYTHON MODULE COUNT")
    print("=" * 72)

    print(
        "Min:",
        min(historical_counts),
    )

    print(
        "Median:",
        f"{median(historical_counts):.4f}",
    )

    print(
        "Mean:",
        f"{mean(historical_counts):.4f}",
    )

    print(
        "Max:",
        max(historical_counts),
    )

    differences = [
        current - historical
        for current, historical
        in zip(
            current_counts,
            historical_counts,
            strict=True,
        )
    ]

    print()
    print("=" * 72)
    print("MODULE COUNT DIFFERENCES")
    print("=" * 72)

    print(
        "Mean current - historical:",
        f"{mean(differences):.6f}",
    )

    print(
        "Median current - historical:",
        f"{median(differences):.6f}",
    )

    print(
        "Min current - historical:",
        min(differences),
    )

    print(
        "Max current - historical:",
        max(differences),
    )

    print()
    print("=" * 72)
    print("PYTHON MODULE JACCARD")
    print("=" * 72)

    print(
        "Min:",
        f"{min(jaccard_scores):.6f}",
    )

    print(
        "Median:",
        f"{median(jaccard_scores):.6f}",
    )

    print(
        "Mean:",
        f"{mean(jaccard_scores):.6f}",
    )

    print(
        "Max:",
        f"{max(jaccard_scores):.6f}",
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
    print("MODULE MEMBERSHIP DIFFERENCES")
    print("=" * 72)

    print(
        "Total current-only memberships:",
        total_current_only,
    )

    print(
        "Total historical-only memberships:",
        total_historical_only,
    )

    print()
    print("=" * 72)
    print("DISCREPANCIES")
    print("=" * 72)

    print(
        "PRs with module-set discrepancies:",
        len(discrepancies),
    )

    if discrepancies:
        print()
        print("FIRST 20 DISCREPANCIES")
        print("----------------------")

        for item in discrepancies[:20]:
            print()
            print(
                f"PR #{item['pull_request_number']}"
            )

            print(
                "Jaccard:",
                f"{item['jaccard']:.6f}",
            )

            print(
                "Current module count:",
                len(
                    item["current_modules"]
                ),
            )

            print(
                "Historical module count:",
                len(
                    item["historical_modules"]
                ),
            )

            if item["current_only"]:
                print(
                    "Current-only modules:"
                )

                for module in item[
                    "current_only"
                ][:20]:
                    print(
                        " ",
                        module,
                    )

            if item["historical_only"]:
                print(
                    "Historical-only modules:"
                )

                for module in item[
                    "historical_only"
                ][:20]:
                    print(
                        " ",
                        module,
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
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()