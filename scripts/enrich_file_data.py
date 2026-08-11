"""Enrich eligible research records with exact pull-request file data."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient
from intentinsight.infrastructure.github.exceptions import GitHubRateLimitError


DATABASE_PATH = Path("intentinsight.db")

PER_PAGE = 100


def utc_now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def ensure_tables(connection: sqlite3.Connection) -> None:
    """Create the enrichment tables if they do not already exist."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pull_request_files (
                                                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                          repository_id INTEGER NOT NULL,
                                                          pull_request_number INTEGER NOT NULL,

                                                          filename TEXT NOT NULL,
                                                          status TEXT NOT NULL,

                                                          additions INTEGER NOT NULL,
                                                          deletions INTEGER NOT NULL,
                                                          changes INTEGER NOT NULL,

                                                          sha TEXT NOT NULL,

                                                          collected_at TEXT NOT NULL,

                                                          UNIQUE(
                                                                 repository_id,
                                                                 pull_request_number,
                                                                 filename,
                                                                 sha
                                                              ),

                                                          FOREIGN KEY(repository_id, pull_request_number)
                                                              REFERENCES pull_requests(repository_id, number)
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pull_request_file_enrichment (
                                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                                                                    repository_id INTEGER NOT NULL,
                                                                    pull_request_number INTEGER NOT NULL,

                                                                    status TEXT NOT NULL,
                                                                    file_count INTEGER NOT NULL DEFAULT 0,

                                                                    error_message TEXT,

                                                                    started_at TEXT NOT NULL,
                                                                    completed_at TEXT,

                                                                    UNIQUE(repository_id, pull_request_number),

                                                                    FOREIGN KEY(repository_id, pull_request_number)
                                                                        REFERENCES pull_requests(repository_id, number)
        )
        """
    )

    connection.commit()


def get_eligible_pull_requests(
        connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """Return all eligible pull requests that need file enrichment."""

    rows = connection.execute(
        """
        SELECT
            pr.repository_id,
            pr.number,
            r.owner,
            r.name
        FROM pull_requests AS pr
                 INNER JOIN research_records AS rr
                            ON rr.repository_id = pr.repository_id
                                AND rr.pull_request_number = pr.number
                 INNER JOIN repositories AS r
                            ON r.id = pr.repository_id
                 LEFT JOIN pull_request_file_enrichment AS e
                           ON e.repository_id = pr.repository_id
                               AND e.pull_request_number = pr.number
        WHERE rr.eligible = 1
          AND (
            e.id IS NULL
                OR e.status != 'completed'
            )
        ORDER BY
            pr.repository_id,
            pr.number
        """
    ).fetchall()

    return rows


def save_enrichment_start(
        connection: sqlite3.Connection,
        repository_id: int,
        pull_request_number: int,
) -> None:
    """Record that enrichment has started."""

    now = utc_now()

    connection.execute(
        """
        INSERT INTO pull_request_file_enrichment (
            repository_id,
            pull_request_number,
            status,
            file_count,
            error_message,
            started_at,
            completed_at
        )
        VALUES (?, ?, 'running', 0, NULL, ?, NULL)
        ON CONFLICT(repository_id, pull_request_number)
            DO UPDATE SET
                          status = 'running',
                          file_count = 0,
                          error_message = NULL,
                          started_at = excluded.started_at,
                          completed_at = NULL
        """,
        (
            repository_id,
            pull_request_number,
            now,
        ),
    )

    connection.commit()


def save_file(
        connection: sqlite3.Connection,
        *,
        repository_id: int,
        pull_request_number: int,
        filename: str,
        status: str,
        additions: int,
        deletions: int,
        changes: int,
        sha: str,
) -> None:
    """Persist one changed-file record."""

    connection.execute(
        """
        INSERT OR IGNORE INTO pull_request_files (
            repository_id,
            pull_request_number,
            filename,
            status,
            additions,
            deletions,
            changes,
            sha,
            collected_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            repository_id,
            pull_request_number,
            filename,
            status,
            additions,
            deletions,
            changes,
            sha,
            utc_now(),
        ),
    )


def mark_completed(
        connection: sqlite3.Connection,
        repository_id: int,
        pull_request_number: int,
        file_count: int,
) -> None:
    """Mark one PR's file enrichment as successfully completed."""

    connection.execute(
        """
        UPDATE pull_request_file_enrichment
        SET
            status = 'completed',
            file_count = ?,
            error_message = NULL,
            completed_at = ?
        WHERE repository_id = ?
          AND pull_request_number = ?
        """,
        (
            file_count,
            utc_now(),
            repository_id,
            pull_request_number,
        ),
    )

    connection.commit()


def mark_failed(
        connection: sqlite3.Connection,
        repository_id: int,
        pull_request_number: int,
        error_message: str,
) -> None:
    """Mark one PR's enrichment as failed."""

    connection.execute(
        """
        UPDATE pull_request_file_enrichment
        SET
            status = 'failed',
            error_message = ?,
            completed_at = ?
        WHERE repository_id = ?
          AND pull_request_number = ?
        """,
        (
            error_message[:1000],
            utc_now(),
            repository_id,
            pull_request_number,
        ),
    )

    connection.commit()


def enrich_pull_request(
        connection: sqlite3.Connection,
        github_client: GitHubClient,
        *,
        repository_id: int,
        owner: str,
        repository: str,
        pull_request_number: int,
) -> int:
    """Fetch and persist all files changed by one pull request."""

    save_enrichment_start(
        connection,
        repository_id,
        pull_request_number,
    )

    page = 1
    total_files = 0

    while True:
        files = github_client.list_pull_request_files(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
            page=page,
            per_page=PER_PAGE,
        )

        if not files:
            break

        for file in files:
            save_file(
                connection,
                repository_id=repository_id,
                pull_request_number=pull_request_number,
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                sha=file.sha,
            )

            total_files += 1

        connection.commit()

        if len(files) < PER_PAGE:
            break

        page += 1

    mark_completed(
        connection,
        repository_id,
        pull_request_number,
        total_files,
    )

    return total_files


def main() -> None:
    """Run resumable PR-file enrichment."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH.resolve()}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        ensure_tables(connection)

        pull_requests = get_eligible_pull_requests(connection)

        total = len(pull_requests)

        print()
        print("=" * 64)
        print("IntentInsight PR File Enrichment")
        print("=" * 64)
        print()
        print(f"Eligible PRs needing enrichment: {total}")
        print()

        if total == 0:
            print("Nothing to enrich.")
            return

        settings = load_settings()

        completed = 0
        failed = 0
        files_stored = 0

        with GitHubClient(settings) as github_client:
            for index, pull_request in enumerate(
                    pull_requests,
                    start=1,
            ):
                repository_id = int(
                    pull_request["repository_id"]
                )
                pull_request_number = int(
                    pull_request["number"]
                )
                owner = str(pull_request["owner"])
                repository = str(pull_request["name"])

                print(
                    f"[{index}/{total}] "
                    f"{owner}/{repository}"
                    f"#{pull_request_number}",
                    end=" ... ",
                    flush=True,
                )

                try:
                    file_count = enrich_pull_request(
                        connection,
                        github_client,
                        repository_id=repository_id,
                        owner=owner,
                        repository=repository,
                        pull_request_number=pull_request_number,
                    )

                    completed += 1
                    files_stored += file_count

                    print(
                        f"OK ({file_count} files)"
                    )

                except GitHubRateLimitError:
                    print("RATE LIMIT")

                    print()
                    print(
                        "GitHub API rate limit reached."
                    )
                    print(
                        "Progress has been committed safely."
                    )
                    print(
                        "Run this script again after "
                        "the rate limit resets."
                    )
                    print()

                    return

                except Exception as exc:
                    failed += 1

                    mark_failed(
                        connection,
                        repository_id,
                        pull_request_number,
                        str(exc),
                    )

                    print(
                        f"FAILED: {exc}"
                    )

                # Small delay prevents unnecessary API pressure.
                time.sleep(0.05)

        print()
        print("=" * 64)
        print("ENRICHMENT SUMMARY")
        print("=" * 64)
        print()
        print(f"PRs processed:       {completed}")
        print(f"Files stored:        {files_stored}")
        print(f"Failed PRs:          {failed}")
        print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()