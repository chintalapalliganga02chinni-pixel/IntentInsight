"""Audit the collected IntentInsight research dataset."""

from __future__ import annotations

import sqlite3


DATABASE_PATH = "intentinsight.db"


def main() -> None:
    """Print the distribution of research-record eligibility."""
    connection = sqlite3.connect(DATABASE_PATH)

    rows = connection.execute(
        """
        SELECT
            exclusion_reason,
            COUNT(*) AS count
        FROM research_records
        GROUP BY exclusion_reason
        ORDER BY count DESC
        """
    ).fetchall()

    print("EXCLUSION REASONS")
    print("-----------------")

    for exclusion_reason, count in rows:
        label = (
            "ELIGIBLE"
            if exclusion_reason is None
            else exclusion_reason
        )

        print(f"{label}: {count}")

    connection.close()


if __name__ == "__main__":
    main()