"""Characterize paths excluded by the historical Python-module mapper."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter


DATABASE = "intentinsight.db"


def classify_path(filename: str) -> str:
    """Classify a non-Python repository path."""
    lower = filename.lower()

    if (
        lower.startswith("docs/")
        or lower.startswith("doc/")
        or "/docs/" in lower
        or "/doc/" in lower
        or lower.endswith((".rst", ".md", ".txt"))
    ):
        return "documentation"

    if (
        lower.endswith(
            (
                ".json",
                ".toml",
                ".yaml",
                ".yml",
                ".ini",
                ".cfg",
                ".conf",
                ".xml",
            )
        )
        or lower in {
            "makefile",
            "dockerfile",
        }
    ):
        return "configuration/build"

    if (
        lower.startswith("tests/")
        or lower.startswith("test/")
        or "/tests/" in lower
        or "/test/" in lower
        or lower.startswith("testsuite/")
    ):
        return "tests"

    if lower.endswith(
        (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            ".eps",
            ".pdf",
            ".css",
            ".js",
        )
    ):
        return "assets/frontend"

    return "other"


def main() -> None:
    """Run the exclusion characterization audit."""
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

    category_counts: Counter[str] = Counter()
    filename_counts: Counter[str] = Counter()

    affected_prs = 0
    excluded_files = 0

    for row in rows:
        current_profile = json.loads(
            row["module_profile_json"]
        )

        current_modules = {
            str(item["module"])
            for item in current_profile
        }

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

        excluded_for_pr = []

        for file in files:
            filename = str(file["filename"])

            if not filename.lower().endswith(
                (".py", ".pyi")
            ):
                excluded_for_pr.append(filename)

        if excluded_for_pr:
            affected_prs += 1
            excluded_files += len(
                excluded_for_pr
            )

        for filename in excluded_for_pr:
            category = classify_path(filename)

            category_counts[category] += 1
            filename_counts[filename] += 1

    connection.close()

    print("=" * 72)
    print(
        "IntentInsight Historical Module Exclusion Audit"
    )
    print("=" * 72)

    print()
    print("PRs analysed:", len(rows))
    print(
        "PRs with excluded non-Python files:",
        affected_prs,
    )
    print(
        "Excluded non-Python file records:",
        excluded_files,
    )

    print()
    print("=" * 72)
    print("EXCLUDED PATH CATEGORIES")
    print("=" * 72)

    for category, count in (
        category_counts.most_common()
    ):
        print(
            f"{category:24} {count}"
        )

    print()
    print("=" * 72)
    print("MOST COMMON EXCLUDED FILES")
    print("=" * 72)

    for filename, count in (
        filename_counts.most_common(30)
    ):
        print(
            f"{count:5}  {filename}"
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