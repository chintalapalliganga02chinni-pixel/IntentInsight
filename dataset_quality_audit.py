"""Quality audit for the IntentInsight research dataset."""

from __future__ import annotations

import sqlite3
from statistics import mean, median


DATABASE_PATH = "intentinsight.db"


def describe(values: list[int]) -> str:
    """Return basic descriptive statistics for integer values."""
    if not values:
        return "no values"

    return (
        f"count={len(values)}, "
        f"min={min(values)}, "
        f"median={median(values):.1f}, "
        f"mean={mean(values):.2f}, "
        f"max={max(values)}"
    )


def main() -> None:
    """Run the dataset quality audit."""

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    print("=" * 60)
    print("INTENTINSIGHT DATASET QUALITY AUDIT")
    print("=" * 60)

    total = connection.execute(
        "SELECT COUNT(*) FROM research_records"
    ).fetchone()[0]

    eligible = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE eligible = 1
        """
    ).fetchone()[0]

    excluded = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE eligible = 0
        """
    ).fetchone()[0]

    print()
    print("DATASET SIZE")
    print("------------")
    print(f"Total records:    {total}")
    print(f"Eligible records: {eligible}")
    print(f"Excluded records: {excluded}")
    print(f"Eligible rate:    {eligible / total * 100:.2f}%")

    rows = connection.execute(
        """
        SELECT
            total_files,
            source_file_count,
            test_file_count,
            documentation_file_count,
            configuration_file_count,
            other_file_count,
            additions,
            deletions,
            commits_count
        FROM research_records
        WHERE eligible = 1
        """
    ).fetchall()

    total_files = [
        int(row["total_files"])
        for row in rows
    ]

    source_files = [
        int(row["source_file_count"])
        for row in rows
    ]

    test_files = [
        int(row["test_file_count"])
        for row in rows
    ]

    documentation_files = [
        int(row["documentation_file_count"])
        for row in rows
    ]

    configuration_files = [
        int(row["configuration_file_count"])
        for row in rows
    ]

    other_files = [
        int(row["other_file_count"])
        for row in rows
    ]

    additions = [
        int(row["additions"])
        for row in rows
    ]

    deletions = [
        int(row["deletions"])
        for row in rows
    ]

    commits = [
        int(row["commits_count"])
        for row in rows
    ]

    print()
    print("ELIGIBLE RECORD FEATURES")
    print("------------------------")

    print(
        "Total changed files:       "
        + describe(total_files)
    )

    print(
        "Source-code files:         "
        + describe(source_files)
    )

    print(
        "Test files:                "
        + describe(test_files)
    )

    print(
        "Documentation files:       "
        + describe(documentation_files)
    )

    print(
        "Configuration files:       "
        + describe(configuration_files)
    )

    print(
        "Other files:               "
        + describe(other_files)
    )

    print(
        "Additions:                 "
        + describe(additions)
    )

    print(
        "Deletions:                 "
        + describe(deletions)
    )

    print(
        "Commits:                   "
        + describe(commits)
    )

    print()
    print("DATA QUALITY CHECKS")
    print("-------------------")

    duplicate_records = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                repository_id,
                pull_request_number,
                COUNT(*) AS occurrences
            FROM research_records
            GROUP BY repository_id, pull_request_number
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    invalid_file_totals = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE total_files != (
            source_file_count
            + test_file_count
            + documentation_file_count
            + configuration_file_count
            + other_file_count
        )
        """
    ).fetchone()[0]

    negative_values = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE total_files < 0
           OR source_file_count < 0
           OR test_file_count < 0
           OR documentation_file_count < 0
           OR configuration_file_count < 0
           OR other_file_count < 0
           OR additions < 0
           OR deletions < 0
           OR commits_count < 0
        """
    ).fetchone()[0]

    missing_repository_ids = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE repository_id IS NULL
        """
    ).fetchone()[0]

    missing_pull_request_numbers = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE pull_request_number IS NULL
        """
    ).fetchone()[0]

    missing_pull_requests = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records AS rr
        LEFT JOIN pull_requests AS pr
            ON pr.repository_id = rr.repository_id
           AND pr.number = rr.pull_request_number
        WHERE pr.id IS NULL
        """
    ).fetchone()[0]

    invalid_eligibility = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE eligible NOT IN (0, 1)
        """
    ).fetchone()[0]

    inconsistent_exclusion_reasons = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE (
            eligible = 1
            AND exclusion_reason IS NOT NULL
        )
        OR (
            eligible = 0
            AND exclusion_reason IS NULL
        )
        """
    ).fetchone()[0]

    merged_without_files = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE is_merged = 1
          AND total_files = 0
        """
    ).fetchone()[0]

    invalid_file_category_counts = connection.execute(
        """
        SELECT COUNT(*)
        FROM research_records
        WHERE source_file_count > total_files
           OR test_file_count > total_files
           OR documentation_file_count > total_files
           OR configuration_file_count > total_files
           OR other_file_count > total_files
        """
    ).fetchone()[0]

    print(
        f"Duplicate research records:       {duplicate_records}"
    )

    print(
        f"Invalid file-category totals:      {invalid_file_totals}"
    )

    print(
        f"Records with negative values:      {negative_values}"
    )

    print(
        f"Missing repository IDs:             {missing_repository_ids}"
    )

    print(
        f"Missing PR numbers:                 {missing_pull_request_numbers}"
    )

    print(
        f"Research records without PR:        {missing_pull_requests}"
    )

    print(
        f"Invalid eligibility values:         {invalid_eligibility}"
    )

    print(
        f"Inconsistent exclusion reasons:    "
        f"{inconsistent_exclusion_reasons}"
    )

    print(
        f"Merged records with zero files:     {merged_without_files}"
    )

    print(
        f"Invalid category counts:             "
        f"{invalid_file_category_counts}"
    )

    print()
    print("=" * 60)

    connection.close()


if __name__ == "__main__":
    main()