"""SQLite database schema."""

from __future__ import annotations

import sqlite3


CREATE_REPOSITORIES_TABLE = """
                            CREATE TABLE IF NOT EXISTS repositories (
                                                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                        owner TEXT NOT NULL,
                                                                        name TEXT NOT NULL,
                                                                        full_name TEXT NOT NULL UNIQUE,
                                                                        default_branch TEXT NOT NULL,
                                                                        html_url TEXT,
                                                                        mined_at TEXT NOT NULL
                            ); \
                            """


CREATE_PULL_REQUESTS_TABLE = """
                             CREATE TABLE IF NOT EXISTS pull_requests (
                                                                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                          repository_id INTEGER NOT NULL,
                                                                          number INTEGER NOT NULL,
                                                                          title TEXT NOT NULL,
                                                                          description TEXT NOT NULL,
                                                                          author TEXT NOT NULL,
                                                                          state TEXT NOT NULL,
                                                                          created_at TEXT NOT NULL,
                                                                          updated_at TEXT NOT NULL,
                                                                          merged_at TEXT,
                                                                          merge_commit_sha TEXT,
                                                                          commits_count INTEGER NOT NULL,
                                                                          changed_files_count INTEGER NOT NULL,
                                                                          additions INTEGER NOT NULL,
                                                                          deletions INTEGER NOT NULL,

                                                                          UNIQUE(repository_id, number),

                                 FOREIGN KEY(repository_id)
                                 REFERENCES repositories(id)
                                 ); \
                             """


def create_schema(connection: sqlite3.Connection) -> None:
    """Create all required database tables."""
    connection.execute(CREATE_REPOSITORIES_TABLE)
    connection.execute(CREATE_PULL_REQUESTS_TABLE)
    connection.commit()