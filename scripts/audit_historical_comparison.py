"""Audit GitHub historical PR comparisons against PR file attribution."""

from __future__ import annotations

import sqlite3
from collections import Counter

from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient


DATABASE = "intentinsight.db"
OWNER = "pallets"
REPOSITORY = "flask"

# Deliberately small first validation sample.
SAMPLE_SIZE = 20


def main() -> None:
    print("=" * 72)
    print("IntentInsight Historical Comparison Audit")
    print("=" * 72)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            number,
            title,
            base_sha,
            head_sha,
            merged_at
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

    if not rows:
        raise RuntimeError("No anchored pull requests found.")

    settings = load_settings()

    with GitHubClient(settings) as github:
        for index, row in enumerate(rows, start=1):
            number = int(row["number"])

            print()
            print("-" * 72)
            print(
                f"[{index}/{len(rows)}] "
                f"PR #{number}: {row['title']}"
            )
            print("-" * 72)

            comparison = github.compare_commits(
                owner=OWNER,
                repository=REPOSITORY,
                base_sha=row["base_sha"],
                head_sha=row["head_sha"],
            )

            github_files = []

            page = 1

            while True:
                current_page = github.list_pull_request_files(
                    owner=OWNER,
                    repository=REPOSITORY,
                    pull_request_number=number,
                    page=page,
                    per_page=100,
                )

                if not current_page:
                    break

                github_files.extend(current_page)

                if len(current_page) < 100:
                    break

                page += 1

            comparison_counter = Counter(
                file.status
                for file in comparison.files
            )

            pr_counter = Counter(
                file.status
                for file in github_files
            )

            comparison_paths = {
                file.filename
                for file in comparison.files
            }

            pr_paths = {
                file.filename
                for file in github_files
            }

            missing_from_comparison = sorted(
                pr_paths - comparison_paths
            )

            extra_in_comparison = sorted(
                comparison_paths - pr_paths
            )

            print("Comparison status:", comparison.status)
            print("Ahead by:", comparison.ahead_by)
            print("Behind by:", comparison.behind_by)
            print("Merge base:", comparison.merge_base_sha)

            print()
            print("GitHub PR file count:", len(github_files))
            print("Comparison file count:", len(comparison.files))

            print()
            print("GitHub PR statuses:")
            for status, count in sorted(pr_counter.items()):
                print(f"  {status:10} {count}")

            print()
            print("Comparison statuses:")
            for status, count in sorted(comparison_counter.items()):
                print(f"  {status:10} {count}")

            print()
            print("Path agreement:")
            print(
                "  Exact filename agreement:",
                comparison_paths == pr_paths,
            )
            print(
                "  Missing from comparison:",
                len(missing_from_comparison),
            )
            print(
                "  Extra in comparison:",
                len(extra_in_comparison),
            )

            if missing_from_comparison:
                print("  Missing examples:")
                for path in missing_from_comparison[:10]:
                    print("   ", path)

            if extra_in_comparison:
                print("  Extra examples:")
                for path in extra_in_comparison[:10]:
                    print("   ", path)

            renamed = [
                file
                for file in comparison.files
                if file.status == "renamed"
            ]

            if renamed:
                print()
                print("Renamed files:")
                for file in renamed[:10]:
                    print(
                        f"  {file.previous_filename}"
                        f" -> {file.filename}"
                    )


if __name__ == "__main__":
    main()