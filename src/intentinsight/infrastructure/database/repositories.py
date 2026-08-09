"""Database repositories for research entities."""

from __future__ import annotations

from datetime import datetime

import sqlite3

from intentinsight.domain.models import PullRequest


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
                commits_count,
                changed_files_count,
                additions,
                deletions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "SELECT COUNT(*) AS count FROM pull_requests"
        ).fetchone()

        return int(row["count"])