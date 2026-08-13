"""Validate historical reconstruction against actual GitHub PR files."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient


DATABASE = "intentinsight.db"
OWNER = "pallets"
REPOSITORY = "flask"

DIVERGED_PRS = [
    113,
    117,
    121,
    128,
    142,
    162,
    167,
    187,
    200,
    201,
    230,
    265,
    297,
]

OUTPUT = Path(
    "results/external/historical_impact"
)
OUTPUT.mkdir(parents=True, exist_ok=True)


def fetch_all_pr_files(
    github: GitHubClient,
    number: int,
):
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
        WHERE number IN (
            113,117,121,128,142,162,167,
            187,200,201,230,265,297
        )
        ORDER BY number
        """
    ).fetchall()

    connection.close()

    if len(rows) != len(DIVERGED_PRS):
        raise RuntimeError(
            f"Expected {len(DIVERGED_PRS)} PRs, "
            f"found {len(rows)}."
        )

    settings = load_settings()

    results = []

    with GitHubClient(settings) as github:
        for row in rows:
            number = int(row["number"])

            print("=" * 72)
            print(f"PR #{number}: {row['title']}")
            print("=" * 72)

            actual = fetch_all_pr_files(
                github,
                number,
            )

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
                actual_paths
                & reconstructed_paths
            )

            union = (
                actual_paths
                | reconstructed_paths
            )

            precision = (
                len(intersection)
                / len(reconstructed_paths)
                if reconstructed_paths
                else 0.0
            )

            recall = (
                len(intersection)
                / len(actual_paths)
                if actual_paths
                else 0.0
            )

            jaccard = (
                len(intersection)
                / len(union)
                if union
                else 1.0
            )

            actual_additions = sum(
                file.additions
                for file in actual
            )
            actual_deletions = sum(
                file.deletions
                for file in actual
            )
            actual_changes = sum(
                file.changes
                for file in actual
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

            print(
                "Actual PR files:",
                len(actual_paths),
            )
            print(
                "Reconstructed files:",
                len(reconstructed_paths),
            )
            print(
                "Intersection:",
                len(intersection),
            )
            print(
                "Precision:",
                f"{precision:.4f}",
            )
            print(
                "Recall:",
                f"{recall:.4f}",
            )
            print(
                "Jaccard:",
                f"{jaccard:.4f}",
            )

            print()
            print(
                "Actual changes:",
                actual_changes,
            )
            print(
                "Reconstructed changes:",
                reconstructed_changes,
            )
            print(
                "Comparison status:",
                comparison.status,
            )
            print(
                "Ahead:",
                comparison.ahead_by,
                "Behind:",
                comparison.behind_by,
            )

            results.append(
                {
                    "pr_number": number,
                    "title": str(row["title"]),
                    "comparison_status": comparison.status,
                    "ahead_by": comparison.ahead_by,
                    "behind_by": comparison.behind_by,
                    "actual_files": len(actual_paths),
                    "reconstructed_files": len(
                        reconstructed_paths
                    ),
                    "intersection_files": len(
                        intersection
                    ),
                    "precision": precision,
                    "recall": recall,
                    "jaccard": jaccard,
                    "actual_additions": actual_additions,
                    "actual_deletions": actual_deletions,
                    "actual_changes": actual_changes,
                    "reconstructed_additions": (
                        reconstructed_additions
                    ),
                    "reconstructed_deletions": (
                        reconstructed_deletions
                    ),
                    "reconstructed_changes": (
                        reconstructed_changes
                    ),
                }
            )

    import csv

    output_path = (
        OUTPUT / "reconstruction_validation.csv"
    )

    with output_path.open(
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
    print("VALIDATION COMPLETE")
    print("=" * 72)
    print(
        "Results:",
        output_path,
    )
    print(
        "PRs validated:",
        len(results),
    )


if __name__ == "__main__":
    main()
