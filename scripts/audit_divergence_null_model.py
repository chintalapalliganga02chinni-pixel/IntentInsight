"""Compare observed intent-impact similarity against random pairings."""

from __future__ import annotations

import random
import sqlite3
import statistics

from intentinsight.analysis.divergence.divergence_analysis import (
    cosine_similarity,
    parse_embedding,
)


DATABASE = "intentinsight.db"


def mean_similarity(
    intents: list[list[float]],
    structures: list[list[float]],
) -> float:
    """Calculate mean pairwise cosine similarity."""

    similarities = [
        cosine_similarity(intent, structure)
        for intent, structure in zip(
            intents,
            structures,
            strict=True,
        )
    ]

    return statistics.mean(similarities)


def main() -> None:
    """Run the observed-vs-random pairing experiment."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT
                intents.repository_id,
                intents.pull_request_number,
                intents.embedding_json AS intent_embedding,
                structures.embedding_json AS structural_embedding
            FROM pull_request_intents AS intents
            INNER JOIN pull_request_structures AS structures
                ON structures.repository_id =
                    intents.repository_id
                AND structures.pull_request_number =
                    intents.pull_request_number
            ORDER BY
                intents.repository_id,
                intents.pull_request_number
            """
        ).fetchall()

        if not rows:
            raise RuntimeError(
                "No matching intent/structural records found."
            )

        intents = [
            parse_embedding(row["intent_embedding"])
            for row in rows
        ]

        structures = [
            parse_embedding(row["structural_embedding"])
            for row in rows
        ]

        observed = mean_similarity(
            intents,
            structures,
        )

        rng = random.Random(42)

        permutation_means: list[float] = []

        permutation_count = 1000

        structure_indices = list(
            range(len(structures))
        )

        for _ in range(permutation_count):
            shuffled_indices = structure_indices.copy()

            rng.shuffle(shuffled_indices)

            shuffled_structures = [
                structures[index]
                for index in shuffled_indices
            ]

            permutation_means.append(
                mean_similarity(
                    intents,
                    shuffled_structures,
                )
            )

        null_mean = statistics.mean(
            permutation_means
        )

        null_std = statistics.stdev(
            permutation_means
        )

        null_q025 = sorted(
            permutation_means
        )[int(0.025 * permutation_count)]

        null_q975 = sorted(
            permutation_means
        )[int(0.975 * permutation_count)]

        greater_or_equal = sum(
            value >= observed
            for value in permutation_means
        )

        p_value = (
            greater_or_equal + 1
        ) / (
            permutation_count + 1
        )

        effect = (
            observed - null_mean
        )

        standardized_effect = (
            effect / null_std
            if null_std > 0
            else 0.0
        )

        print()
        print("=" * 64)
        print("INTENT–IMPACT NULL MODEL")
        print("=" * 64)
        print()

        print(
            f"PRs analysed:             {len(rows)}"
        )

        print(
            f"Permutations:             {permutation_count}"
        )

        print()

        print("OBSERVED")
        print("--------")
        print(
            f"Mean cosine similarity:   {observed:.6f}"
        )

        print()

        print("RANDOM PAIRING NULL MODEL")
        print("-------------------------")
        print(
            f"Mean similarity:          {null_mean:.6f}"
        )
        print(
            f"Std deviation:            {null_std:.6f}"
        )
        print(
            f"2.5th percentile:          {null_q025:.6f}"
        )
        print(
            f"97.5th percentile:         {null_q975:.6f}"
        )

        print()

        print("EFFECT")
        print("------")
        print(
            f"Observed - random:        {effect:.6f}"
        )
        print(
            f"Standardized effect:      {standardized_effect:.4f}"
        )
        print(
            f"Permutation p-value:      {p_value:.4f}"
        )

        print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()