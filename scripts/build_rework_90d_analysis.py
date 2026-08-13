import csv
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DB = "intentinsight.db"
OUTPUT = Path("rework_90d_analysis.csv")
WINDOW_DAYS = 90


def parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def path_to_module(filename):
    if not filename.endswith(".py"):
        return None

    path = filename.replace("\\", "/")

    if path.startswith("tests/"):
        return None

    if path.startswith("docs/"):
        return None

    parts = path[:-3].split("/")

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    if not parts:
        return None

    return ".".join(parts)


connection = sqlite3.connect(DB)
connection.row_factory = sqlite3.Row

try:
    eligible = connection.execute("""
        SELECT
            r.repository_id,
            r.pull_request_number,
            p.merged_at,

            d.intent_similarity,
            d.intent_impact_divergence,
            d.module_count,
            d.changed_file_count,
            d.module_entropy,
            d.module_concentration,
            d.top_module_weight,
            d.package_count,
            d.cross_package_spread,
            d.total_additions,
            d.total_deletions,
            d.total_changes,
            d.modified_file_count,
            d.added_file_count,
            d.removed_file_count,
            d.renamed_file_count

        FROM research_records AS r

        INNER JOIN pull_requests AS p
            ON p.repository_id = r.repository_id
            AND p.number = r.pull_request_number

        INNER JOIN intent_impact_divergence AS d
            ON d.repository_id = r.repository_id
            AND d.pull_request_number = r.pull_request_number

        WHERE r.eligible = 1
          AND r.is_merged = 1
          AND p.merged_at IS NOT NULL

        ORDER BY p.merged_at
    """).fetchall()

    merged_prs = connection.execute("""
        SELECT
            repository_id,
            number,
            merged_at
        FROM pull_requests
        WHERE merged_at IS NOT NULL
        ORDER BY merged_at
    """).fetchall()

    files = connection.execute("""
        SELECT
            repository_id,
            pull_request_number,
            filename
        FROM pull_request_files
    """).fetchall()

    modules_by_pr = defaultdict(set)

    for row in files:
        module = path_to_module(row["filename"])

        if module is not None:
            modules_by_pr[
                (
                    row["repository_id"],
                    row["pull_request_number"],
                )
            ].add(module)

    latest_merge = max(
        parse_time(row["merged_at"])
        for row in merged_prs
    )

    rows = []

    for index, row in enumerate(eligible, start=1):

        repository_id = row["repository_id"]
        pr_number = row["pull_request_number"]

        merged_at = parse_time(row["merged_at"])

        observation_end = (
            merged_at
            + timedelta(days=WINDOW_DAYS)
        )

        # Primary analysis excludes right-censored observations.
        if observation_end > latest_merge:
            continue

        original_modules = modules_by_pr[
            (repository_id, pr_number)
        ]

        later_rework_prs = []
        reworked_modules = set()
        first_rework_days = None

        for later in merged_prs:

            if later["repository_id"] != repository_id:
                continue

            later_time = parse_time(
                later["merged_at"]
            )

            if later_time <= merged_at:
                continue

            if later_time > observation_end:
                break

            later_modules = modules_by_pr[
                (
                    repository_id,
                    later["number"],
                )
            ]

            overlap = (
                original_modules
                & later_modules
            )

            if overlap:

                later_rework_prs.append(
                    later["number"]
                )

                reworked_modules.update(
                    overlap
                )

                days = (
                    later_time - merged_at
                ).total_seconds() / 86400.0

                if (
                    first_rework_days is None
                    or days < first_rework_days
                ):
                    first_rework_days = days

        rows.append({
            "repository_id": repository_id,
            "pull_request_number": pr_number,

            "merged_at": row["merged_at"],

            # IntentInsight
            "intent_similarity": row[
                "intent_similarity"
            ],
            "intent_impact_divergence": row[
                "intent_impact_divergence"
            ],

            # Structural / conventional predictors
            "module_count": row["module_count"],
            "changed_file_count": row[
                "changed_file_count"
            ],
            "module_entropy": row[
                "module_entropy"
            ],
            "module_concentration": row[
                "module_concentration"
            ],
            "top_module_weight": row[
                "top_module_weight"
            ],
            "package_count": row["package_count"],
            "cross_package_spread": row[
                "cross_package_spread"
            ],
            "total_additions": row[
                "total_additions"
            ],
            "total_deletions": row[
                "total_deletions"
            ],
            "total_changes": row[
                "total_changes"
            ],
            "modified_file_count": row[
                "modified_file_count"
            ],
            "added_file_count": row[
                "added_file_count"
            ],
            "removed_file_count": row[
                "removed_file_count"
            ],
            "renamed_file_count": row[
                "renamed_file_count"
            ],

            # Future outcome
            "rework_90d": int(
                bool(later_rework_prs)
            ),
            "rework_pr_count_90d": len(
                later_rework_prs
            ),
            "reworked_module_count_90d": len(
                reworked_modules
            ),
            "days_to_first_rework": (
                ""
                if first_rework_days is None
                else round(
                    first_rework_days,
                    6,
                )
            ),
        })

        if index % 100 == 0:
            print(
                f"{index}/{len(eligible)} "
                "eligible PRs processed"
            )

    if not rows:
        raise RuntimeError(
            "No fully observable rows were produced."
        )

    fields = list(rows[0].keys())

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)

    positive = sum(
        row["rework_90d"] == 1
        for row in rows
    )

    negative = len(rows) - positive

    print()
    print("=" * 72)
    print("90-DAY REWORK ANALYSIS DATASET")
    print("=" * 72)
    print()
    print(f"Rows written:       {len(rows)}")
    print(f"Rework = 1:         {positive}")
    print(f"Rework = 0:         {negative}")
    print(
        f"Rework prevalence:  "
        f"{positive / len(rows) * 100:.2f}%"
    )
    print()
    print(f"Output: {OUTPUT}")
    print()
    print("Database was not modified.")
    print("No GitHub requests were made.")

finally:
    connection.close()
