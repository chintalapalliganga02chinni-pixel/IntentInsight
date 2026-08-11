"""Application service for semantic pull-request intent analysis."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.intent.intent_text import build_intent_text


def utc_now() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


class IntentAnalysisService:
    """Generate and persist semantic representations of PR intent."""

    def __init__(
            self,
            encoder: IntentEncoder,
    ) -> None:
        self._encoder = encoder

    def analyze_repository(
            self,
            connection: sqlite3.Connection,
    ) -> int:
        """Analyze eligible PRs that lack semantic representations."""

        rows = connection.execute(
            """
            SELECT
                pr.repository_id,
                pr.number,
                pr.title,
                pr.description
            FROM pull_requests AS pr
                     INNER JOIN research_records AS rr
                                ON rr.repository_id = pr.repository_id
                                    AND rr.pull_request_number = pr.number
                     LEFT JOIN pull_request_intents AS intent
                               ON intent.repository_id = pr.repository_id
                                   AND intent.pull_request_number = pr.number
            WHERE rr.eligible = 1
              AND intent.id IS NULL
            ORDER BY
                pr.repository_id,
                pr.number
            """
        ).fetchall()

        if not rows:
            return 0

        texts = [
            build_intent_text(
                title=str(row["title"]),
                description=str(row["description"]),
            )
            for row in rows
        ]

        embeddings = self._encoder.encode_many(texts)

        for row, text, embedding in zip(
                rows,
                texts,
                embeddings,
                strict=True,
        ):
            connection.execute(
                """
                INSERT INTO pull_request_intents (
                    repository_id,
                    pull_request_number,
                    title,
                    description,
                    combined_text,
                    model_name,
                    model_version,
                    embedding_dimension,
                    embedding_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["repository_id"]),
                    int(row["number"]),
                    str(row["title"]),
                    str(row["description"]),
                    text,
                    self._encoder.model_name,
                    self._encoder.model_version,
                    len(embedding),
                    json.dumps(embedding),
                    utc_now(),
                ),
            )

        connection.commit()

        return len(rows)