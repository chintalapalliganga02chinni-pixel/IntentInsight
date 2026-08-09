"""Tests for SQLite persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from intentinsight.domain.models import PullRequest
from intentinsight.infrastructure.database.repositories import (
    PullRequestRepository,
)
from intentinsight.infrastructure.database.schema import create_schema


def _create_connection() -> sqlite3.Connection:
    """Create an in-memory SQLite database."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_schema(connection)
    return connection


def test_database_schema_can_be_created() -> None:
    """The database schema should be created successfully."""
    connection = _create_connection()

    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    assert [row["name"] for row in tables] == [
        "pull_requests",
        "repositories",
        "sqlite_sequence",
    ]

    connection.close()


def test_pull_request_can_be_persisted() -> None:
    """A pull request should be stored in SQLite."""
    connection = _create_connection()

    connection.execute(
        """
        INSERT INTO repositories (
            owner,
            name,
            full_name,
            default_branch,
            html_url,
            mined_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "example",
            "repository",
            "example/repository",
            "main",
            "https://github.com/example/repository",
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    connection.commit()

    repository_id = connection.execute(
        "SELECT id FROM repositories"
    ).fetchone()["id"]

    repository = PullRequestRepository(connection)

    pull_request = PullRequest(
        repository="example/repository",
        number=1,
        title="Improve architecture",
        description="Refactor dependency handling.",
        author="developer",
        state="closed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        merged_at=datetime.now(timezone.utc),
        merge_commit_sha="abc123",
        commits_count=3,
        changed_files_count=5,
        additions=100,
        deletions=20,
    )

    pull_request_id = repository.save(
        repository_id=repository_id,
        pull_request=pull_request,
    )

    assert pull_request_id > 0
    assert repository.count() == 1

    connection.close()