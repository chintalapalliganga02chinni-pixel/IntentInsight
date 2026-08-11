"""Application service for structural pull-request analysis."""

from __future__ import annotations

import json
import sqlite3

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.structural.structural_representation import (
    StructuralRepresentationBuilder,
    utc_now,
)


class StructuralAnalysisService:
    """Generate structural representations for eligible pull requests."""

    def __init__(
        self,
        encoder: IntentEncoder,
    ) -> None:
        self._builder = StructuralRepresentationBuilder(
            encoder=encoder,
        )

    def analyze_repository(
        self,
        connection: sqlite3.Connection,
    ) -> int:
        """Analyze eligible PRs without existing structural records."""

        prs = connection.execute(
            """
            SELECT
                rr.repository_id,
                rr.pull_request_number
            FROM research_records AS rr
            LEFT JOIN pull_request_structures AS structure
                ON structure.repository_id = rr.repository_id
                AND structure.pull_request_number = rr.pull_request_number
            WHERE rr.eligible = 1
              AND structure.id IS NULL
            ORDER BY
                rr.repository_id,
                rr.pull_request_number
            """
        ).fetchall()

        created = 0

        for pr in prs:
            repository_id = int(pr["repository_id"])
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
                    changes
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

            file_rows = [
                dict(row)
                for row in rows
            ]

            representation = self._builder.build(
                file_rows,
            )

            embedding = representation["embedding"]

            connection.execute(
                """
                INSERT INTO pull_request_structures (
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
                    renamed_file_count,
                    module_profile_json,
                    structural_text,
                    model_name,
                    model_version,
                    embedding_dimension,
                    embedding_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    repository_id,
                    pull_request_number,
                    int(representation["module_count"]),
                    int(representation["changed_file_count"]),
                    int(representation["total_additions"]),
                    int(representation["total_deletions"]),
                    int(representation["total_changes"]),
                    int(representation["modified_file_count"]),
                    int(representation["added_file_count"]),
                    int(representation["removed_file_count"]),
                    int(representation["renamed_file_count"]),
                    json.dumps(
                        representation["module_profile"],
                        sort_keys=True,
                    ),
                    str(representation["structural_text"]),
                    self._builder._encoder.model_name,
                    self._builder._encoder.model_version,
                    len(embedding),
                    json.dumps(embedding),
                    utc_now(),
                ),
            )

            created += 1

            if created % 50 == 0:
                connection.commit()
                print(
                    f"Structural records created: {created}"
                )

        connection.commit()

        return created