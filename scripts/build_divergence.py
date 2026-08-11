"""Build intent-impact divergence metrics for the dataset."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from intentinsight.analysis.divergence.divergence_schema import (
    ensure_divergence_schema,
)
from intentinsight.application.services.divergence_analysis_service import (
    DivergenceAnalysisService,
)


DATABASE_PATH = Path("intentinsight.db")


def main() -> None:
    """Build the divergence dataset."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH.resolve()}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )
    connection.row_factory = sqlite3.Row

    try:
        ensure_divergence_schema(
            connection
        )

        intent_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_request_intents
            """
        ).fetchone()[0]

        structural_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_request_structures
            """
        ).fetchone()[0]

        existing_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM intent_impact_divergence
            """
        ).fetchone()[0]

        joinable_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pull_request_intents AS intents
            INNER JOIN pull_request_structures AS structures
                ON structures.repository_id =
                    intents.repository_id
                AND structures.pull_request_number =
                    intents.pull_request_number
            """
        ).fetchone()[0]

        print()
        print("=" * 64)
        print("IntentInsight Intent–Impact Divergence")
        print("=" * 64)
        print()
        print(
            f"Intent records:          {intent_count}"
        )
        print(
            f"Structural records:      {structural_count}"
        )
        print(
            f"Joinable PRs:             {joinable_count}"
        )
        print(
            f"Existing divergence:     {existing_count}"
        )
        print()

        if joinable_count == 0:
            raise RuntimeError(
                "No PRs have both intent and structural representations."
            )

        service = DivergenceAnalysisService()

        created = service.analyze(
            connection
        )

        final_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM intent_impact_divergence
            """
        ).fetchone()[0]

        print()
        print("=" * 64)
        print("DIVERGENCE SUMMARY")
        print("=" * 64)
        print()
        print(
            f"Records created:         {created}"
        )
        print(
            f"Total divergence records:{final_count}"
        )
        print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()