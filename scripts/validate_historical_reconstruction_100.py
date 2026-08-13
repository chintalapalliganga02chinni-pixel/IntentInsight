"""Validate historical PR reconstruction against GitHub PR file truth."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient


DATABASE = "intentinsight.db"
OWNER = "pallets"
REPOSITORY = "flask"
SAMPLE_SIZE = 100

OUTPUT = Path(
    "results/external/historical_impact"
)
OUTPUT.mkdir(parents=True, exist_ok=True)


def fetch_all_pr_files(github: GitHubClient, number: int):
    files = []
    page = 1

    while True:
        current = github.list_pull_request_files(
            owner=OWNER,
            repository=REPOSITORY,
            pull_request_number=number,
            page=page,
            per_page=100,
        )

        if not current:
            break

        files.extend(current)

        if len(current) < 100:
            break

        page += 1

    return files


def main() -> None:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            number,
            title,
            base_sha,
            head_sha
        FROM pull_requests
        WHERE base_sha IS NOT NULL
          AND base_sha != ''
          AND head_sha IS NOT NULL
          AND head_sha != ''
        ORDER BY number
        LIMIT ?
        """,
        (SAMPLE_SIZE,),
    ).fetchall()

    connection.close()

    settings = load_settings()
    results = []

    with GitHubClient(settings) as github:
        for index, row in enumerate(rows, start=1):
            number = int(row["number"])

            print(
                f"[{index}/{len(rows)}] "
                f"PR #{number}: {row['title']}"
            )

            actual = fetch_all_pr_files(github, number)

            comparison = github.compare_commits(
                owner=OWNER,
                repository=REPOSITORY,
                base_sha=str(row["base_sha"]),
                head_sha=str(row["head_sha"]),
            )

            actual_paths = {
                file.filename
                for file in actual
            }

            reconstructed_paths = {
                file.filename
                for file in comparison.files
            }

            intersection = (
                actual_paths & reconstructed_paths
            )

            union = (
                actual_paths | reconstructed_paths
            )

            precision = (
                len(intersection)
                / len(reconstructed_paths)
                if reconstructed_paths
                else 1.0
            )

            recall = (
                len(intersection)
                / len(actual_paths)
                if actual_paths
                else 1.0
            )

            jaccard = (
                len(intersection)
                / len(union)
                if union
                else 1.0
            )

            actual_additions = sum(
                file.additions for file in actual
            )
            actual_deletions = sum(
                file.deletions for file in actual
            )
            actual_changes = sum(
                file.changes for file in actual
            )

            reconstructed_additions = sum(
                file.additions
                for file in comparison.files
            )
            reconstructed_deletions = sum(
                file.deletions
                for file in comparison.files
            )
            reconstructed_changes = sum(
                file.changes
                for file in comparison.files
            )

            results.append(
                {
                    "pr_number": number,
                    "comparison_status": comparison.status,
                    "ahead_by": comparison.ahead_by,
                    "behind_by": comparison.behind_by,
                    "actual_files": len(actual_paths),
                    "reconstructed_files": len(
                        reconstructed_paths
                    ),
                    "precision": precision,
                    "recall": recall,
                    "jaccard": jaccard,
                    "actual_additions": actual_additions,
                    "reconstructed_additions": (
                        reconstructed_additions
                    ),
                    "actual_deletions": actual_deletions,
                    "reconstructed_deletions": (
                        reconstructed_deletions
                    ),
                    "actual_changes": actual_changes,
                    "reconstructed_changes": (
                        reconstructed_changes
                    ),
                    "exact_file_match": (
                        actual_paths == reconstructed_paths
                    ),
                    "exact_change_match": (
                        actual_additions
                        == reconstructed_additions
                        and actual_deletions
                        == reconstructed_deletions
                        and actual_changes
                        == reconstructed_changes
                    ),
                }
            )

    output = OUTPUT / "reconstruction_validation_100.csv"

    with output.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=results[0].keys(),
        )
        writer.writeheader()
        writer.writerows(results)

    print()
    print("=" * 72)
    print("100-PR RECONSTRUCTION VALIDATION")
    print("=" * 72)

    total = len(results)

    exact_files = sum(
        bool(r["exact_file_match"])
        for r in results
    )

    exact_changes = sum(
        bool(r["exact_change_match"])
        for r in results
    )

    print("PRs validated:", total)
    print(
        "Exact file-set matches:",
        f"{exact_files}/{total}",
    )
    print(
        "Exact change matches:",
        f"{exact_changes}/{total}",
    )

    for status in sorted(
        {str(r["comparison_status"]) for r in results}
    ):
        subset = [
            r for r in results
            if r["comparison_status"] == status
        ]

        print()
        print(f"STATUS: {status}")
        print("Count:", len(subset))

        for metric in (
            "precision",
            "recall",
            "jaccard",
        ):
            mean = sum(
                float(r[metric])
                for r in subset
            ) / len(subset)

            print(
                f"Mean {metric}: {mean:.6f}"
            )

    print()
    print("Results:", output)
    print("Database was not modified.")


if __name__ == "__main__":
    main()
