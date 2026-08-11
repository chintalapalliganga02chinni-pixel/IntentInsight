"""Tests for SQLite persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from intentinsight.domain.models import PullRequest
from intentinsight.domain.models.research_record import ResearchRecord
from intentinsight.infrastructure.database.repositories import (
    CollectionRunRepository,
    PullRequestRepository,
    ResearchRecordRepository,
    RepositoryRepository,
)
from intentinsight.infrastructure.database.schema import create_schema
from intentinsight.infrastructure.github.models import RepositoryInfo


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
        "collection_runs",
        "pull_requests",
        "repositories",
        "research_records",
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


def test_research_record_can_be_persisted() -> None:
    """A research record should be persisted in SQLite."""
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

    connection.execute(
        """
        INSERT INTO pull_requests (
            repository_id,
            number,
            title,
            description,
            author,
            state,
            created_at,
            updated_at,
            merged_at,
            merge_commit_sha,
            commits_count,
            changed_files_count,
            additions,
            deletions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            repository_id,
            42,
            "Improve architecture",
            "Improve application structure.",
            "developer",
            "closed",
            "2026-01-01T00:00:00+00:00",
            "2026-01-02T00:00:00+00:00",
            "2026-01-02T00:00:00+00:00",
            "abc123",
            3,
            2,
            25,
            8,
        ),
    )

    connection.commit()

    record = ResearchRecord(
        repository="example/repository",
        pull_request_number=42,
        title="Improve architecture",
        description="Improve application structure.",
        author="developer",
        is_merged=True,
        merge_commit_sha="abc123",
        total_files=2,
        source_file_count=1,
        test_file_count=1,
        documentation_file_count=0,
        configuration_file_count=0,
        other_file_count=0,
        additions=25,
        deletions=8,
        commits_count=3,
        eligible=True,
        exclusion_reason=None,
    )

    repository = ResearchRecordRepository(connection)

    record_id = repository.save(
        repository_id=repository_id,
        record=record,
    )

    assert record_id > 0
    assert repository.count() == 1
    assert repository.count_eligible() == 1
    assert repository.count_excluded() == 0

    connection.close()


def test_repository_can_be_persisted() -> None:
    """Repository metadata should be stored in SQLite."""
    connection = _create_connection()

    repository = RepositoryRepository(connection)

    repository_info = RepositoryInfo(
        owner="example",
        name="repository",
        full_name="example/repository",
        default_branch="main",
        private=False,
        url="https://github.com/example/repository",
        stars=100,
        forks=20,
        open_issues=5,
    )

    repository_id = repository.save(repository_info)

    assert repository_id > 0
    assert repository.get_by_full_name(
        "example/repository"
    ) == repository_id

    connection.close()


def test_collection_run_can_be_persisted() -> None:
    """A collection run should be recorded in SQLite."""
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
        """
        SELECT id
        FROM repositories
        WHERE full_name = ?
        """,
        ("example/repository",),
    ).fetchone()["id"]

    repository = CollectionRunRepository(connection)

    started_at = datetime(
        2026,
        8,
        9,
        10,
        0,
        tzinfo=timezone.utc,
    )

    completed_at = datetime(
        2026,
        8,
        9,
        10,
        5,
        tzinfo=timezone.utc,
    )

    run_id = repository.save(
        repository_id=repository_id,
        started_at=started_at,
        completed_at=completed_at,
        status="success",
        pull_requests_discovered=100,
        records_created=100,
        eligible_records=42,
        excluded_records=58,
    )

    assert run_id > 0
    assert repository.count() == 1

    connection.close()
    def test_research_record_exists_can_be_checked() -> None:
        """An existing research record should be detectable."""
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

    repository = ResearchRecordRepository(connection)

    assert repository.exists(
        repository_id=repository_id,
        pull_request_number=42,
    ) is False

    connection.execute(
        """
        INSERT INTO research_records (
            repository_id,
            pull_request_number,
            is_merged,
            merge_commit_sha,
            total_files,
            source_file_count,
            test_file_count,
            documentation_file_count,
            configuration_file_count,
            other_file_count,
            additions,
            deletions,
            commits_count,
            eligible,
            exclusion_reason,
            collected_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            repository_id,
            42,
            1,
            "abc123",
            2,
            1,
            1,
            0,
            0,
            0,
            25,
            8,
            3,
            1,
            None,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    connection.commit()

    assert repository.exists(
        repository_id=repository_id,
        pull_request_number=42,
    ) is True

    connection.close()