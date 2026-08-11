"""Database schema for intent-impact divergence analysis."""

from __future__ import annotations

import sqlite3


CREATE_INTENT_IMPACT_DIVERGENCE_TABLE = """
CREATE TABLE IF NOT EXISTS intent_impact_divergence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    repository_id INTEGER NOT NULL,
    pull_request_number INTEGER NOT NULL,

    intent_similarity REAL NOT NULL,
    intent_impact_divergence REAL NOT NULL,

    module_count INTEGER NOT NULL,
    changed_file_count INTEGER NOT NULL,

    module_entropy REAL NOT NULL,
    module_concentration REAL NOT NULL,
    top_module_weight REAL NOT NULL,

    package_count INTEGER NOT NULL,
    cross_package_spread INTEGER NOT NULL,

    total_additions INTEGER NOT NULL,
    total_deletions INTEGER NOT NULL,
    total_changes INTEGER NOT NULL,

    modified_file_count INTEGER NOT NULL,
    added_file_count INTEGER NOT NULL,
    removed_file_count INTEGER NOT NULL,
    renamed_file_count INTEGER NOT NULL,

    created_at TEXT NOT NULL,

    UNIQUE(repository_id, pull_request_number),

    FOREIGN KEY(repository_id, pull_request_number)
        REFERENCES pull_requests(repository_id, number)
);
"""


def ensure_divergence_schema(
    connection: sqlite3.Connection,
) -> None:
    """Create the intent-impact divergence table."""

    connection.execute(
        CREATE_INTENT_IMPACT_DIVERGENCE_TABLE
    )
    connection.commit()