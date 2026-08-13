"""IntentInsight structural-scope ablation experiment.

This is a READ-ONLY experiment.

It compares two structural representations for the same 703 eligible PRs:

A. CURRENT FULL
   All changed files are converted into structural modules.

B. PYTHON-ONLY
   The same persisted changed-file records are restricted to .py/.pyi
   files before structural representation.

The intent embeddings and existing current structural embeddings are read
from the database. The Python-only structural embeddings are generated
in memory only.

No database records are modified.
No existing embeddings are overwritten.
No GitHub requests are made.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from statistics import mean, median

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.structural.module_path import (
    filename_to_module,
)


DATABASE = "intentinsight.db"
EMBEDDING_DIMENSION = 384


@dataclass(frozen=True)
class Result:
    """Full versus Python-only divergence for one PR."""

    repository_id: int
    pull_request_number: int

    full_similarity: float
    full_divergence: float

    python_similarity: float
    python_divergence: float

    @property
    def difference(self) -> float:
        """Return Python-only minus full divergence."""

        return (
            self.python_divergence
            - self.full_divergence
        )


def is_python_file(filename: str) -> bool:
    """Return whether a repository file is Python source."""

    normalized = filename.replace("\\", "/")

    return normalized.endswith(
        (".py", ".pyi")
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

    return dot / (
        left_norm * right_norm
    )


def build_python_only_embedding(
    rows: list[sqlite3.Row],
    encoder: IntentEncoder,
) -> list[float]:
    """Build the Python-only structural embedding in memory."""

    module_data: dict[
        str,
        dict[str, object],
    ] = {}

    for row in rows:
        filename = str(
            row["filename"]
        )

        if not is_python_file(filename):
            continue

        module = filename_to_module(
            filename
        )

        if module not in module_data:
            module_data[module] = {
                "changes": 0,
            }

        module_data[module]["changes"] = (
            int(module_data[module]["changes"])
            + int(row["changes"] or 0)
        )

    if not module_data:
        return [
            0.0
        ] * EMBEDDING_DIMENSION

    modules = sorted(module_data)

    module_texts = [
        module.replace(".", " ")
        for module in modules
    ]

    embeddings = encoder.encode_many(
        module_texts
    )

    if not embeddings:
        return [
            0.0
        ] * EMBEDDING_DIMENSION

    weights = [
        1.0
        + math.log1p(
            max(
                int(
                    module_data[module][
                        "changes"
                    ]
                ),
                0,
            )
        )
        for module in modules
    ]

    total_weight = sum(weights)

    if total_weight <= 0.0:
        return [
            0.0
        ] * len(embeddings[0])

    dimension = len(embeddings[0])

    weighted = [
        0.0
    ] * dimension

    for weight, embedding in zip(
        weights,
        embeddings,
        strict=True,
    ):
        normalized_weight = (
            weight / total_weight
        )

        for index, value in enumerate(
            embedding
        ):
            weighted[index] += (
                normalized_weight * value
            )

    magnitude = math.sqrt(
        sum(
            value * value
            for value in weighted
        )
    )

    if magnitude == 0.0:
        return weighted

    return [
        value / magnitude
        for value in weighted
    ]


def percentile(
    values: list[float],
    fraction: float,
) -> float:
    """Return a linearly interpolated percentile."""

    ordered = sorted(values)

    if not ordered:
        return 0.0

    position = (
        fraction
        * (len(ordered) - 1)
    )

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    weight = (
        position - lower
    )

    return (
        ordered[lower]
        * (1.0 - weight)
        + ordered[upper]
        * weight
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
        (
            left_value
            - left_mean
        )
        * (
            right_value
            - right_mean
        )
        for left_value, right_value in zip(
            left,
            right,
            strict=True,
        )
    )

    left_denominator = math.sqrt(
        sum(
            (
                value
                - left_mean
            ) ** 2
            for value in left
        )
    )

    right_denominator = math.sqrt(
        sum(
            (
                value
                - right_mean
            ) ** 2
            for value in right
        )
    )

    if (
        left_denominator == 0.0
        or right_denominator == 0.0
    ):
        return 0.0

    return (
        numerator
        / (
            left_denominator
            * right_denominator
        )
    )


def rank_values(
    values: list[float],
) -> list[float]:
    """Assign average ranks, handling ties."""

    indexed = sorted(
        enumerate(values),
        key=lambda item: item[1],
    )

    ranks = [
        0.0
    ] * len(values)

    index = 0

    while index < len(indexed):
        end = index + 1

        while (
            end < len(indexed)
            and indexed[end][1]
            == indexed[index][1]
        ):
            end += 1

        average_rank = (
            (index + 1)
            + end
        ) / 2.0

        for position in range(
            index,
            end,
        ):
            original_index = (
                indexed[position][0]
            )

            ranks[original_index] = (
                average_rank
            )

        index = end

    return ranks


def spearman_correlation(
    left: list[float],
    right: list[float],
) -> float:
    """Calculate Spearman rank correlation."""

    return pearson_correlation(
        rank_values(left),
        rank_values(right),
    )


def wilcoxon_signed_rank(
    differences: list[float],
) -> tuple[float, float]:
    """Calculate a two-sided Wilcoxon signed-rank statistic.

    The p-value uses the normal approximation with continuity correction.
    Zero differences are discarded.
    """

    non_zero = [
        difference
        for difference in differences
        if not math.isclose(
            difference,
            0.0,
            abs_tol=1e-12,
        )
    ]

    if not non_zero:
        return 0.0, 1.0

    absolute_values = [
        abs(value)
        for value in non_zero
    ]

    ranks = rank_values(
        absolute_values
    )

    positive_rank_sum = sum(
        rank
        for rank, value in zip(
            ranks,
            non_zero,
            strict=True,
        )
        if value > 0
    )

    negative_rank_sum = sum(
        rank
        for rank, value in zip(
            ranks,
            non_zero,
            strict=True,
        )
        if value < 0
    )

    statistic = min(
        positive_rank_sum,
        negative_rank_sum,
    )

    n = len(non_zero)

    mean_w = (
        n * (n + 1)
    ) / 4.0

    variance_w = (
        n
        * (n + 1)
        * (2 * n + 1)
    ) / 24.0

    if variance_w <= 0.0:
        return statistic, 1.0

    continuity = 0.5

    z = (
        statistic
        - mean_w
        + continuity
    ) / math.sqrt(variance_w)

    # Two-sided normal approximation.
    p_value = math.erfc(
        abs(z)
        / math.sqrt(2.0)
    )

    return statistic, p_value


def bootstrap_mean_difference(
    differences: list[float],
    iterations: int = 10000,
    seed: int = 20260811,
) -> tuple[float, float, float]:
    """Return mean and percentile bootstrap 95% CI."""

    import random

    if not differences:
        return 0.0, 0.0, 0.0

    rng = random.Random(seed)

    sample_size = len(
        differences
    )

    bootstrap_means: list[float] = []

    for _ in range(iterations):
        sample = [
            differences[
                rng.randrange(
                    sample_size
                )
            ]
            for _ in range(sample_size)
        ]

        bootstrap_means.append(
            mean(sample)
        )

    return (
        mean(differences),
        percentile(
            bootstrap_means,
            0.025,
        ),
        percentile(
            bootstrap_means,
            0.975,
        ),
    )


def main() -> None:
    """Run the structural-scope ablation."""

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = (
        sqlite3.Row
    )

    rows = connection.execute(
        """
        SELECT
            rr.repository_id,
            rr.pull_request_number,
            intents.embedding_json
                AS intent_embedding,
            structures.embedding_json
                AS full_structural_embedding
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

    print()
    print("=" * 72)
    print("IntentInsight Structural-Scope Ablation")
    print("=" * 72)
    print()

    print(
        "PRs analysed:",
        len(rows),
    )

    if len(rows) != 703:
        raise RuntimeError(
            f"Expected 703 eligible PRs, "
            f"found {len(rows)}."
        )

    print()
    print("READ-ONLY EXPERIMENT")
    print(
        "No database records will be modified."
    )
    print(
        "No existing embeddings will be overwritten."
    )
    print(
        "No GitHub requests will be made."
    )

    encoder = IntentEncoder()

    results: list[Result] = []

    for index, row in enumerate(
        rows,
        start=1,
    ):
        intent_embedding = json.loads(
            row["intent_embedding"]
        )

        full_embedding = json.loads(
            row[
                "full_structural_embedding"
            ]
        )

        if len(intent_embedding) != (
            EMBEDDING_DIMENSION
        ):
            raise RuntimeError(
                "Unexpected intent embedding "
                f"dimension for PR "
                f"#{row['pull_request_number']}: "
                f"{len(intent_embedding)}"
            )

        if len(full_embedding) != (
            EMBEDDING_DIMENSION
        ):
            raise RuntimeError(
                "Unexpected full structural "
                f"embedding dimension for PR "
                f"#{row['pull_request_number']}: "
                f"{len(full_embedding)}"
            )

        file_rows = connection.execute(
            """
            SELECT
                filename,
                additions,
                deletions,
                changes,
                status
            FROM pull_request_files
            WHERE repository_id = ?
              AND pull_request_number = ?
            ORDER BY id
            """,
            (
                int(
                    row["repository_id"]
                ),
                int(
                    row[
                        "pull_request_number"
                    ]
                ),
            ),
        ).fetchall()

        python_embedding = (
            build_python_only_embedding(
                file_rows,
                encoder,
            )
        )

        full_similarity = (
            cosine_similarity(
                intent_embedding,
                full_embedding,
            )
        )

        python_similarity = (
            cosine_similarity(
                intent_embedding,
                python_embedding,
            )
        )

        full_divergence = (
            1.0
            - full_similarity
        )

        python_divergence = (
            1.0
            - python_similarity
        )

        results.append(
            Result(
                repository_id=int(
                    row["repository_id"]
                ),
                pull_request_number=int(
                    row[
                        "pull_request_number"
                    ]
                ),
                full_similarity=(
                    full_similarity
                ),
                full_divergence=(
                    full_divergence
                ),
                python_similarity=(
                    python_similarity
                ),
                python_divergence=(
                    python_divergence
                ),
            )
        )

        if index % 50 == 0:
            print(
                f"{index}/{len(rows)} PRs analysed"
            )

    connection.close()

    full_divergences = [
        result.full_divergence
        for result in results
    ]

    python_divergences = [
        result.python_divergence
        for result in results
    ]

    differences = [
        result.difference
        for result in results
    ]

    # ------------------------------------------------------------
    # Full representation
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("CURRENT FULL DIVERGENCE")
    print("=" * 72)

    print(
        "Min:",
        f"{min(full_divergences):.6f}",
    )

    print(
        "Q1:",
        f"{percentile(full_divergences, 0.25):.6f}",
    )

    print(
        "Median:",
        f"{median(full_divergences):.6f}",
    )

    print(
        "Mean:",
        f"{mean(full_divergences):.6f}",
    )

    print(
        "Q3:",
        f"{percentile(full_divergences, 0.75):.6f}",
    )

    print(
        "Max:",
        f"{max(full_divergences):.6f}",
    )

    # ------------------------------------------------------------
    # Python-only representation
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("PYTHON-ONLY DIVERGENCE")
    print("=" * 72)

    print(
        "Min:",
        f"{min(python_divergences):.6f}",
    )

    print(
        "Q1:",
        f"{percentile(python_divergences, 0.25):.6f}",
    )

    print(
        "Median:",
        f"{median(python_divergences):.6f}",
    )

    print(
        "Mean:",
        f"{mean(python_divergences):.6f}",
    )

    print(
        "Q3:",
        f"{percentile(python_divergences, 0.75):.6f}",
    )

    print(
        "Max:",
        f"{max(python_divergences):.6f}",
    )

    # ------------------------------------------------------------
    # Paired differences
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("PYTHON-ONLY - CURRENT FULL")
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
            difference,
            0.0,
            abs_tol=1e-9,
        )
        for difference in differences
    )

    python_higher = sum(
        difference > 0.0
        for difference in differences
    )

    full_higher = sum(
        difference < 0.0
        for difference in differences
    )

    print()

    print(
        "Identical:",
        f"{identical} "
        f"({100 * identical / len(results):.2f}%)",
    )

    print(
        "Python-only higher:",
        f"{python_higher} "
        f"({100 * python_higher / len(results):.2f}%)",
    )

    print(
        "Current full higher:",
        f"{full_higher} "
        f"({100 * full_higher / len(results):.2f}%)",
    )

    # ------------------------------------------------------------
    # Correlation
    # ------------------------------------------------------------

    pearson = pearson_correlation(
        full_divergences,
        python_divergences,
    )

    spearman = spearman_correlation(
        full_divergences,
        python_divergences,
    )

    print()
    print("=" * 72)
    print("CORRELATION")
    print("=" * 72)

    print(
        "Pearson r:",
        f"{pearson:.6f}",
    )

    print(
        "Spearman rho:",
        f"{spearman:.6f}",
    )

    # ------------------------------------------------------------
    # Wilcoxon
    # ------------------------------------------------------------

    statistic, p_value = (
        wilcoxon_signed_rank(
            differences
        )
    )

    print()
    print("=" * 72)
    print("WILCOXON SIGNED-RANK TEST")
    print("=" * 72)

    print(
        "Statistic:",
        f"{statistic:.6f}",
    )

    print(
        "Approximate two-sided p-value:",
        f"{p_value:.10f}",
    )

    # ------------------------------------------------------------
    # Effect size
    # ------------------------------------------------------------

    non_zero = [
        difference
        for difference in differences
        if not math.isclose(
            difference,
            0.0,
            abs_tol=1e-12,
        )
    ]

    if non_zero:
        effect_size = (
            mean(non_zero)
            / math.sqrt(
                mean(
                    (
                        value
                        - mean(non_zero)
                    ) ** 2
                    for value in non_zero
                )
            )
            if len(non_zero) > 1
            else 0.0
        )
    else:
        effect_size = 0.0

    print()
    print("=" * 72)
    print("EFFECT SIZE")
    print("=" * 72)

    print(
        "Standardised mean difference "
        "(non-zero paired differences):",
        f"{effect_size:.6f}",
    )

    # ------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------

    bootstrap_mean, ci_low, ci_high = (
        bootstrap_mean_difference(
            differences
        )
    )

    print()
    print("=" * 72)
    print("BOOTSTRAP 95% CI")
    print("=" * 72)

    print(
        "Mean difference:",
        f"{bootstrap_mean:.6f}",
    )

    print(
        "95% CI lower:",
        f"{ci_low:.6f}",
    )

    print(
        "95% CI upper:",
        f"{ci_high:.6f}",
    )

    # ------------------------------------------------------------
    # Absolute differences
    # ------------------------------------------------------------

    absolute_differences = [
        abs(value)
        for value in differences
    ]

    print()
    print("=" * 72)
    print("ABSOLUTE DIVERGENCE CHANGE")
    print("=" * 72)

    print(
        "Mean absolute difference:",
        f"{mean(absolute_differences):.6f}",
    )

    print(
        "Median absolute difference:",
        f"{median(absolute_differences):.6f}",
    )

    print(
        "Max absolute difference:",
        f"{max(absolute_differences):.6f}",
    )

    print(
        "Changed by > 0.01:",
        sum(
            value > 0.01
            for value in absolute_differences
        ),
    )

    print(
        "Changed by > 0.05:",
        sum(
            value > 0.05
            for value in absolute_differences
        ),
    )

    print(
        "Changed by > 0.10:",
        sum(
            value > 0.10
            for value in absolute_differences
        ),
    )

    # ------------------------------------------------------------
    # Largest changes
    # ------------------------------------------------------------

    ordered = sorted(
        results,
        key=lambda result: result.difference,
        reverse=True,
    )

    print()
    print("=" * 72)
    print("LARGEST PYTHON-ONLY INCREASES")
    print("=" * 72)

    for result in ordered[:15]:
        print(
            f"PR #{result.pull_request_number}: "
            f"full={result.full_divergence:.6f}, "
            f"python={result.python_divergence:.6f}, "
            f"delta={result.difference:+.6f}"
        )

    print()
    print("=" * 72)
    print("LARGEST PYTHON-ONLY DECREASES")
    print("=" * 72)

    for result in ordered[-15:][::-1]:
        print(
            f"PR #{result.pull_request_number}: "
            f"full={result.full_divergence:.6f}, "
            f"python={result.python_divergence:.6f}, "
            f"delta={result.difference:+.6f}"
        )

    print()
    print("=" * 72)
    print("EXPERIMENT COMPLETE")
    print("=" * 72)
    print()
    print(
        "No database records were modified."
    )
    print(
        "No existing embeddings were modified."
    )
    print(
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()