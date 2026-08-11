"""Database repositories for research entities."""

from __future__ import annotations

from datetime import datetime, timezone

import sqlite3

from intentinsight.domain.models import PullRequest
from intentinsight.domain.models.research_record import ResearchRecord
from intentinsight.infrastructure.github.models import RepositoryInfo


class RepositoryRepository:
    """Persist GitHub repository metadata in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, repository: RepositoryInfo) -> int:
        """Insert or update repository metadata."""

        mined_at = datetime.now(timezone.utc).isoformat()

        self._connection.execute(
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
            ON CONFLICT(full_name)
                DO UPDATE SET
                              owner = excluded.owner,
                              name = excluded.name,
                              default_branch = excluded.default_branch,
                              html_url = excluded.html_url,
                              mined_at = excluded.mined_at
            """,
            (
                repository.owner,
                repository.name,
                repository.full_name,
                repository.default_branch,
                repository.url,
                mined_at,
            ),
        )

        self._connection.commit()

        row = self._connection.execute(
            """
            SELECT id
            FROM repositories
            WHERE full_name = ?
            """,
            (repository.full_name,),
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "Repository was saved but its database ID "
                "could not be found."
            )

        return int(row["id"])

    def get_by_full_name(self, full_name: str) -> int | None:
        """Return the database ID for a repository."""

        row = self._connection.execute(
            """
            SELECT id
            FROM repositories
            WHERE full_name = ?
            """,
            (full_name,),
        ).fetchone()

        if row is None:
            return None

        return int(row["id"])


class PullRequestRepository:
    """Persist pull requests in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(
            self,
            repository_id: int,
            pull_request: PullRequest,
    ) -> int:
        """Insert or update a pull request."""

        cursor = self._connection.execute(
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
                base_sha,
                head_sha,
                commits_count,
                changed_files_count,
                additions,
                deletions
            )
            VALUES (
                       ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, ?, ?, ?
                   )
            ON CONFLICT(repository_id, number)
                DO UPDATE SET
                              title = excluded.title,
                              description = excluded.description,
                              author = excluded.author,
                              state = excluded.state,
                              created_at = excluded.created_at,
                              updated_at = excluded.updated_at,
                              merged_at = excluded.merged_at,
                              merge_commit_sha = excluded.merge_commit_sha,
                              base_sha = excluded.base_sha,
                              head_sha = excluded.head_sha,
                              commits_count = excluded.commits_count,
                              changed_files_count = excluded.changed_files_count,
                              additions = excluded.additions,
                              deletions = excluded.deletions
            """,
            (
                repository_id,
                pull_request.number,
                pull_request.title,
                pull_request.description,
                pull_request.author,
                pull_request.state,
                pull_request.created_at.isoformat(),
                pull_request.updated_at.isoformat(),
                (
                    pull_request.merged_at.isoformat()
                    if pull_request.merged_at
                    else None
                ),
                pull_request.merge_commit_sha,
                pull_request.base_sha,
                pull_request.head_sha,
                pull_request.commits_count,
                pull_request.changed_files_count,
                pull_request.additions,
                pull_request.deletions,
            ),
        )

        self._connection.commit()

        return cursor.lastrowid or 0

    def count(self) -> int:
        """Return the number of stored pull requests."""

        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM pull_requests
            """
        ).fetchone()

        return int(row["count"])


class ResearchRecordRepository:
    """Persist research dataset observations in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(
            self,
            repository_id: int,
            record: ResearchRecord,
    ) -> int:
        """Insert or update a research record."""

        collected_at = datetime.now(timezone.utc).isoformat()

        cursor = self._connection.execute(
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
            VALUES (
                       ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, ?, ?, ?
                   )
            ON CONFLICT(repository_id, pull_request_number)
                DO UPDATE SET
                              is_merged = excluded.is_merged,
                              merge_commit_sha = excluded.merge_commit_sha,
                              total_files = excluded.total_files,
                              source_file_count = excluded.source_file_count,
                              test_file_count = excluded.test_file_count,
                              documentation_file_count =
                                  excluded.documentation_file_count,
                              configuration_file_count =
                                  excluded.configuration_file_count,
                              other_file_count = excluded.other_file_count,
                              additions = excluded.additions,
                              deletions = excluded.deletions,
                              commits_count = excluded.commits_count,
                              eligible = excluded.eligible,
                              exclusion_reason = excluded.exclusion_reason,
                              collected_at = excluded.collected_at
            """,
            (
                repository_id,
                record.pull_request_number,
                int(record.is_merged),
                record.merge_commit_sha,
                record.total_files,
                record.source_file_count,
                record.test_file_count,
                record.documentation_file_count,
                record.configuration_file_count,
                record.other_file_count,
                record.additions,
                record.deletions,
                record.commits_count,
                int(record.eligible),
                record.exclusion_reason,
                collected_at,
            ),
        )

        self._connection.commit()

        return cursor.lastrowid or 0

    def exists(
            self,
            repository_id: int,
            pull_request_number: int,
    ) -> bool:
        """Return whether a research record already exists."""

        row = self._connection.execute(
            """
            SELECT 1
            FROM research_records
            WHERE repository_id = ?
              AND pull_request_number = ?
            LIMIT 1
            """,
            (
                repository_id,
                pull_request_number,
            ),
        ).fetchone()

        return row is not None

    def count(self) -> int:
        """Return the number of research records."""

        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM research_records
            """
        ).fetchone()

        return int(row["count"])

    def count_eligible(self) -> int:
        """Return the number of eligible research records."""

        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM research_records
            WHERE eligible = 1
            """
        ).fetchone()

        return int(row["count"])

    def count_excluded(self) -> int:
        """Return the number of excluded research records."""

        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM research_records
            WHERE eligible = 0
            """
        ).fetchone()

        return int(row["count"])


class CollectionRunRepository:
    """Persist research dataset collection runs."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(
            self,
            repository_id: int,
            *,
            started_at: datetime,
            completed_at: datetime,
            status: str,
            pull_requests_discovered: int,
            records_created: int,
            eligible_records: int,
            excluded_records: int,
    ) -> int:
        """Persist one collection run."""

        cursor = self._connection.execute(
            """
            INSERT INTO collection_runs (
                repository_id,
                started_at,
                completed_at,
                status,
                pull_requests_discovered,
                records_created,
                eligible_records,
                excluded_records
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repository_id,
                started_at.isoformat(),
                completed_at.isoformat(),
                status,
                pull_requests_discovered,
                records_created,
                eligible_records,
                excluded_records,
            ),
        )

        self._connection.commit()

        return cursor.lastrowid or 0

    def count(self) -> int:
        """Return the number of collection runs."""

        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM collection_runs
            """
        ).fetchone()

        return int(row["count"])