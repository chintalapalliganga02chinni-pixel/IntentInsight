"""Build structural representations for eligible pull requests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.structural.structural_schema import (
    ensure_structural_schema,
)
from intentinsight.application.services.structural_analysis_service import (
    StructuralAnalysisService,
)


DATABASE_PATH = Path("intentinsight.db")


def main() -> None:
    """Generate structural representations."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH.resolve()}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        ensure_structural_schema(connection)

        eligible_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM research_records
            WHERE eligible = 1
            """
        ).fetchone()[0]

        existing_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_request_structures
            """
        ).fetchone()[0]

        print()
        print("=" * 64)
        print("IntentInsight Structural Analysis")
        print("=" * 64)
        print()
        print(f"Eligible PRs:             {eligible_count}")
        print(f"Existing structures:      {existing_count}")
        print()

        if existing_count >= eligible_count:
            print(
                "All eligible PRs already have structural representations."
            )
            return

        print("Loading semantic embedding model...")
        print()

        encoder = IntentEncoder()

        service = StructuralAnalysisService(
            encoder=encoder,
        )

        created = service.analyze_repository(
            connection,
        )

        final_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_request_structures
            """
        ).fetchone()[0]

        total_modules = connection.execute(
            """
            SELECT COALESCE(SUM(module_count), 0)
            FROM pull_request_structures
            """
        ).fetchone()[0]

        total_files = connection.execute(
            """
            SELECT COALESCE(SUM(changed_file_count), 0)
            FROM pull_request_structures
            """
        ).fetchone()[0]

        print()
        print("=" * 64)
        print("STRUCTURAL REPRESENTATION SUMMARY")
        print("=" * 64)
        print()
        print(f"Records created:         {created}")
        print(f"Total structures:        {final_count}")
        print(f"Module instances:        {total_modules}")
        print(f"Changed files represented:{total_files}")
        print(
            "Embedding model:         "
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()