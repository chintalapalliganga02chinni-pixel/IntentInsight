"""Build semantic intent representations for eligible pull requests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.intent.intent_schema import ensure_intent_schema
from intentinsight.application.services.intent_analysis_service import (
    IntentAnalysisService,
)


DATABASE_PATH = Path("intentinsight.db")


def main() -> None:
    """Generate semantic intent representations."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH.resolve()}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        ensure_intent_schema(connection)

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
            FROM pull_request_intents
            """
        ).fetchone()[0]

        print()
        print("=" * 64)
        print("IntentInsight Semantic Intent Analysis")
        print("=" * 64)
        print()
        print(f"Eligible PRs:             {eligible_count}")
        print(f"Existing intent records:  {existing_count}")
        print()

        if existing_count >= eligible_count:
            print(
                "All eligible PRs already have semantic representations."
            )
            return

        print("Loading semantic embedding model...")
        print()

        encoder = IntentEncoder()

        service = IntentAnalysisService(
            encoder=encoder,
        )

        created = service.analyze_repository(
            connection,
        )

        final_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_request_intents
            """
        ).fetchone()[0]

        print()
        print("=" * 64)
        print("SEMANTIC INTENT SUMMARY")
        print("=" * 64)
        print()
        print(f"Records created:         {created}")
        print(f"Total intent records:    {final_count}")
        print(f"Embedding model:         {encoder.model_name}")
        print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()