"""Compare current and historically reconstructed intent-impact divergence.

This is a READ-ONLY research experiment.

It:
- reads the existing database,
- reconstructs historical structural profiles in memory,
- creates historical structural embeddings in memory,
- compares them with the existing current structural embeddings,
- does not modify the database,
- does not overwrite existing embeddings,
- does not call GitHub.

The historical representation uses the same:
- IntentEncoder,
- 384-dimensional embedding space,
- log-scaled change weighting,
- weighted averaging,
- L2 normalization,
- cosine similarity,
- divergence = 1 - similarity

as the current structural representation.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from statistics import mean, median

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.domain.models.historical_impact import (
    HistoricalImpact,
    HistoricalImpactFile,
)
from intentinsight.domain.services.historical_impact_profile_builder import (
    build_historical_impact_profile,
)


DATABASE = "intentinsight.db"


@dataclass(frozen=True)
class Comparison:
    """Current versus historical divergence for one PR."""

    repository_id: int
    pull_request_number: int
    current_similarity: float
    current_divergence: float
    historical_similarity: float
    historical_divergence: float

    @property
    def divergence_difference(self) -> float:
        """Return historical divergence minus current divergence."""
        return (
                self.historical_divergence
                - self.current_divergence
        )


def cosine_similarity(
        left: list[float],
        right: list[float],
) -> float:
    """Calculate cosine similarity."""

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
        sum(value * value for value in left)
    )

    right_norm = math.sqrt(
        sum(value * value for value in right)
    )

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return dot / (left_norm * right_norm)


def build_historical_embedding(
        profile: object,
        encoder: IntentEncoder,
) -> list[float]:
    """Build a historical structural embedding in memory."""

    if not profile.modules:
        return [0.0] * 384

    module_texts = [
        module.module.replace(".", " ")
        for module in profile.modules
    ]

    embeddings = encoder.encode_many(
        module_texts,
    )

    if not embeddings:
        return [0.0] * 384

    # This is the same weighting formula used by
    # StructuralRepresentationBuilder.
    weights = [
        1.0 + math.log1p(
            max(module.changes, 0)
        )
        for module in profile.modules
    ]

    total_weight = sum(weights)

    if total_weight <= 0.0:
        return [0.0] * len(embeddings[0])

    dimension = len(embeddings[0])
    weighted = [0.0] * dimension

    for weight, embedding in zip(
            weights,
            embeddings,
            strict=True,
    ):
        normalized_weight = weight / total_weight

        for index, value in enumerate(embedding):
            weighted[index] += (
                    normalized_weight * value
            )

    # Same final L2 normalization as the current
    # structural representation.
    magnitude = math.sqrt(
        sum(value * value for value in weighted)
    )

    if magnitude == 0.0:
        return weighted

    return [
        value / magnitude
        for value in weighted
    ]


def build_historical_profile(
        connection: sqlite3.Connection,
        repository_id: int,
        pull_request_number: int,
) -> object:
    """Build a historical profile from validated file records."""

    rows = connection.execute(
        """
        SELECT
            filename,
            status,
            additions,
            deletions,
            changes,
            sha
        FROM pull_request_files
        WHERE repository_id = ?
          AND pull_request_number = ?
        ORDER BY id
        """,
        (
            repository_id,
            pull_request_number,
        ),
    ).fetchall()

    files = tuple(
        HistoricalImpactFile(
            filename=str(row["filename"]),
            status=str(row["status"]),
            additions=int(row["additions"] or 0),
            deletions=int(row["deletions"] or 0),
            changes=int(row["changes"] or 0),
            sha=str(row["sha"] or ""),
        )
        for row in rows
    )

    if not files:
        raise RuntimeError(
            f"No file records found for PR #{pull_request_number}."
        )

    anchor = connection.execute(
        """
        SELECT
            base_sha,
            head_sha
        FROM pull_requests
        WHERE repository_id = ?
          AND number = ?
        """,
        (
            repository_id,
            pull_request_number,
        ),
    ).fetchone()

    if anchor is None:
        raise RuntimeError(
            "Could not find PR anchor metadata "
            f"for PR #{pull_request_number}."
        )

    impact = HistoricalImpact(
        repository="",
        pull_request_number=pull_request_number,
        base_sha=str(anchor["base_sha"] or ""),
        head_sha=str(anchor["head_sha"] or ""),
        merge_base_sha=None,
        comparison_status="validated",
        ahead_by=0,
        behind_by=0,
        files=files,
    )

    return build_historical_impact_profile(
        impact,
    )


def percentile(
        values: list[float],
        fraction: float,
) -> float:
    """Calculate a linear-interpolated percentile."""

    ordered = sorted(values)

    if not ordered:
        return 0.0

    position = fraction * (len(ordered) - 1)

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    weight = position - lower

    return (
            ordered[lower] * (1.0 - weight)
            + ordered[upper] * weight
    )


def pearson_correlation(
        left: list[float],
        right: list[float],
) -> float:
    """Calculate Pearson correlation."""

    if len(left) != len(right):
        raise ValueError(
            "Correlation vectors have different lengths."
        )

    left_mean = mean(left)
    right_mean = mean(right)

    numerator = sum(
        (left_value - left_mean)
        * (right_value - right_mean)
        for left_value, right_value in zip(
            left,
            right,
            strict=True,
        )
    )

    left_denominator = math.sqrt(
        sum(
            (value - left_mean) ** 2
            for value in left
        )
    )

    right_denominator = math.sqrt(
        sum(
            (value - right_mean) ** 2
            for value in right
        )
    )

    if (
            left_denominator == 0.0
            or right_denominator == 0.0
    ):
        return 0.0

    return numerator / (
            left_denominator * right_denominator
    )


def main() -> None:
    """Run the read-only historical divergence experiment."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            rr.repository_id,
            rr.pull_request_number,
            intents.embedding_json AS intent_embedding,
            structures.embedding_json
                                   AS current_structural_embedding
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

        WHERE rr.eligible = 1

        ORDER BY
            rr.repository_id,
            rr.pull_request_number
        """
    ).fetchall()

    print("=" * 72)
    print("IntentInsight Historical Divergence Experiment")
    print("=" * 72)
    print()
    print("PRs analysed:", len(rows))
    print()
    print("READ-ONLY EXPERIMENT")
    print("No database records will be modified.")
    print("No existing embeddings will be overwritten.")
    print("No GitHub requests will be made.")

    encoder = IntentEncoder()

    comparisons: list[Comparison] = []

    for index, row in enumerate(rows, start=1):
        intent_embedding = json.loads(
            row["intent_embedding"]
        )

        current_embedding = json.loads(
            row["current_structural_embedding"]
        )

        if len(intent_embedding) != 384:
            raise RuntimeError(
                "Unexpected intent embedding dimension "
                f"for PR #{row['pull_request_number']}: "
                f"{len(intent_embedding)}"
            )

        if len(current_embedding) != 384:
            raise RuntimeError(
                "Unexpected current structural embedding "
                f"dimension for PR "
                f"#{row['pull_request_number']}: "
                f"{len(current_embedding)}"
            )

        historical_profile = build_historical_profile(
            connection,
            int(row["repository_id"]),
            int(row["pull_request_number"]),
        )

        historical_embedding = build_historical_embedding(
            historical_profile,
            encoder,
        )

        if len(historical_embedding) != 384:
            raise RuntimeError(
                "Unexpected historical embedding dimension "
                f"for PR #{row['pull_request_number']}: "
                f"{len(historical_embedding)}"
            )

        current_similarity = cosine_similarity(
            intent_embedding,
            current_embedding,
        )

        historical_similarity = cosine_similarity(
            intent_embedding,
            historical_embedding,
        )

        current_divergence = (
                1.0 - current_similarity
        )

        historical_divergence = (
                1.0 - historical_similarity
        )

        comparisons.append(
            Comparison(
                repository_id=int(
                    row["repository_id"]
                ),
                pull_request_number=int(
                    row["pull_request_number"]
                ),
                current_similarity=current_similarity,
                current_divergence=current_divergence,
                historical_similarity=(
                    historical_similarity
                ),
                historical_divergence=(
                    historical_divergence
                ),
            )
        )

        if index % 50 == 0:
            print(
                f"{index}/{len(rows)} PRs analysed"
            )

    connection.close()

    if not comparisons:
        raise RuntimeError(
            "No eligible PRs were available."
        )

    current_divergences = [
        item.current_divergence
        for item in comparisons
    ]

    historical_divergences = [
        item.historical_divergence
        for item in comparisons
    ]

    differences = [
        item.divergence_difference
        for item in comparisons
    ]

    # ------------------------------------------------------------
    # Current divergence
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("CURRENT DIVERGENCE")
    print("=" * 72)

    print(
        "Min:",
        f"{min(current_divergences):.6f}",
    )
    print(
        "Q1:",
        f"{percentile(current_divergences, 0.25):.6f}",
    )
    print(
        "Median:",
        f"{median(current_divergences):.6f}",
    )
    print(
        "Mean:",
        f"{mean(current_divergences):.6f}",
    )
    print(
        "Q3:",
        f"{percentile(current_divergences, 0.75):.6f}",
    )
    print(
        "Max:",
        f"{max(current_divergences):.6f}",
    )

    # ------------------------------------------------------------
    # Historical divergence
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("HISTORICAL DIVERGENCE")
    print("=" * 72)

    print(
        "Min:",
        f"{min(historical_divergences):.6f}",
    )
    print(
        "Q1:",
        f"{percentile(historical_divergences, 0.25):.6f}",
    )
    print(
        "Median:",
        f"{median(historical_divergences):.6f}",
    )
    print(
        "Mean:",
        f"{mean(historical_divergences):.6f}",
    )
    print(
        "Q3:",
        f"{percentile(historical_divergences, 0.75):.6f}",
    )
    print(
        "Max:",
        f"{max(historical_divergences):.6f}",
    )

    # ------------------------------------------------------------
    # Difference
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("HISTORICAL - CURRENT DIVERGENCE")
    print("=" * 72)

    print(
        "Min difference:",
        f"{min(differences):.6f}",
    )
    print(
        "Q1 difference:",
        f"{percentile(differences, 0.25):.6f}",
    )
    print(
        "Median difference:",
        f"{median(differences):.6f}",
    )
    print(
        "Mean difference:",
        f"{mean(differences):.6f}",
    )
    print(
        "Q3 difference:",
        f"{percentile(differences, 0.75):.6f}",
    )
    print(
        "Max difference:",
        f"{max(differences):.6f}",
    )

    identical = sum(
        math.isclose(
            value,
            0.0,
            abs_tol=1e-9,
        )
        for value in differences
    )

    historical_higher = sum(
        value > 0.0
        for value in differences
    )

    historical_lower = sum(
        value < 0.0
        for value in differences
    )

    total = len(differences)

    print()
    print(
        "Identical:",
        f"{identical} "
        f"({100 * identical / total:.2f}%)",
    )

    print(
        "Historical higher:",
        f"{historical_higher} "
        f"({100 * historical_higher / total:.2f}%)",
    )

    print(
        "Historical lower:",
        f"{historical_lower} "
        f"({100 * historical_lower / total:.2f}%)",
    )

    # ------------------------------------------------------------
    # Correlation
    # ------------------------------------------------------------

    correlation = pearson_correlation(
        current_divergences,
        historical_divergences,
    )

    print()
    print("=" * 72)
    print("CORRELATION")
    print("=" * 72)

    print(
        "Current vs historical divergence r =",
        f"{correlation:.6f}",
    )

    # ------------------------------------------------------------
    # Largest changes
    # ------------------------------------------------------------

    largest = sorted(
        comparisons,
        key=lambda item: item.divergence_difference,
        reverse=True,
    )

    print()
    print("=" * 72)
    print("LARGEST DIVERGENCE INCREASES")
    print("=" * 72)

    for item in largest[:15]:
        print(
            f"PR #{item.pull_request_number}: "
            f"current={item.current_divergence:.6f}, "
            f"historical={item.historical_divergence:.6f}, "
            f"delta={item.divergence_difference:+.6f}"
        )

    print()
    print("=" * 72)
    print("LARGEST DIVERGENCE DECREASES")
    print("=" * 72)

    for item in largest[-15:][::-1]:
        print(
            f"PR #{item.pull_request_number}: "
            f"current={item.current_divergence:.6f}, "
            f"historical={item.historical_divergence:.6f}, "
            f"delta={item.divergence_difference:+.6f}"
        )

    # ------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("EXPERIMENT COMPLETE")
    print("=" * 72)
    print()
    print("No database records were modified.")
    print("No existing embeddings were modified.")
    print("No GitHub requests were made.")


if __name__ == "__main__":
    main()