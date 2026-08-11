"""Backfill historical GitHub commit anchors for existing pull requests."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.database.connection import DatabaseConnection
from intentinsight.infrastructure.database.schema import create_schema
from intentinsight.infrastructure.github.client import GitHubClient
from intentinsight.infrastructure.github.exceptions import (
    GitHubRateLimitError,
)


DATABASE_PATH = PROJECT_ROOT / "intentinsight.db"
PER_PAGE = 100


def main() -> None:
    """Backfill base/head commit SHAs without rebuilding the dataset."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    settings = load_settings()
    database = DatabaseConnection(str(DATABASE_PATH))

    total_seen = 0
    matched = 0
    updated = 0
    missing_anchor = 0
    unmatched = 0

    with GitHubClient(settings) as github_client:
        with database.connect() as connection:
            create_schema(connection)

            repositories = connection.execute(
                """
                SELECT id, owner, name, full_name
                FROM repositories
                ORDER BY id
                """
            ).fetchall()

            if not repositories:
                raise RuntimeError(
                    "No repositories exist in the database."
                )

            print()
            print("=" * 64)
            print("IntentInsight PR Anchor Backfill")
            print("=" * 64)
            print()
            print(f"Repositories: {len(repositories)}")
            print(f"Database:     {DATABASE_PATH}")
            print()

            for repository in repositories:
                repository_id = int(repository["id"])
                owner = str(repository["owner"])
                name = str(repository["name"])
                full_name = str(repository["full_name"])

                print(f"Processing {full_name} ...")

                page = 1

                while True:
                    pull_requests = (
                        github_client.list_pull_requests(
                            owner=owner,
                            repository=name,
                            state="all",
                            page=page,
                            per_page=PER_PAGE,
                        )
                    )

                    if not pull_requests:
                        break

                    for data in pull_requests:
                        total_seen += 1

                        number = int(data["number"])

                        base = data.get("base") or {}
                        head = data.get("head") or {}

                        base_sha = base.get("sha")
                        head_sha = head.get("sha")

                        if not base_sha or not head_sha:
                            missing_anchor += 1
                            continue

                        row = connection.execute(
                            """
                            SELECT id
                            FROM pull_requests
                            WHERE repository_id = ?
                              AND number = ?
                            """,
                            (
                                repository_id,
                                number,
                            ),
                        ).fetchone()

                        if row is None:
                            unmatched += 1

                            print(
                                f"  UNMATCHED GitHub PR: "
                                f"#{number} - "
                                f"{data.get('title') or ''}"
                            )

                            continue

                        matched += 1

                        connection.execute(
                            """
                            UPDATE pull_requests
                            SET
                                base_sha = ?,
                                head_sha = ?
                            WHERE repository_id = ?
                              AND number = ?
                            """,
                            (
                                str(base_sha),
                                str(head_sha),
                                repository_id,
                                number,
                            ),
                        )

                        updated += 1

                    connection.commit()

                    print(
                        f"  page {page}: "
                        f"{len(pull_requests)} PRs processed"
                    )

                    if len(pull_requests) < PER_PAGE:
                        break

                    page += 1

                print()

    print("=" * 64)
    print("ANCHOR BACKFILL SUMMARY")
    print("=" * 64)
    print()
    print(f"GitHub PRs seen:        {total_seen}")
    print(f"Database PRs matched:   {matched}")
    print(f"Rows updated:            {updated}")
    print(f"Missing anchors:         {missing_anchor}")
    print(f"Unmatched database PRs:  {unmatched}")
    print()

    with sqlite3.connect(DATABASE_PATH) as connection:
        total_database_prs = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_requests
            """
        ).fetchone()[0]

        base_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_requests
            WHERE base_sha IS NOT NULL
              AND base_sha != ''
            """
        ).fetchone()[0]

        head_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_requests
            WHERE head_sha IS NOT NULL
              AND head_sha != ''
            """
        ).fetchone()[0]

    print(f"Database PRs total:     {total_database_prs}")
    print(f"Base SHA populated:     {base_count}")
    print(f"Head SHA populated:     {head_count}")
    print()

    if total_database_prs == matched:
        print("All database PRs matched to GitHub PR metadata.")
    else:
        print(
            "WARNING: GitHub/database PR counts do not completely match."
        )

    if (
            base_count == total_database_prs
            and head_count == total_database_prs
    ):
        print("Historical base/head anchor coverage: 100%.")
    else:
        print(
            "WARNING: Not every database PR has both historical anchors."
        )

    print()


if __name__ == "__main__":
    try:
        main()
    except GitHubRateLimitError:
        print()
        print("GitHub API rate limit reached.")
        print("Completed pages were already committed.")
        print("Run the script again after the rate limit resets.")
        raise SystemExit(2)