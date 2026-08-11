"""Database schema for structural pull-request representations."""

from __future__ import annotations

import sqlite3


CREATE_PULL_REQUEST_STRUCTURES_TABLE = """
CREATE TABLE IF NOT EXISTS pull_request_structures (
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

    UNIQUE(repository_id, pull_request_number),

    FOREIGN KEY(repository_id, pull_request_number)
        REFERENCES pull_requests(repository_id, number)
);
"""


def ensure_structural_schema(
    connection: sqlite3.Connection,
) -> None:
    """Create the structural representation table."""

    connection.execute(CREATE_PULL_REQUEST_STRUCTURES_TABLE)
    connection.commit()