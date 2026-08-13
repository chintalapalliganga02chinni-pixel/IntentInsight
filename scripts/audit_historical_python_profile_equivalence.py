"""Audit numerical equivalence of current and historical Python profiles.

READ-ONLY AUDIT.

For every eligible PR, reconstruct the Python-only structural profile from
the persisted pull_request_files using the current module mapper and compare
it with the historical impact profile.

No database records are modified.
No embeddings are generated.
No GitHub requests are made.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from statistics import mean, median

from intentinsight.analysis.structural.module_path import (
    filename_to_module,
)
from intentinsight.domain.models.historical_impact import (
    HistoricalImpact,
    HistoricalImpactFile,
)
from intentinsight.domain.services.historical_impact_mapper import (
    path_to_module,
)
from intentinsight.domain.services.historical_impact_profile_builder import (
    build_historical_impact_profile,
)


DATABASE = "intentinsight.db"


def is_python_file(filename: str) -> bool:
    """Return whether a file is Python source."""

    normalized = filename.replace("\\", "/")

    return normalized.endswith((".py", ".pyi"))


def build_current_python_profile(
    rows: list[sqlite3.Row],
) -> dict[str, dict[str, object]]:
    """Aggregate Python files using the current module mapper."""

    modules: dict[str, dict[str, object]] = {}

    for row in rows:
        filename = str(row["filename"])

        if not is_python_file(filename):
            continue

        module = filename_to_module(filename)

        if module not in modules:
            modules[module] = {
                "file_count": 0,
                "additions": 0,
                "deletions": 0,
                "changes": 0,
                "statuses": set(),
            }

        data = modules[module]

        data["file_count"] = (
            int(data["file_count"]) + 1
        )
        data["additions"] = (
            int(data["additions"])
            + int(row["additions"] or 0)
        )
        data["deletions"] = (
            int(data["deletions"])
            + int(row["deletions"] or 0)
        )
        data["changes"] = (
            int(data["changes"])
            + int(row["changes"] or 0)
        )

        statuses = data["statuses"]
        assert isinstance(statuses, set)
        statuses.add(str(row["status"]))

    return modules


def build_historical_profile(
    rows: list[sqlite3.Row],
    pull_request_number: int,
) -> object:
    """Build the historical profile from the same file rows."""

    files = tuple(
        HistoricalImpactFile(
            filename=str(row["filename"]),
            status=str(row["status"]),
            additions=int(row["additions"] or 0),
            deletions=int(row["deletions"] or 0),
            changes=int(row["changes"] or 0),
            sha=str(row["sha"] or ""),
        )
        for row in rows
    )

    impact = HistoricalImpact(
        repository="",
        pull_request_number=pull_request_number,
        base_sha="",
        head_sha="",
        merge_base_sha=None,
        comparison_status="validated",
        ahead_by=0,
        behind_by=0,
        files=files,
    )

    return build_historical_impact_profile(impact)


def main() -> None:
    """Run the profile equivalence audit."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    prs = connection.execute(
        """
        SELECT
            repository_id,
            pull_request_number
        FROM research_records
        WHERE eligible = 1
        ORDER BY
            repository_id,
            pull_request_number
        """
    ).fetchall()

    print()
    print("=" * 72)
    print("IntentInsight Historical Python Profile Equivalence Audit")
    print("=" * 72)
    print()
    print("PRs analysed:", len(prs))

    if len(prs) != 703:
        raise RuntimeError(
            f"Expected 703 eligible PRs, found {len(prs)}."
        )

    exact_profiles = 0
    profile_mismatches = 0

    total_current_python_files = 0
    total_historical_python_files = 0

    total_current_additions = 0
    total_historical_additions = 0

    total_current_deletions = 0
    total_historical_deletions = 0

    total_current_changes = 0
    total_historical_changes = 0

    module_count_differences: list[int] = []
    file_count_differences: list[int] = []
    addition_differences: list[int] = []
    deletion_differences: list[int] = []
    change_differences: list[int] = []

    discrepancy_details: list[dict[str, object]] = []

    status_comparison: Counter[str] = Counter()

    for index, pr in enumerate(
        prs,
        start=1,
    ):
        repository_id = int(
            pr["repository_id"]
        )

        pull_request_number = int(
            pr["pull_request_number"]
        )

        rows = connection.execute(
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
            ORDER BY id
            """,
            (
                repository_id,
                pull_request_number,
            ),
        ).fetchall()

        current_modules = (
            build_current_python_profile(rows)
        )

        historical_profile = (
            build_historical_profile(
                rows,
                pull_request_number,
            )
        )

        historical_modules = {
            module.module: {
                "file_count": module.file_count,
                "additions": module.additions,
                "deletions": module.deletions,
                "changes": module.changes,
                "statuses": set(module.statuses),
            }
            for module in historical_profile.modules
        }

        current_module_names = set(
            current_modules
        )

        historical_module_names = set(
            historical_modules
        )

        if (
            current_module_names
            != historical_module_names
        ):
            status_comparison[
                "module_set_mismatch"
            ] += 1

        module_mismatch = False
        module_differences: list[dict[str, object]] = []

        for module in sorted(
            current_module_names
            | historical_module_names
        ):
            current = current_modules.get(module)
            historical = historical_modules.get(module)

            if current is None:
                module_mismatch = True

                module_differences.append(
                    {
                        "module": module,
                        "type": "historical_only",
                    }
                )

                continue

            if historical is None:
                module_mismatch = True

                module_differences.append(
                    {
                        "module": module,
                        "type": "current_only",
                    }
                )

                continue

            current_statuses = current["statuses"]
            historical_statuses = (
                historical["statuses"]
            )

            assert isinstance(
                current_statuses,
                set,
            )
            assert isinstance(
                historical_statuses,
                set,
            )

            if (
                int(current["file_count"])
                != int(historical["file_count"])
                or int(current["additions"])
                != int(historical["additions"])
                or int(current["deletions"])
                != int(historical["deletions"])
                or int(current["changes"])
                != int(historical["changes"])
                or current_statuses
                != historical_statuses
            ):
                module_mismatch = True

                module_differences.append(
                    {
                        "module": module,
                        "current": {
                            "file_count": int(
                                current["file_count"]
                            ),
                            "additions": int(
                                current["additions"]
                            ),
                            "deletions": int(
                                current["deletions"]
                            ),
                            "changes": int(
                                current["changes"]
                            ),
                            "statuses": sorted(
                                current_statuses
                            ),
                        },
                        "historical": {
                            "file_count": int(
                                historical["file_count"]
                            ),
                            "additions": int(
                                historical["additions"]
                            ),
                            "deletions": int(
                                historical["deletions"]
                            ),
                            "changes": int(
                                historical["changes"]
                            ),
                            "statuses": sorted(
                                historical_statuses
                            ),
                        },
                    }
                )

        current_file_count = sum(
            int(data["file_count"])
            for data in current_modules.values()
        )

        current_additions = sum(
            int(data["additions"])
            for data in current_modules.values()
        )

        current_deletions = sum(
            int(data["deletions"])
            for data in current_modules.values()
        )

        current_changes = sum(
            int(data["changes"])
            for data in current_modules.values()
        )

        historical_file_count = sum(
            module.file_count
            for module in historical_profile.modules
        )

        historical_additions = sum(
            module.additions
            for module in historical_profile.modules
        )

        historical_deletions = sum(
            module.deletions
            for module in historical_profile.modules
        )

        historical_changes = sum(
            module.changes
            for module in historical_profile.modules
        )

        total_current_python_files += (
            current_file_count
        )
        total_historical_python_files += (
            historical_file_count
        )

        total_current_additions += (
            current_additions
        )
        total_historical_additions += (
            historical_additions
        )

        total_current_deletions += (
            current_deletions
        )
        total_historical_deletions += (
            historical_deletions
        )

        total_current_changes += (
            current_changes
        )
        total_historical_changes += (
            historical_changes
        )

        module_count_differences.append(
            len(current_modules)
            - len(historical_modules)
        )

        file_count_differences.append(
            current_file_count
            - historical_file_count
        )

        addition_differences.append(
            current_additions
            - historical_additions
        )

        deletion_differences.append(
            current_deletions
            - historical_deletions
        )

        change_differences.append(
            current_changes
            - historical_changes
        )

        if module_mismatch:
            profile_mismatches += 1

            if len(discrepancy_details) < 20:
                discrepancy_details.append(
                    {
                        "pull_request_number": (
                            pull_request_number
                        ),
                        "differences": (
                            module_differences
                        ),
                    }
                )
        else:
            exact_profiles += 1

        if index % 100 == 0:
            print(
                f"{index}/{len(prs)} PRs audited"
            )

    connection.close()

    print()
    print("=" * 72)
    print("EXACT PROFILE AGREEMENT")
    print("=" * 72)

    print(
        "Exact numerical/module profiles:",
        exact_profiles,
        f"({exact_profiles / len(prs):.2%})",
    )

    print(
        "Profile mismatches:",
        profile_mismatches,
        f"({profile_mismatches / len(prs):.2%})",
    )

    print()
    print("=" * 72)
    print("PYTHON FILE COUNTS")
    print("=" * 72)

    print(
        "Current total:",
        total_current_python_files,
    )

    print(
        "Historical total:",
        total_historical_python_files,
    )

    print(
        "Difference:",
        total_current_python_files
        - total_historical_python_files,
    )

    print()
    print("=" * 72)
    print("ADDITIONS")
    print("=" * 72)

    print(
        "Current total:",
        total_current_additions,
    )

    print(
        "Historical total:",
        total_historical_additions,
    )

    print(
        "Difference:",
        total_current_additions
        - total_historical_additions,
    )

    print()
    print("=" * 72)
    print("DELETIONS")
    print("=" * 72)

    print(
        "Current total:",
        total_current_deletions,
    )

    print(
        "Historical total:",
        total_historical_deletions,
    )

    print(
        "Difference:",
        total_current_deletions
        - total_historical_deletions,
    )

    print()
    print("=" * 72)
    print("CHANGES")
    print("=" * 72)

    print(
        "Current total:",
        total_current_changes,
    )

    print(
        "Historical total:",
        total_historical_changes,
    )

    print(
        "Difference:",
        total_current_changes
        - total_historical_changes,
    )

    print()
    print("=" * 72)
    print("PER-PR DIFFERENCES")
    print("=" * 72)

    comparisons = [
        (
            "module_count",
            module_count_differences,
        ),
        (
            "python_file_count",
            file_count_differences,
        ),
        (
            "additions",
            addition_differences,
        ),
        (
            "deletions",
            deletion_differences,
        ),
        (
            "changes",
            change_differences,
        ),
    ]

    for name, differences in comparisons:
        print()
        print(name)

        print(
            "Mean difference:",
            f"{mean(differences):.6f}",
        )

        print(
            "Median difference:",
            f"{median(differences):.6f}",
        )

        print(
            "Min difference:",
            min(differences),
        )

        print(
            "Max difference:",
            max(differences),
        )

        print(
            "Identical:",
            sum(
                difference == 0
                for difference in differences
            ),
            f"({sum(difference == 0 for difference in differences) / len(differences):.2%})",
        )

    print()
    print("=" * 72)
    print("MODULE STATUS")
    print("=" * 72)

    for name, count in sorted(
        status_comparison.items()
    ):
        print(
            f"{name}: {count}"
        )

    if discrepancy_details:
        print()
        print("=" * 72)
        print("FIRST PROFILE DISCREPANCIES")
        print("=" * 72)

        for item in discrepancy_details:
            print()
            print(
                f"PR #{item['pull_request_number']}"
            )

            for difference in item[
                "differences"
            ][:10]:
                print(
                    difference
                )

    print()
    print("=" * 72)
    print("AUDIT COMPLETE")
    print("=" * 72)
    print()
    print(
        "No database records were modified."
    )
    print(
        "No embeddings were generated."
    )
    print(
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()