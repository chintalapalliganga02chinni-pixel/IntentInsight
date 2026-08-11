"""Database schema for semantic pull-request intent."""

from __future__ import annotations

import sqlite3


CREATE_PULL_REQUEST_INTENTS_TABLE = """
                                    CREATE TABLE IF NOT EXISTS pull_request_intents (
                                                                                        id INTEGER PRIMARY KEY AUTOINCREMENT,

                                                                                        repository_id INTEGER NOT NULL,
                                                                                        pull_request_number INTEGER NOT NULL,

                                                                                        title TEXT NOT NULL,
                                                                                        description TEXT NOT NULL,
                                                                                        combined_text TEXT NOT NULL,

                                                                                        model_name TEXT NOT NULL,
                                                                                        model_version TEXT NOT NULL,

                                                                                        embedding_dimension INTEGER NOT NULL,
                                                                                        embedding_json TEXT NOT NULL,

                                                                                        created_at TEXT NOT NULL,

                                                                                        UNIQUE(repository_id, pull_request_number),

                                        FOREIGN KEY(repository_id, pull_request_number)
                                        REFERENCES pull_requests(repository_id, number)
                                        ); \
                                    """


def ensure_intent_schema(
        connection: sqlite3.Connection,
) -> None:
    """Create the semantic intent table if it does not already exist."""

    connection.execute(CREATE_PULL_REQUEST_INTENTS_TABLE)
    connection.commit()