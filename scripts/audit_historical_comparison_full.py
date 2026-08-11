"""Full-population audit of historical GitHub PR comparisons."""

from __future__ import annotations

import sqlite3
from collections import Counter

from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient


DATABASE = "intentinsight.db"
OWNER = "pallets"
REPOSITORY = "flask"


def load_research_pull_requests(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """Load all anchored research pull requests."""
    connection.row_factory = sqlite3.Row

    return connection.execute(
        """
        SELECT
            repository_id,
            number,
            title,
            base_sha,
            head_sha
        FROM pull_requests
        WHERE base_sha IS NOT NULL
          AND base_sha != ''
          AND head_sha IS NOT NULL
          AND head_sha != ''
          AND EXISTS (
              SELECT 1
              FROM pull_request_structures s
              WHERE s.repository_id = pull_requests.repository_id
                AND s.pull_request_number = pull_requests.number
          )
        ORDER BY number
        """
    ).fetchall()


def load_database_files(
    connection: sqlite3.Connection,
    repository_id: int,
    pull_request_number: int,
) -> list[sqlite3.Row]:
    """Load stored changed-file records for one PR."""
    connection.row_factory = sqlite3.Row

    return connection.execute(
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
            repository_id,
            pull_request_number,
        ),
    ).fetchall()


def main() -> None:
    print("=" * 72)
    print("IntentInsight Full Historical Comparison Audit")
    print("=" * 72)

    connection = sqlite3.connect(DATABASE)

    pull_requests = load_research_pull_requests(connection)

    print()
    print("Research PRs:", len(pull_requests))

    if len(pull_requests) != 703:
        raise RuntimeError(
            "Expected exactly 703 research PRs."
        )

    exact_file_count = 0
    exact_filename = 0
    exact_status = 0

    total_github_files = 0
    total_database_files = 0

    diverged_count = 0
    ahead_count = 0
    behind_count = 0

    discrepancies: list[dict[str, object]] = []

    github_statuses = Counter()
    database_statuses = Counter()

    with GitHubClient(load_settings()) as github:
        for index, row in enumerate(pull_requests, start=1):
            number = int(row["number"])

            comparison = github.compare_commits(
                owner=OWNER,
                repository=REPOSITORY,
                base_sha=str(row["base_sha"]),
                head_sha=str(row["head_sha"]),
            )

            database_files = load_database_files(
                connection,
                repository_id=int(row["repository_id"]),
                pull_request_number=number,
            )

            github_files = comparison.files

            github_paths = {
                file.filename
                for file in github_files
            }

            database_paths = {
                str(file["filename"])
                for file in database_files
            }

            github_status_map = {
                file.filename: file.status
                for file in github_files
            }

            database_status_map = {
                str(file["filename"]): str(file["status"])
                for file in database_files
            }

            filename_match = github_paths == database_paths

            status_match = (
                filename_match
                and all(
                    github_status_map[path]
                    == database_status_map[path]
                    for path in github_paths
                )
            )

            file_count_match = (
                len(github_files)
                == len(database_files)
            )

            total_github_files += len(github_files)
            total_database_files += len(database_files)

            if file_count_match:
                exact_file_count += 1

            if filename_match:
                exact_filename += 1

            if status_match:
                exact_status += 1

            github_statuses.update(
                file.status
                for file in github_files
            )

            database_statuses.update(
                str(file["status"])
                for file in database_files
            )

            if comparison.status == "diverged":
                diverged_count += 1
            elif comparison.status == "ahead":
                ahead_count += 1
            elif comparison.status == "behind":
                behind_count += 1

            if not status_match:
                discrepancies.append(
                    {
                        "number": number,
                        "title": row["title"],
                        "comparison_status": comparison.status,
                        "github_count": len(github_files),
                        "database_count": len(database_files),
                        "missing_from_database": sorted(
                            github_paths - database_paths
                        ),
                        "extra_in_database": sorted(
                            database_paths - github_paths
                        ),
                    }
                )

            if index % 50 == 0:
                print(
                    f"  {index}/{len(pull_requests)} PRs audited"
                )

    connection.close()

    print()
    print("=" * 72)
    print("FULL AUDIT SUMMARY")
    print("=" * 72)

    print()
    print("PRs analysed:", len(pull_requests))

    print()
    print("EXACT AGREEMENT")

    print(
        "File count:",
        exact_file_count,
        f"({exact_file_count / len(pull_requests):.2%})",
    )

    print(
        "Filenames:",
        exact_filename,
        f"({exact_filename / len(pull_requests):.2%})",
    )

    print(
        "Statuses:",
        exact_status,
        f"({exact_status / len(pull_requests):.2%})",
    )

    print()
    print("TOTAL FILES")

    print("GitHub comparison:", total_github_files)
    print("Database records: ", total_database_files)

    print()
    print("COMPARISON STATUS")

    print("Ahead:   ", ahead_count)
    print("Diverged:", diverged_count)
    print("Behind:  ", behind_count)

    print()
    print("GITHUB FILE STATUSES")

    for status, count in sorted(github_statuses.items()):
        print(f"{status:10} {count}")

    print()
    print("DATABASE FILE STATUSES")

    for status, count in sorted(database_statuses.items()):
        print(f"{status:10} {count}")

    print()
    print("DISCREPANCIES:", len(discrepancies))

    if discrepancies:
        print()
        print("FIRST 20 DISCREPANCIES")

        for item in discrepancies[:20]:
            print()
            print(
                f"PR #{item['number']}: "
                f"{item['title']}"
            )
            print(
                "  Comparison status:",
                item["comparison_status"],
            )
            print(
                "  GitHub files:",
                item["github_count"],
            )
            print(
                "  Database files:",
                item["database_count"],
            )

            missing = item["missing_from_database"]
            extra = item["extra_in_database"]

            if missing:
                print("  Missing from database:")
                for path in missing[:10]:
                    print("   ", path)

            if extra:
                print("  Extra in database:")
                for path in extra[:10]:
                    print("   ", path)


if __name__ == "__main__":
    main()