"""Ablation study for the structural representation."""

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


def module_only_text(module_profile_json: str) -> str:
    """Create a representation containing module identities only."""

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


def mean_similarity(
    intents: list[list[float]],
    structures: list[list[float]],
) -> float:
    """Calculate mean cosine similarity."""

    values = [
        cosine_similarity(intent, structure)
        for intent, structure in zip(
            intents,
            structures,
            strict=True,
        )
    ]

    return statistics.mean(values)


def null_distribution(
    intents: list[list[float]],
    structures: list[list[float]],
    permutations: int = 1000,
) -> list[float]:
    """Generate a random-pairing null distribution."""

    rng = random.Random(42)

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
            mean_similarity(
                intents,
                shuffled_structures,
            )
        )

    return results


def print_result(
    name: str,
    observed: float,
    null_values: list[float],
) -> None:
    """Print observed-vs-null results."""

    null_mean = statistics.mean(null_values)

    print(name)
    print("-" * len(name))

    print(
        f"Observed similarity:    {observed:.6f}"
    )

    print(
        f"Random similarity:      {null_mean:.6f}"
    )

    print(
        f"Observed - random:      "
        f"{observed - null_mean:.6f}"
    )

    greater_or_equal = sum(
        value >= observed
        for value in null_values
    )

    p_value = (
        greater_or_equal + 1
    ) / (
        len(null_values) + 1
    )

    print(
        f"Permutation p-value:    {p_value:.4f}"
    )

    print()


def main() -> None:
    """Run the structural representation ablation."""

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
        raise RuntimeError(
            "No matching PR records found."
        )

    intents = [
        parse_embedding(row["intent_embedding"])
        for row in rows
    ]

    current_structures = [
        parse_embedding(row["structural_embedding"])
        for row in rows
    ]

    print()
    print("=" * 64)
    print("INTENTINSIGHT STRUCTURAL REPRESENTATION ABLATION")
    print("=" * 64)
    print()

    print(
        f"PRs analysed: {len(rows)}"
    )

    print(
        "Loading embedding model..."
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    module_texts = [
        module_only_text(
            row["module_profile_json"]
        )
        for row in rows
    ]

    print(
        "Encoding module-only representations..."
    )

    module_embeddings = model.encode(
        module_texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    module_only_structures = [
        vector.tolist()
        for vector in module_embeddings
    ]

    print()

    current_observed = mean_similarity(
        intents,
        current_structures,
    )

    module_only_observed = mean_similarity(
        intents,
        module_only_structures,
    )

    print("RESULTS")
    print("=======")
    print()

    print(
        f"Current structural observed: "
        f"{current_observed:.6f}"
    )

    print(
        f"Module-only observed:         "
        f"{module_only_observed:.6f}"
    )

    print()

    current_null = null_distribution(
        intents,
        current_structures,
    )

    module_null = null_distribution(
        intents,
        module_only_structures,
    )

    print_result(
        "CURRENT STRUCTURAL REPRESENTATION",
        current_observed,
        current_null,
    )

    print_result(
        "MODULE-ONLY REPRESENTATION",
        module_only_observed,
        module_null,
    )

    print(
        "DIRECT COMPARISON"
    )
    print(
        "-----------------"
    )

    difference = (
        current_observed
        - module_only_observed
    )

    print(
        f"Full - module-only:     "
        f"{difference:.6f}"
    )

    print()

    print(
        "Interpretation should be based on the "
        "relative results above; no threshold is "
        "assumed in advance."
    )

    print()

    
if __name__ == "__main__":
    main()