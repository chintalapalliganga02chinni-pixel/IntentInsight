"""SQLite database connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class DatabaseConnection:
    """Manage SQLite database connections."""

    def __init__(self, database_path: str) -> None:
        self._database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        """Create a SQLite connection."""
        self._database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row

        return connection