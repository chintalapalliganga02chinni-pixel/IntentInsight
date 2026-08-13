"""
IntentInsight Structural Random-Control Experiment

READ-ONLY.

Question:
Does the Python-only structural representation preserve more
PR-intent similarity than a size-matched random selection of files?

Important implementation detail:
Module embeddings are encoded ONCE and cached. Random controls are
then calculated using the cached vectors, so the experiment does not
repeatedly call the SentenceTransformer model.

No database modifications.
No GitHub requests.
"""

from __future__ import annotations

import csv
import json
import math
import sqlite3
from pathlib import Path

import numpy as np

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.structural.module_path import (
    filename_to_module,
)


DB_PATH = "intentinsight.db"
OUTPUT_PATH = Path(
    "structural_random_control_analysis.csv"
)

RANDOM_SEED = 20260811
RANDOM_ITERATIONS = 1000


def is_python(filename: str) -> bool:
    """Return whether a filename is Python source."""

    value = filename.replace("\\", "/").lower()

    return value.endswith(
        (".py", ".pyi")
    )


def normalize_vector(
        vector: np.ndarray,
) -> np.ndarray:
    """L2-normalize a vector."""

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm


def cosine(
        first: np.ndarray,
        second: np.ndarray,
) -> float:
    """Calculate cosine similarity."""

    denominator = (
            np.linalg.norm(first)
            * np.linalg.norm(second)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(first, second)
        / denominator
    )


def build_module_embedding_cache(
        connection: sqlite3.Connection,
        encoder: IntentEncoder,
) -> dict[str, np.ndarray]:
    """
    Find every structural module used by the dataset and encode each
    unique module exactly once.
    """

    rows = connection.execute(
        """
        SELECT DISTINCT filename
        FROM pull_request_files
        ORDER BY filename
        """
    ).fetchall()

    modules = sorted(
        {
            filename_to_module(
                str(row["filename"])
            )
            for row in rows
        }
    )

    print(
        f"Unique structural modules: "
        f"{len(modules)}"
    )

    if not modules:
        raise RuntimeError(
            "No structural modules found."
        )

    texts = [
        module.replace(".", " ")
        for module in modules
    ]

    print(
        "Encoding unique modules once..."
    )

    embeddings = encoder.encode_many(
        texts
    )

    cache: dict[
        str,
        np.ndarray,
    ] = {}

    for module, embedding in zip(
            modules,
            embeddings,
            strict=True,
    ):
        cache[module] = normalize_vector(
            np.asarray(
                embedding,
                dtype=float,
            )
        )

    print(
        f"Cached embeddings: "
        f"{len(cache)}"
    )

    return cache


def structural_embedding_from_rows(
        rows: list[sqlite3.Row],
        module_cache: dict[str, np.ndarray],
) -> np.ndarray:
    """
    Build the structural embedding from already-cached module vectors.

    The weighting matches the current structural representation:

        weight = 1 + log1p(changes)

    Files belonging to the same module are aggregated first.
    """

    module_changes: dict[
        str,
        int,
    ] = {}

    for row in rows:
        module = filename_to_module(
            str(row["filename"])
        )

        changes = int(
            row["changes"] or 0
        )

        module_changes[module] = (
                module_changes.get(
                    module,
                    0,
                )
                + changes
        )

    if not module_changes:
        dimension = len(
            next(iter(
                module_cache.values()
            ))
        )

        return np.zeros(
            dimension,
            dtype=float,
        )

    first_embedding = next(
        iter(
            module_cache.values()
        )
    )

    result = np.zeros(
        len(first_embedding),
        dtype=float,
    )

    total_weight = 0.0

    for module, changes in (
            module_changes.items()
    ):
        if module not in module_cache:
            raise RuntimeError(
                f"Missing cached module: "
                f"{module}"
            )

        weight = (
                1.0
                + math.log1p(
            max(changes, 0)
        )
        )

        result += (
                weight
                * module_cache[module]
        )

        total_weight += weight

    if total_weight <= 0:
        return result

    result /= total_weight

    return normalize_vector(
        result
    )


def structural_embedding_from_indices(
        files: list[sqlite3.Row],
        indices: np.ndarray,
        module_cache: dict[str, np.ndarray],
) -> np.ndarray:
    """
    Build a structural embedding from sampled file indices.

    Uses cached module vectors; no model calls occur here.
    """

    module_changes: dict[
        str,
        int,
    ] = {}

    for index in indices:
        row = files[int(index)]

        module = filename_to_module(
            str(row["filename"])
        )

        changes = int(
            row["changes"] or 0
        )

        module_changes[module] = (
                module_changes.get(
                    module,
                    0,
                )
                + changes
        )

    first_embedding = next(
        iter(
            module_cache.values()
        )
    )

    result = np.zeros(
        len(first_embedding),
        dtype=float,
    )

    total_weight = 0.0

    for module, changes in (
            module_changes.items()
    ):
        weight = (
                1.0
                + math.log1p(
            max(changes, 0)
        )
        )

        result += (
                weight
                * module_cache[module]
        )

        total_weight += weight

    if total_weight <= 0:
        return result

    result /= total_weight

    return normalize_vector(
        result
    )


def percentile(
        values: list[float],
        q: float,
) -> float:
    """Return a percentile."""

    return float(
        np.percentile(
            np.asarray(
                values,
                dtype=float,
            ),
            q,
        )
    )


def main() -> None:
    print("=" * 72)
    print(
        "IntentInsight Structural Random-Control Experiment"
    )
    print("=" * 72)
    print()

    print("READ-ONLY")
    print(
        "No database records will be modified."
    )
    print(
        "No GitHub requests will be made."
    )
    print()

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    prs = connection.execute(
        """
        SELECT
            rr.repository_id,
            rr.pull_request_number
        FROM research_records AS rr
                 JOIN pull_request_intents AS intents
                      ON intents.repository_id =
                         rr.repository_id
                          AND intents.pull_request_number =
                              rr.pull_request_number
        WHERE rr.eligible = 1
        ORDER BY
            rr.repository_id,
            rr.pull_request_number
        """
    ).fetchall()

    if len(prs) != 703:
        connection.close()

        raise RuntimeError(
            f"Expected 703 eligible PRs, "
            f"found {len(prs)}."
        )

    print(
        f"PRs analysed: {len(prs)}"
    )

    print(
        f"Random iterations per PR: "
        f"{RANDOM_ITERATIONS}"
    )

    print()

    encoder = IntentEncoder()

    module_cache = (
        build_module_embedding_cache(
            connection,
            encoder,
        )
    )

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    output_rows: list[
        dict[str, object]
    ] = []

    all_python_similarity: list[
        float
    ] = []

    all_random_mean_similarity: list[
        float
    ] = []

    all_random_best_similarity: list[
        float
    ] = []

    all_differences: list[
        float
    ] = []

    for position, pr in enumerate(
            prs,
            start=1,
    ):
        repository_id = int(
            pr["repository_id"]
        )

        pull_request_number = int(
            pr["pull_request_number"]
        )

        intent_row = connection.execute(
            """
            SELECT embedding_json
            FROM pull_request_intents
            WHERE repository_id = ?
              AND pull_request_number = ?
            """,
            (
                repository_id,
                pull_request_number,
            ),
        ).fetchone()

        if intent_row is None:
            connection.close()

            raise RuntimeError(
                f"Missing intent for "
                f"PR #{pull_request_number}"
            )

        intent = np.asarray(
            json.loads(
                intent_row[
                    "embedding_json"
                ]
            ),
            dtype=float,
        )

        files = connection.execute(
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

        if not files:
            connection.close()

            raise RuntimeError(
                f"No files for "
                f"PR #{pull_request_number}"
            )

        python_files = [
            row
            for row in files
            if is_python(
                str(row["filename"])
            )
        ]

        if not python_files:
            connection.close()

            raise RuntimeError(
                f"No Python files for "
                f"PR #{pull_request_number}"
            )

        python_count = len(
            python_files
        )

        non_python_count = (
                len(files)
                - python_count
        )

        # ----------------------------------------------------------
        # Python-only structural representation
        # ----------------------------------------------------------

        python_embedding = (
            structural_embedding_from_rows(
                python_files,
                module_cache,
            )
        )

        python_similarity = cosine(
            intent,
            python_embedding,
        )

        # ----------------------------------------------------------
        # Random control
        # ----------------------------------------------------------

        random_similarities: list[
            float
        ] = []

        all_indices = np.arange(
            len(files)
        )

        for _ in range(
                RANDOM_ITERATIONS
        ):
            sampled_indices = rng.choice(
                all_indices,
                size=python_count,
                replace=False,
            )

            random_embedding = (
                structural_embedding_from_indices(
                    files,
                    sampled_indices,
                    module_cache,
                )
            )

            random_similarity = cosine(
                intent,
                random_embedding,
            )

            random_similarities.append(
                random_similarity
            )

        random_mean = float(
            np.mean(
                random_similarities
            )
        )

        random_median = float(
            np.median(
                random_similarities
            )
        )

        random_p05 = percentile(
            random_similarities,
            5,
        )

        random_p95 = percentile(
            random_similarities,
            95,
        )

        random_best = float(
            np.max(
                random_similarities
            )
        )

        difference = (
                python_similarity
                - random_mean
        )

        probability_random_beats_python = (
            float(
                np.mean(
                    np.asarray(
                        random_similarities
                    )
                    >= python_similarity
                )
            )
        )

        all_python_similarity.append(
            python_similarity
        )

        all_random_mean_similarity.append(
            random_mean
        )

        all_random_best_similarity.append(
            random_best
        )

        all_differences.append(
            difference
        )

        output_rows.append(
            {
                "repository_id":
                    repository_id,
                "pull_request_number":
                    pull_request_number,
                "total_files":
                    len(files),
                "python_file_count":
                    python_count,
                "non_python_file_count":
                    non_python_count,
                "python_similarity":
                    python_similarity,
                "random_mean_similarity":
                    random_mean,
                "random_median_similarity":
                    random_median,
                "random_p05_similarity":
                    random_p05,
                "random_p95_similarity":
                    random_p95,
                "random_best_similarity":
                    random_best,
                "python_minus_random_mean":
                    difference,
                "random_probability_beats_python":
                    probability_random_beats_python,
            }
        )

        if position % 25 == 0:
            print(
                f"{position}/{len(prs)} "
                "PRs processed"
            )

    connection.close()

    # --------------------------------------------------------------
    # Overall results
    # --------------------------------------------------------------

    python_values = np.asarray(
        all_python_similarity,
        dtype=float,
    )

    random_values = np.asarray(
        all_random_mean_similarity,
        dtype=float,
    )

    best_random_values = np.asarray(
        all_random_best_similarity,
        dtype=float,
    )

    differences = np.asarray(
        all_differences,
        dtype=float,
    )

    python_better = int(
        np.sum(
            differences > 0
        )
    )

    random_better = int(
        np.sum(
            differences < 0
        )
    )

    identical = int(
        np.sum(
            np.isclose(
                differences,
                0.0,
            )
        )
    )

    print()
    print("=" * 72)
    print(
        "PYTHON-ONLY VS RANDOM CONTROL"
    )
    print("=" * 72)
    print()

    print(
        f"Mean Python similarity: "
        f"{python_values.mean():.6f}"
    )

    print(
        f"Mean random similarity: "
        f"{random_values.mean():.6f}"
    )

    print(
        f"Mean Python - random: "
        f"{differences.mean():+.6f}"
    )

    print(
        f"Median Python - random: "
        f"{np.median(differences):+.6f}"
    )

    print(
        f"Python higher: "
        f"{python_better}"
    )

    print(
        f"Random higher: "
        f"{random_better}"
    )

    print(
        f"Identical: "
        f"{identical}"
    )

    print(
        f"Mean random BEST similarity: "
        f"{best_random_values.mean():.6f}"
    )

    # --------------------------------------------------------------
    # PRs containing non-Python files
    # --------------------------------------------------------------

    informative_mask = np.array(
        [
            int(
                row[
                    "non_python_file_count"
                ]
            ) > 0
            for row in output_rows
        ],
        dtype=bool,
    )

    informative_python = (
        python_values[
            informative_mask
        ]
    )

    informative_random = (
        random_values[
            informative_mask
        ]
    )

    informative_difference = (
        differences[
            informative_mask
        ]
    )

    print()
    print("=" * 72)
    print(
        "PRs WITH NON-PYTHON FILES"
    )
    print("=" * 72)
    print()

    print(
        f"n: "
        f"{len(informative_difference)}"
    )

    print(
        f"Mean Python similarity: "
        f"{informative_python.mean():.6f}"
    )

    print(
        f"Mean random similarity: "
        f"{informative_random.mean():.6f}"
    )

    print(
        f"Mean difference: "
        f"{informative_difference.mean():+.6f}"
    )

    print(
        f"Median difference: "
        f"{np.median(informative_difference):+.6f}"
    )

    print(
        f"Python higher: "
        f"{int(np.sum(informative_difference > 0))}"
    )

    print(
        f"Random higher: "
        f"{int(np.sum(informative_difference < 0))}"
    )

    print(
        f"Identical: "
        f"{int(np.sum(np.isclose(informative_difference, 0.0)))}"
    )

    # --------------------------------------------------------------
    # Save results
    # --------------------------------------------------------------

    fields = list(
        output_rows[0].keys()
    )

    with OUTPUT_PATH.open(
            "w",
            newline="",
            encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(
            output_rows
        )

    print()
    print("=" * 72)
    print("OUTPUT")
    print("=" * 72)
    print()

    print(
        f"Rows written: "
        f"{len(output_rows)}"
    )

    print(
        f"Output: "
        f"{OUTPUT_PATH}"
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
        "No GitHub requests were made."
    )


if __name__ == "__main__":
    main()