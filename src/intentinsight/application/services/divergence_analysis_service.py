"""Application service for intent-impact divergence analysis."""

from __future__ import annotations

import json
import sqlite3

from intentinsight.analysis.divergence.divergence_analysis import (
    calculate_divergence_metrics,
    parse_embedding,
    parse_module_profile,
    utc_now,
)


class DivergenceAnalysisService:
    """Calculate and persist divergence metrics for eligible PRs."""

    def analyze(
        self,
        connection: sqlite3.Connection,
    ) -> int:
        """
        Calculate divergence for PRs that have both intent and
        structural representations.

        Existing divergence records are skipped so the operation
        is safely repeatable.
        """

        rows = connection.execute(
            """
            SELECT
                intents.repository_id,
                intents.pull_request_number,

                intents.embedding_json AS intent_embedding,

                structures.embedding_json AS structural_embedding,
                structures.module_profile_json,
                structures.changed_file_count,

                structures.total_additions,
                structures.total_deletions,
                structures.total_changes,

                structures.modified_file_count,
                structures.added_file_count,
                structures.removed_file_count,
                structures.renamed_file_count

            FROM pull_request_intents AS intents

            INNER JOIN pull_request_structures AS structures
                ON structures.repository_id = intents.repository_id
                AND structures.pull_request_number =
                    intents.pull_request_number

            LEFT JOIN intent_impact_divergence AS existing
                ON existing.repository_id = intents.repository_id
                AND existing.pull_request_number =
                    intents.pull_request_number

            WHERE existing.id IS NULL

            ORDER BY
                intents.repository_id,
                intents.pull_request_number
            """
        ).fetchall()

        created = 0

        for row in rows:
            intent_embedding = parse_embedding(
                row["intent_embedding"]
            )

            structural_embedding = parse_embedding(
                row["structural_embedding"]
            )

            module_profile = parse_module_profile(
                row["module_profile_json"]
            )

            metrics = calculate_divergence_metrics(
                intent_embedding=intent_embedding,
                structural_embedding=structural_embedding,
                module_profile=module_profile,
                changed_file_count=int(
                    row["changed_file_count"]
                ),
            )

            connection.execute(
                """
                INSERT INTO intent_impact_divergence (
                    repository_id,
                    pull_request_number,

                    intent_similarity,
                    intent_impact_divergence,

                    module_count,
                    changed_file_count,

                    module_entropy,
                    module_concentration,
                    top_module_weight,

                    package_count,
                    cross_package_spread,

                    total_additions,
                    total_deletions,
                    total_changes,

                    modified_file_count,
                    added_file_count,
                    removed_file_count,
                    renamed_file_count,

                    created_at
                )
                VALUES (
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?
                )
                """,
                (
                    int(row["repository_id"]),
                    int(row["pull_request_number"]),

                    metrics.intent_similarity,
                    metrics.intent_impact_divergence,

                    metrics.module_count,
                    metrics.changed_file_count,

                    metrics.module_entropy,
                    metrics.module_concentration,
                    metrics.top_module_weight,

                    metrics.package_count,
                    metrics.cross_package_spread,

                    int(row["total_additions"]),
                    int(row["total_deletions"]),
                    int(row["total_changes"]),

                    int(row["modified_file_count"]),
                    int(row["added_file_count"]),
                    int(row["removed_file_count"]),
                    int(row["renamed_file_count"]),

                    utc_now(),
                ),
            )

            created += 1

            if created % 100 == 0:
                connection.commit()
                print(
                    f"Divergence records created: {created}"
                )

        connection.commit()

        return created