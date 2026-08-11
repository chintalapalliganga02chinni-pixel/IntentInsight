"""Tests for the divergence analysis application service."""

from __future__ import annotations

import json
import sqlite3

from intentinsight.analysis.divergence.divergence_schema import (
    ensure_divergence_schema,
)
from intentinsight.application.services.divergence_analysis_service import (
    DivergenceAnalysisService,
)


def create_connection() -> sqlite3.Connection:
    """Create an in-memory database for the service test."""

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.executescript(
        """
        CREATE TABLE pull_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repository_id INTEGER NOT NULL,
            number INTEGER NOT NULL,
            UNIQUE(repository_id, number)
        );

        CREATE TABLE pull_request_intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repository_id INTEGER NOT NULL,
            pull_request_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            combined_text TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            embedding_dimension INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(repository_id, pull_request_number)
        );

        CREATE TABLE pull_request_structures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repository_id INTEGER NOT NULL,
            pull_request_number INTEGER NOT NULL,
            module_count INTEGER NOT NULL,
            changed_file_count INTEGER NOT NULL,
            total_additions INTEGER NOT NULL,
            total_deletions INTEGER NOT NULL,
            total_changes INTEGER NOT NULL,
            modified_file_count INTEGER NOT NULL,
            added_file_count INTEGER NOT NULL,
            removed_file_count INTEGER NOT NULL,
            renamed_file_count INTEGER NOT NULL,
            module_profile_json TEXT NOT NULL,
            structural_text TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            embedding_dimension INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(repository_id, pull_request_number)
        );
        """
    )

    ensure_divergence_schema(
        connection
    )

    return connection


def insert_test_data(
    connection: sqlite3.Connection,
) -> None:
    """Insert one matching intent/structure pair."""

    connection.execute(
        """
        INSERT INTO pull_requests (
            repository_id,
            number
        )
        VALUES (?, ?)
        """,
        (1, 42),
    )

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
            1,
            42,
            "Improve request handling",
            "Improve request handling.",
            "Improve request handling\nImprove request handling.",
            "test-model",
            "1",
            3,
            json.dumps([1.0, 0.0, 0.0]),
            "2026-01-01T00:00:00+00:00",
        ),
    )

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
            1,
            42,
            2,
            3,
            20,
            5,
            25,
            2,
            1,
            0,
            0,
            json.dumps(
                [
                    {
                        "module": "flask.app",
                        "file_count": 2,
                        "additions": 15,
                        "deletions": 4,
                        "changes": 19,
                        "weight": 3.0,
                        "statuses": {
                            "modified": 2
                        },
                    },
                    {
                        "module": "flask.ctx",
                        "file_count": 1,
                        "additions": 5,
                        "deletions": 1,
                        "changes": 6,
                        "weight": 1.0,
                        "statuses": {
                            "added": 1
                        },
                    },
                ]
            ),
            "Changed modules:\n- flask.app\n- flask.ctx",
            "test-model",
            "1",
            3,
            json.dumps([1.0, 0.0, 0.0]),
            "2026-01-01T00:00:00+00:00",
        ),
    )

    connection.commit()


def test_service_creates_divergence_record() -> None:
    """The service should persist one divergence record."""

    connection = create_connection()

    try:
        insert_test_data(connection)

        service = DivergenceAnalysisService()

        created = service.analyze(
            connection
        )

        assert created == 1

        row = connection.execute(
            """
            SELECT *
            FROM intent_impact_divergence
            """
        ).fetchone()

        assert row is not None

        assert row["repository_id"] == 1
        assert row["pull_request_number"] == 42

        assert row["intent_similarity"] == 1.0
        assert row["intent_impact_divergence"] == 0.0

        assert row["module_count"] == 2
        assert row["changed_file_count"] == 3

        assert row["module_concentration"] == 0.75
        assert row["package_count"] == 1
        assert row["cross_package_spread"] == 0

    finally:
        connection.close()


def test_service_is_idempotent() -> None:
    """Running the service twice should not create duplicates."""

    connection = create_connection()

    try:
        insert_test_data(connection)

        service = DivergenceAnalysisService()

        first_created = service.analyze(
            connection
        )

        second_created = service.analyze(
            connection
        )

        assert first_created == 1
        assert second_created == 0

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM intent_impact_divergence
            """
        ).fetchone()[0]

        assert count == 1

    finally:
        connection.close()


def test_service_ignores_intent_without_structure() -> None:
    """PRs without structural representations should be skipped."""

    connection = create_connection()

    try:
        connection.execute(
            """
            INSERT INTO pull_requests (
                repository_id,
                number
            )
            VALUES (?, ?)
            """,
            (1, 99),
        )

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
                1,
                99,
                "Test",
                "Test",
                "Test",
                "test-model",
                "1",
                3,
                json.dumps([1.0, 0.0, 0.0]),
                "2026-01-01T00:00:00+00:00",
            ),
        )

        connection.commit()

        service = DivergenceAnalysisService()

        created = service.analyze(
            connection
        )

        assert created == 0

    finally:
        connection.close()