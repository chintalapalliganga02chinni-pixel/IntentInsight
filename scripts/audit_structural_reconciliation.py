"""Reconcile stored structural metrics against current file records."""

from __future__ import annotations

import sqlite3


DATABASE = "intentinsight.db"


def main() -> None:
    """Compare stored structural metrics with current file rows."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    structural_rows = connection.execute(
        """
        SELECT
            repository_id,
            pull_request_number,
            module_count,
            changed_file_count,
            total_additions,
            total_deletions,
            total_changes,
            modified_file_count,
            added_file_count,
            removed_file_count,
            renamed_file_count
        FROM pull_request_structures
        ORDER BY pull_request_number
        """
    ).fetchall()

    print("=" * 72)
    print("IntentInsight Structural Reconciliation Audit")
    print("=" * 72)

    print()
    print(
        "Structural records:",
        len(structural_rows),
    )

    mismatches = []

    for row in structural_rows:
        files = connection.execute(
            """
            SELECT
                filename,
                status,
                additions,
                deletions,
                changes
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

        current_file_count = len(files)

        current_additions = sum(
            int(file["additions"] or 0)
            for file in files
        )

        current_deletions = sum(
            int(file["deletions"] or 0)
            for file in files
        )

        current_changes = sum(
            int(file["changes"] or 0)
            for file in files
        )

        current_modified = sum(
            file["status"] == "modified"
            for file in files
        )

        current_added = sum(
            file["status"] == "added"
            for file in files
        )

        current_removed = sum(
            file["status"] == "removed"
            for file in files
        )

        current_renamed = sum(
            file["status"] == "renamed"
            for file in files
        )

        differences = {
            "changed_file_count": (
                int(row["changed_file_count"])
                - current_file_count
            ),
            "total_additions": (
                int(row["total_additions"])
                - current_additions
            ),
            "total_deletions": (
                int(row["total_deletions"])
                - current_deletions
            ),
            "total_changes": (
                int(row["total_changes"])
                - current_changes
            ),
            "modified_file_count": (
                int(row["modified_file_count"])
                - current_modified
            ),
            "added_file_count": (
                int(row["added_file_count"])
                - current_added
            ),
            "removed_file_count": (
                int(row["removed_file_count"])
                - current_removed
            ),
            "renamed_file_count": (
                int(row["renamed_file_count"])
                - current_renamed
            ),
        }

        if any(
            difference != 0
            for difference in differences.values()
        ):
            mismatches.append(
                (
                    row,
                    len(files),
                    current_additions,
                    current_deletions,
                    current_changes,
                    current_modified,
                    current_added,
                    current_removed,
                    current_renamed,
                    differences,
                )
            )

    connection.close()

    print()
    print(
        "PRs with exact numerical agreement:",
        len(structural_rows) - len(mismatches),
    )

    print(
        "PRs with numerical mismatch:",
        len(mismatches),
    )

    print()
    print("=" * 72)
    print("FIRST 20 MISMATCHES")
    print("=" * 72)

    for (
        row,
        file_count,
        additions,
        deletions,
        changes,
        modified,
        added,
        removed,
        renamed,
        differences,
    ) in mismatches[:20]:
        print()
        print(
            f"PR #{row['pull_request_number']}"
        )

        print(
            "  Stored:",
            f"files={row['changed_file_count']},",
            f"additions={row['total_additions']},",
            f"deletions={row['total_deletions']},",
            f"changes={row['total_changes']}",
        )

        print(
            "  Current:",
            f"files={file_count},",
            f"additions={additions},",
            f"deletions={deletions},",
            f"changes={changes}",
        )

        print(
            "  Difference:",
            f"files={differences['changed_file_count']},",
            f"additions={differences['total_additions']},",
            f"deletions={differences['total_deletions']},",
            f"changes={differences['total_changes']}",
        )

        print(
            "  Status difference:",
            f"modified={differences['modified_file_count']},",
            f"added={differences['added_file_count']},",
            f"removed={differences['removed_file_count']},",
            f"renamed={differences['renamed_file_count']}",
        )

    print()
    print("=" * 72)
    print("RECONCILIATION COMPLETE")
    print("=" * 72)

    print()
    print(
        "No database records were modified."
    )


if __name__ == "__main__":
    main()