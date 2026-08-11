"""Audit the existing intent-impact divergence baseline."""

from __future__ import annotations

import json
import math
import sqlite3
from statistics import mean, median


DATABASE = "intentinsight.db"


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(left) != len(right):
        raise ValueError(
            "Embedding dimensions do not match."
        )

    dot = sum(
        left_value * right_value
        for left_value, right_value in zip(
            left,
            right,
            strict=True,
        )
    )

    left_norm = math.sqrt(
        sum(
            value * value
            for value in left
        )
    )

    right_norm = math.sqrt(
        sum(
            value * value
            for value in right
        )
    )

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot / (
        left_norm * right_norm
    )


def main() -> None:
    """Audit stored intent and structural embeddings."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            rr.repository_id,
            rr.pull_request_number,
            intents.embedding_json AS intent_embedding,
            structures.embedding_json
                AS structural_embedding,
            divergence.intent_similarity
                AS stored_similarity,
            divergence.intent_impact_divergence
                AS stored_divergence,
            divergence.module_count,
            divergence.changed_file_count,
            divergence.module_entropy,
            divergence.module_concentration,
            divergence.top_module_weight,
            divergence.package_count,
            divergence.cross_package_spread,
            divergence.total_additions,
            divergence.total_deletions,
            divergence.total_changes
        FROM research_records AS rr

        INNER JOIN pull_request_intents AS intents
            ON intents.repository_id =
                rr.repository_id
            AND intents.pull_request_number =
                rr.pull_request_number

        INNER JOIN pull_request_structures AS structures
            ON structures.repository_id =
                rr.repository_id
            AND structures.pull_request_number =
                rr.pull_request_number

        LEFT JOIN intent_impact_divergence AS divergence
            ON divergence.repository_id =
                rr.repository_id
            AND divergence.pull_request_number =
                rr.pull_request_number

        WHERE rr.eligible = 1

        ORDER BY
            rr.repository_id,
            rr.pull_request_number
        """
    ).fetchall()

    print("=" * 72)
    print("IntentInsight Baseline Divergence Audit")
    print("=" * 72)

    print()
    print(
        "Eligible PRs with intent + structure:",
        len(rows),
    )

    similarities: list[float] = []
    divergences: list[float] = []

    stored_similarity_mismatches = 0
    stored_divergence_mismatches = 0

    missing_divergence_records = 0

    dimensions: set[int] = set()

    for row in rows:
        intent_embedding = json.loads(
            row["intent_embedding"]
        )

        structural_embedding = json.loads(
            row["structural_embedding"]
        )

        intent_dimension = len(
            intent_embedding
        )

        structural_dimension = len(
            structural_embedding
        )

        dimensions.add(
            intent_dimension
        )
        dimensions.add(
            structural_dimension
        )

        similarity = cosine_similarity(
            intent_embedding,
            structural_embedding,
        )

        divergence = 1.0 - similarity

        similarities.append(similarity)
        divergences.append(divergence)

        if row["stored_similarity"] is None:
            missing_divergence_records += 1
        else:
            if not math.isclose(
                similarity,
                float(
                    row["stored_similarity"]
                ),
                rel_tol=1e-9,
                abs_tol=1e-9,
            ):
                stored_similarity_mismatches += 1

        if row["stored_divergence"] is not None:
            if not math.isclose(
                divergence,
                float(
                    row["stored_divergence"]
                ),
                rel_tol=1e-9,
                abs_tol=1e-9,
            ):
                stored_divergence_mismatches += 1

    print()
    print("=" * 72)
    print("EMBEDDING DIMENSIONS")
    print("=" * 72)

    print()

    for dimension in sorted(dimensions):
        print(
            "Dimension:",
            dimension,
        )

    print()
    print("=" * 72)
    print("INTENT / STRUCTURE SIMILARITY")
    print("=" * 72)

    print()
    print(
        "Min:",
        f"{min(similarities):.6f}",
    )

    print(
        "Q1:",
        f"{percentile(similarities, 0.25):.6f}",
    )

    print(
        "Median:",
        f"{median(similarities):.6f}",
    )

    print(
        "Mean:",
        f"{mean(similarities):.6f}",
    )

    print(
        "Q3:",
        f"{percentile(similarities, 0.75):.6f}",
    )

    print(
        "Max:",
        f"{max(similarities):.6f}",
    )

    print()
    print("=" * 72)
    print("INTENT / STRUCTURE DIVERGENCE")
    print("=" * 72)

    print()
    print(
        "Min:",
        f"{min(divergences):.6f}",
    )

    print(
        "Q1:",
        f"{percentile(divergences, 0.25):.6f}",
    )

    print(
        "Median:",
        f"{median(divergences):.6f}",
    )

    print(
        "Mean:",
        f"{mean(divergences):.6f}",
    )

    print(
        "Q3:",
        f"{percentile(divergences, 0.75):.6f}",
    )

    print(
        "Max:",
        f"{max(divergences):.6f}",
    )

    print()
    print("=" * 72)
    print("STORED DIVERGENCE VALIDATION")
    print("=" * 72)

    print()
    print(
        "Missing divergence records:",
        missing_divergence_records,
    )

    print(
        "Similarity mismatches:",
        stored_similarity_mismatches,
    )

    print(
        "Divergence mismatches:",
        stored_divergence_mismatches,
    )

    print()
    print("=" * 72)
    print("AUDIT COMPLETE")
    print("=" * 72)

    print()
    print(
        "No database records were modified."
    )


def percentile(
    values: list[float],
    fraction: float,
) -> float:
    """Calculate a linear-interpolated percentile."""
    if not values:
        return 0.0

    ordered = sorted(values)

    position = (
        fraction
        * (len(ordered) - 1)
    )

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    weight = position - lower

    return (
        ordered[lower]
        * (1.0 - weight)
        + ordered[upper]
        * weight
    )


if __name__ == "__main__":
    main()