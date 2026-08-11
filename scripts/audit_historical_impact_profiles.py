"""Audit historical structural impact profiles without modifying the database."""

from __future__ import annotations

import sqlite3
from collections import Counter

from intentinsight.domain.models.historical_impact import (
    HistoricalImpact,
    HistoricalImpactFile,
)
from intentinsight.domain.services.historical_impact_profile_builder import (
    build_historical_impact_profile,
)


DATABASE = "intentinsight.db"


def main() -> None:
    print("=" * 72)
    print("IntentInsight Historical Impact Profile Audit")
    print("=" * 72)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    pull_requests = connection.execute(
        """
        SELECT
            repository_id,
            number,
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

    if len(pull_requests) != 703:
        raise RuntimeError(
            f"Expected 703 research PRs, found {len(pull_requests)}."
        )

    module_counts: list[int] = []
    package_counts: list[int] = []
    total_file_counts: list[int] = []
    non_python_counts: list[int] = []
    additions: list[int] = []
    deletions: list[int] = []
    total_changes: list[int] = []

    status_counts: Counter[str] = Counter()

    zero_module_prs: list[int] = []
    high_module_prs: list[tuple[int, int]] = []

    for index, row in enumerate(pull_requests, start=1):
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
                row["number"],
            ),
        ).fetchall()

        impact_files = tuple(
            HistoricalImpactFile(
                filename=str(file["filename"]),
                status=str(file["status"]),
                additions=int(file["additions"]),
                deletions=int(file["deletions"]),
                changes=int(file["changes"]),
                sha=str(file["sha"]),
            )
            for file in files
        )

        impact = HistoricalImpact(
            repository="pallets/flask",
            pull_request_number=int(row["number"]),
            base_sha=str(row["base_sha"]),
            head_sha=str(row["head_sha"]),
            merge_base_sha=None,
            comparison_status="stored",
            ahead_by=0,
            behind_by=0,
            files=impact_files,
        )

        profile = build_historical_impact_profile(impact)

        module_counts.append(profile.module_count)
        package_counts.append(profile.package_count)
        total_file_counts.append(profile.total_files)
        non_python_counts.append(profile.non_python_file_count)
        additions.append(profile.additions)
        deletions.append(profile.deletions)
        total_changes.append(profile.total_changes)

        status_counts.update(
            file.status
            for file in impact_files
        )

        if profile.module_count == 0:
            zero_module_prs.append(int(row["number"]))

        high_module_prs.append(
            (
                int(row["number"]),
                profile.module_count,
            )
        )

        if index % 100 == 0:
            print(
                f"{index}/{len(pull_requests)} PRs profiled"
            )

    connection.close()

    high_module_prs.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    def summary(values: list[int]) -> tuple[int, float, int, int]:
        return (
            min(values),
            sum(values) / len(values),
            sorted(values)[len(values) // 2],
            max(values),
        )

    print()
    print("=" * 72)
    print("HISTORICAL IMPACT PROFILE SUMMARY")
    print("=" * 72)

    print()
    print("PRs analysed:", len(pull_requests))

    print()
    print("MODULE COUNT")
    minimum, mean, median, maximum = summary(module_counts)
    print("Min:", minimum)
    print("Mean:", f"{mean:.4f}")
    print("Median:", median)
    print("Max:", maximum)

    print()
    print("PACKAGE COUNT")
    minimum, mean, median, maximum = summary(package_counts)
    print("Min:", minimum)
    print("Mean:", f"{mean:.4f}")
    print("Median:", median)
    print("Max:", maximum)

    print()
    print("TOTAL FILE COUNT")
    minimum, mean, median, maximum = summary(total_file_counts)
    print("Min:", minimum)
    print("Mean:", f"{mean:.4f}")
    print("Median:", median)
    print("Max:", maximum)

    print()
    print("NON-PYTHON FILE COUNT")
    minimum, mean, median, maximum = summary(non_python_counts)
    print("Min:", minimum)
    print("Mean:", f"{mean:.4f}")
    print("Median:", median)
    print("Max:", maximum)

    print()
    print("TOTAL ADDITIONS")
    minimum, mean, median, maximum = summary(additions)
    print("Min:", minimum)
    print("Mean:", f"{mean:.4f}")
    print("Median:", median)
    print("Max:", maximum)

    print()
    print("TOTAL DELETIONS")
    minimum, mean, median, maximum = summary(deletions)
    print("Min:", minimum)
    print("Mean:", f"{mean:.4f}")
    print("Median:", median)
    print("Max:", maximum)

    print()
    print("TOTAL CHANGES")
    minimum, mean, median, maximum = summary(total_changes)
    print("Min:", minimum)
    print("Mean:", f"{mean:.4f}")
    print("Median:", median)
    print("Max:", maximum)

    print()
    print("FILE STATUSES")
    for status, count in sorted(status_counts.items()):
        print(f"{status:10} {count}")

    print()
    print("PRs WITH ZERO PYTHON MODULES:", len(zero_module_prs))

    if zero_module_prs:
        print(
            "Examples:",
            zero_module_prs[:20],
        )

    print()
    print("TOP 10 PRs BY MODULE COUNT")

    for number, module_count in high_module_prs[:10]:
        print(
            f"PR #{number}: {module_count} modules"
        )


if __name__ == "__main__":
    main()