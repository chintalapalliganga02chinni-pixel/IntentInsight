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
                                                                          base_sha TEXT,
                                                                          head_sha TEXT,
                                                                          commits_count INTEGER NOT NULL,
                                                                          changed_files_count INTEGER NOT NULL,
                                                                          additions INTEGER NOT NULL,
                                                                          deletions INTEGER NOT NULL,

                                                                          UNIQUE(repository_id, number),

                                 FOREIGN KEY(repository_id)
                                 REFERENCES repositories(id)
                                 ); \
                             """


CREATE_RESEARCH_RECORDS_TABLE = """
                                CREATE TABLE IF NOT EXISTS research_records (
                                                                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                                repository_id INTEGER NOT NULL,
                                                                                pull_request_number INTEGER NOT NULL,

                                                                                is_merged INTEGER NOT NULL,
                                                                                merge_commit_sha TEXT,

                                                                                total_files INTEGER NOT NULL,
                                                                                source_file_count INTEGER NOT NULL,
                                                                                test_file_count INTEGER NOT NULL,
                                                                                documentation_file_count INTEGER NOT NULL,
                                                                                configuration_file_count INTEGER NOT NULL,
                                                                                other_file_count INTEGER NOT NULL,

                                                                                additions INTEGER NOT NULL,
                                                                                deletions INTEGER NOT NULL,
                                                                                commits_count INTEGER NOT NULL,

                                                                                eligible INTEGER NOT NULL,
                                                                                exclusion_reason TEXT,

                                                                                collected_at TEXT NOT NULL,

                                                                                UNIQUE(repository_id, pull_request_number),

                                    FOREIGN KEY(repository_id, pull_request_number)
                                    REFERENCES pull_requests(repository_id, number)
                                    ); \
                                """


CREATE_COLLECTION_RUNS_TABLE = """
                               CREATE TABLE IF NOT EXISTS collection_runs (
                                                                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                              repository_id INTEGER NOT NULL,

                                                                              started_at TEXT NOT NULL,
                                                                              completed_at TEXT NOT NULL,

                                                                              status TEXT NOT NULL,

                                                                              pull_requests_discovered INTEGER NOT NULL,
                                                                              records_created INTEGER NOT NULL,
                                                                              eligible_records INTEGER NOT NULL,
                                                                              excluded_records INTEGER NOT NULL,

                                                                              FOREIGN KEY(repository_id)
                                   REFERENCES repositories(id)
                                   ); \
                               """


CREATE_PULL_REQUEST_FILES_TABLE = """
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
                                      ); \
                                  """


CREATE_PULL_REQUEST_FILE_ENRICHMENT_TABLE = """
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
                                                ); \
                                            """


def create_schema(connection: sqlite3.Connection) -> None:
    """Create all required database tables."""

    connection.execute(CREATE_REPOSITORIES_TABLE)
    connection.execute(CREATE_PULL_REQUESTS_TABLE)
    connection.execute(CREATE_RESEARCH_RECORDS_TABLE)
    connection.execute(CREATE_COLLECTION_RUNS_TABLE)

    # The enrichment tables already exist in the current IntentInsight
    # database and are managed separately from the core schema.

    # SQLite does not modify an existing table when CREATE TABLE IF NOT EXISTS
    # is executed. Therefore, add the historical commit anchors explicitly.
    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(pull_requests)"
        ).fetchall()
    }

    if "base_sha" not in columns:
        connection.execute(
            "ALTER TABLE pull_requests ADD COLUMN base_sha TEXT"
        )

    if "head_sha" not in columns:
        connection.execute(
            "ALTER TABLE pull_requests ADD COLUMN head_sha TEXT"
        )

    connection.commit()