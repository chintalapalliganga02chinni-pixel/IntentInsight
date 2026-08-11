"""Statistical comparison of structural representation ablations."""

from __future__ import annotations

import json
import random
import sqlite3
import statistics

from sentence_transformers import SentenceTransformer

from intentinsight.analysis.divergence.divergence_analysis import (
    cosine_similarity,
    parse_embedding,
)


DATABASE = "intentinsight.db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BOOTSTRAPS = 5000
PERMUTATIONS = 1000
SEED = 42


def module_only_text(module_profile_json: str) -> str:
    """Build a module-name-only representation."""

    profile = json.loads(module_profile_json)

    modules = [
        str(item["module"])
        for item in profile
        if isinstance(item, dict) and item.get("module")
    ]

    if not modules:
        return "Changed modules: none"

    return "Changed modules:\n" + "\n".join(
        f"- {module}"
        for module in modules
    )


def similarities(
    intents: list[list[float]],
    structures: list[list[float]],
) -> list[float]:
    """Calculate per-PR cosine similarities."""

    return [
        cosine_similarity(intent, structure)
        for intent, structure in zip(
            intents,
            structures,
            strict=True,
        )
    ]


def bootstrap_mean_difference(
    first: list[float],
    second: list[float],
    repetitions: int,
    seed: int,
) -> tuple[float, float, float]:
    """
    Bootstrap the mean paired difference.

    Returns:
        observed difference,
        lower 95% percentile,
        upper 95% percentile.
    """

    if len(first) != len(second):
        raise ValueError("Input vectors must have equal length.")

    paired = [
        left - right
        for left, right in zip(
            first,
            second,
            strict=True,
        )
    ]

    observed = statistics.mean(paired)

    rng = random.Random(seed)

    bootstrap_means: list[float] = []

    for _ in range(repetitions):
        sample = [
            paired[rng.randrange(len(paired))]
            for _ in paired
        ]

        bootstrap_means.append(
            statistics.mean(sample)
        )

    bootstrap_means.sort()

    lower_index = int(
        0.025 * repetitions
    )

    upper_index = int(
        0.975 * repetitions
    )

    upper_index = min(
        upper_index,
        repetitions - 1,
    )

    return (
        observed,
        bootstrap_means[lower_index],
        bootstrap_means[upper_index],
    )


def null_mean_distribution(
    intents: list[list[float]],
    structures: list[list[float]],
    permutations: int,
    seed: int,
) -> list[float]:
    """Generate null-model means by random pairing."""

    rng = random.Random(seed)

    indices = list(range(len(structures)))

    results: list[float] = []

    for _ in range(permutations):
        shuffled = indices.copy()
        rng.shuffle(shuffled)

        shuffled_structures = [
            structures[index]
            for index in shuffled
        ]

        results.append(
            statistics.mean(
                similarities(
                    intents,
                    shuffled_structures,
                )
            )
        )

    return results


def main() -> None:
    """Run statistical ablation analysis."""

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT
                intents.embedding_json AS intent_embedding,
                structures.embedding_json AS structural_embedding,
                structures.module_profile_json
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
    finally:
        connection.close()

    if not rows:
        raise RuntimeError("No matching records found.")

    intents = [
        parse_embedding(row["intent_embedding"])
        for row in rows
    ]

    full_structures = [
        parse_embedding(row["structural_embedding"])
        for row in rows
    ]

    print()
    print("=" * 64)
    print("STRUCTURAL ABLATION STATISTICAL ANALYSIS")
    print("=" * 64)
    print()

    print(f"PRs analysed: {len(rows)}")
    print(f"Bootstrap repetitions: {BOOTSTRAPS}")
    print(f"Null permutations: {PERMUTATIONS}")
    print()

    model = SentenceTransformer(
        MODEL_NAME
    )

    module_texts = [
        module_only_text(
            row["module_profile_json"]
        )
        for row in rows
    ]

    module_vectors = model.encode(
        module_texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    module_structures = [
        vector.tolist()
        for vector in module_vectors
    ]

    full_actual = similarities(
        intents,
        full_structures,
    )

    module_actual = similarities(
        intents,
        module_structures,
    )

    full_observed = statistics.mean(
        full_actual
    )

    module_observed = statistics.mean(
        module_actual
    )

    print("OBSERVED SIMILARITY")
    print("-------------------")
    print(
        f"Full:         {full_observed:.6f}"
    )
    print(
        f"Module-only:  {module_observed:.6f}"
    )
    print(
        f"Full - module: "
        f"{full_observed - module_observed:.6f}"
    )
    print()

    (
        observed_difference,
        lower,
        upper,
    ) = bootstrap_mean_difference(
        full_actual,
        module_actual,
        BOOTSTRAPS,
        SEED,
    )

    print("PAIRED BOOTSTRAP")
    print("----------------")
    print(
        f"Mean per-PR difference: "
        f"{observed_difference:.6f}"
    )
    print(
        f"95% bootstrap interval: "
        f"[{lower:.6f}, {upper:.6f}]"
    )
    print()

    print("GENERATING NULL DISTRIBUTIONS")
    print("-----------------------------")

    full_null = null_mean_distribution(
        intents,
        full_structures,
        PERMUTATIONS,
        SEED,
    )

    module_null = null_mean_distribution(
        intents,
        module_structures,
        PERMUTATIONS,
        SEED,
    )

    full_null_mean = statistics.mean(
        full_null
    )

    module_null_mean = statistics.mean(
        module_null
    )

    full_effect = (
        full_observed
        - full_null_mean
    )

    module_effect = (
        module_observed
        - module_null_mean
    )

    effect_difference = (
        full_effect
        - module_effect
    )

    print()
    print("OBSERVED-VS-NULL EFFECT")
    print("-----------------------")
    print(
        f"Full observed:          "
        f"{full_observed:.6f}"
    )
    print(
        f"Full null mean:         "
        f"{full_null_mean:.6f}"
    )
    print(
        f"Full effect:            "
        f"{full_effect:.6f}"
    )
    print()

    print(
        f"Module-only observed:   "
        f"{module_observed:.6f}"
    )
    print(
        f"Module-only null mean:  "
        f"{module_null_mean:.6f}"
    )
    print(
        f"Module-only effect:     "
        f"{module_effect:.6f}"
    )
    print()

    print(
        f"Difference in effects:  "
        f"{effect_difference:.6f}"
    )
    print()

    print("INTERPRETATION")
    print("--------------")
    print(
        "Positive values mean the full representation "
        "has stronger PR-specific separation than "
        "the module-only representation."
    )
    print(
        "The bootstrap interval is for the raw "
        "per-PR similarity difference; the effect "
        "comparison above is descriptive."
    )
    print()


if __name__ == "__main__":
    main()