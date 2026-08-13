"""Audit real GitHub historical PR impact reconstruction."""

from __future__ import annotations

import sqlite3

from intentinsight.domain.services.historical_impact_mapper import (
    comparison_to_historical_impact,
)
from intentinsight.domain.services.historical_impact_profile_builder import (
    build_historical_impact_profile,
)
from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient


DATABASE = "intentinsight.db"
OWNER = "pallets"
REPOSITORY = "flask"

SAMPLE_SIZE = 100


def main() -> None:
    print("=" * 72)
    print("IntentInsight Historical Impact Reconstruction Audit")
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

    print()
    print("Sample size:", len(rows))
    print()

    settings = load_settings()

    successful = 0
    total_files = 0
    total_additions = 0
    total_deletions = 0
    total_changes = 0
    total_python_modules = 0
    total_non_python_files = 0

    status_counts: dict[str, int] = {}
    diverged_prs: list[dict[str, int | str]] = []

    with GitHubClient(settings) as github:
        for index, row in enumerate(rows, start=1):
            number = int(row["number"])

            print("-" * 72)
            print(
                f"[{index}/{len(rows)}] "
                f"PR #{number}: {row['title']}"
            )
            print("-" * 72)

            comparison = github.compare_commits(
                owner=OWNER,
                repository=REPOSITORY,
                base_sha=str(row["base_sha"]),
                head_sha=str(row["head_sha"]),
            )

            impact = comparison_to_historical_impact(
                repository=f"{OWNER}/{REPOSITORY}",
                pull_request_number=number,
                comparison=comparison,
            )

            profile = build_historical_impact_profile(impact)

            successful += 1

            total_files += impact.total_files
            total_additions += impact.additions
            total_deletions += impact.deletions
            total_changes += impact.total_changes
            total_python_modules += len(profile.modules)
            total_non_python_files += profile.non_python_file_count

            status_counts[impact.comparison_status] = (
                status_counts.get(impact.comparison_status, 0) + 1
            )

            if impact.comparison_status == "diverged":
                diverged_prs.append(
                    {
                        "number": number,
                        "title": str(row["title"]),
                        "ahead_by": impact.ahead_by,
                        "behind_by": impact.behind_by,
                        "files": impact.total_files,
                        "changes": impact.total_changes,
                    }
                )

            print("Comparison status:", impact.comparison_status)
            print("Ahead by:", impact.ahead_by)
            print("Behind by:", impact.behind_by)
            print("Merge base:", impact.merge_base_sha)
            print()
            print("Historical impact files:", impact.total_files)
            print("Historical additions:", impact.additions)
            print("Historical deletions:", impact.deletions)
            print("Historical changes:", impact.total_changes)
            print("Python modules:", len(profile.modules))
            print(
                "Non-Python files:",
                profile.non_python_file_count,
            )

            if profile.modules:
                print("Modules:")
                for module in profile.modules[:10]:
                    print(
                        f"  {module.module} "
                        f"({module.file_count} files, "
                        f"+{module.additions}/"
                        f"-{module.deletions})"
                    )

            print()

    print("=" * 72)
    print("HISTORICAL IMPACT AUDIT SUMMARY")
    print("=" * 72)

    print("PRs successfully reconstructed:", successful)
    print("Total reconstructed files:", total_files)
    print("Total additions:", total_additions)
    print("Total deletions:", total_deletions)
    print("Total changes:", total_changes)
    print("Total Python modules:", total_python_modules)
    print("Total non-Python files:", total_non_python_files)

    if successful:
        print()
        print(
            "Average files / PR:",
            f"{total_files / successful:.2f}",
        )
        print(
            "Average Python modules / PR:",
            f"{total_python_modules / successful:.2f}",
        )

    print()
    print("COMPARISON STATUS SUMMARY")
    print("-" * 72)

    for status, count in sorted(status_counts.items()):
        print(f"{status}: {count}")

    if diverged_prs:
        print()
        print("DIVERGED PRs")
        print("-" * 72)

        for item in sorted(
            diverged_prs,
            key=lambda value: (
                int(value["behind_by"]),
                int(value["files"]),
                int(value["changes"]),
            ),
            reverse=True,
        ):
            print(
                f"PR #{item['number']}: {item['title']}"
            )
            print(
                f"  ahead={item['ahead_by']} "
                f"behind={item['behind_by']} "
                f"files={item['files']} "
                f"changes={item['changes']}"
            )

    print()
    print("Database was not modified.")
    print("No embeddings were generated.")


if __name__ == "__main__":
    main()
