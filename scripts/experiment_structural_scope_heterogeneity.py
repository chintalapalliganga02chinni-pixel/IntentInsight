"""Analyse heterogeneity of the structural-scope ablation effect.

READ-ONLY EXPERIMENT.

For each of the 703 eligible PRs, compare:
    FULL structural divergence
    PYTHON-ONLY structural divergence

Then relate the paired divergence difference to the amount/type of
non-Python file impact.

No database records are modified.
No embeddings are overwritten.
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
class PRResult:
    """One PR's structural-scope comparison."""

    repository_id: int
    pull_request_number: int

    full_divergence: float
    python_divergence: float

    non_python_files: int
    python_files: int

    non_python_additions: int
    non_python_deletions: int
    non_python_changes: int

    total_files: int
    total_changes: int

    documentation_files: int
    configuration_files: int
    test_files: int
    other_files: int
    asset_files: int

    @property
    def delta(self) -> float:
        """Python-only minus full divergence."""

        return (
            self.python_divergence
            - self.full_divergence
        )

    @property
    def non_python_ratio(self) -> float:
        """Fraction of changed files that are non-Python."""

        if self.total_files == 0:
            return 0.0

        return (
            self.non_python_files
            / self.total_files
        )

    @property
    def non_python_change_ratio(self) -> float:
        """Fraction of changed lines belonging to non-Python files."""

        if self.total_changes == 0:
            return 0.0

        return (
            self.non_python_changes
            / self.total_changes
        )


def is_python_file(filename: str) -> bool:
    """Return whether a file is Python source."""

    normalized = filename.replace("\\", "/")

    return normalized.endswith(
        (".py", ".pyi")
    )


def classify_non_python(
    filename: str,
) -> str:
    """Classify a non-Python file."""

    normalized = filename.replace("\\", "/")
    lower = normalized.lower()

    documentation_extensions = (
        ".rst",
        ".md",
        ".txt",
        ".adoc",
        ".markdown",
    )

    configuration_names = {
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "tox.ini",
        ".pre-commit-config.yaml",
        ".pre-commit-config.yml",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-dev.in",
    }

    configuration_extensions = (
        ".toml",
        ".ini",
        ".cfg",
        ".yaml",
        ".yml",
        ".json",
    )

    asset_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".webp",
        ".css",
        ".scss",
        ".less",
        ".js",
        ".map",
    )

    if (
        lower.startswith("docs/")
        or lower.startswith("doc/")
        or lower.endswith(
            documentation_extensions
        )
    ):
        return "documentation"

    filename_only = lower.rsplit("/", 1)[-1]

    if (
        filename_only in configuration_names
        or lower.startswith(
            (
                ".github/",
                "requirements/",
                "config/",
                "configs/",
            )
        )
        or lower.endswith(
            configuration_extensions
        )
    ):
        return "configuration/build"

    if (
        "/test" in lower
        or lower.startswith("test/")
        or lower.startswith("tests/")
        or lower.endswith(
            (
                "_test.rst",
                "_test.txt",
            )
        )
    ):
        return "tests"

    if lower.endswith(asset_extensions):
        return "assets/frontend"

    return "other"


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

    if (
        left_norm == 0.0
        or right_norm == 0.0
    ):
        return 0.0

    return dot / (
        left_norm * right_norm
    )


def build_python_only_embedding(
    rows: list[sqlite3.Row],
    encoder: IntentEncoder,
) -> list[float]:
    """Build the Python-only structural embedding."""

    module_data: dict[
        str,
        int,
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

        module_data[module] = (
            module_data.get(module, 0)
            + int(row["changes"] or 0)
        )

    if not module_data:
        return [
            0.0
        ] * EMBEDDING_DIMENSION

    modules = sorted(module_data)

    embeddings = encoder.encode_many(
        [
            module.replace(".", " ")
            for module in modules
        ]
    )

    weights = [
        1.0
        + math.log1p(
            max(
                module_data[module],
                0,
            )
        )
        for module in modules
    ]

    total_weight = sum(weights)

    if total_weight <= 0:
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

    if magnitude == 0:
        return weighted

    return [
        value / magnitude
        for value in weighted
    ]


def pearson(
    x: list[float],
    y: list[float],
) -> float:
    """Calculate Pearson correlation."""

    if len(x) != len(y):
        raise ValueError(
            "Vectors have different lengths."
        )

    x_mean = mean(x)
    y_mean = mean(y)

    numerator = sum(
        (
            xv - x_mean
        )
        * (
            yv - y_mean
        )
        for xv, yv in zip(
            x,
            y,
            strict=True,
        )
    )

    x_denominator = math.sqrt(
        sum(
            (value - x_mean) ** 2
            for value in x
        )
    )

    y_denominator = math.sqrt(
        sum(
            (value - y_mean) ** 2
            for value in y
        )
    )

    if (
        x_denominator == 0
        or y_denominator == 0
    ):
        return 0.0

    return (
        numerator
        / (
            x_denominator
            * y_denominator
        )
    )


def percentile(
    values: list[float],
    fraction: float,
) -> float:
    """Calculate an interpolated percentile."""

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

    weight = position - lower

    return (
        ordered[lower]
        * (1.0 - weight)
        + ordered[upper]
        * weight
    )


def describe(
    name: str,
    values: list[float],
) -> None:
    """Print descriptive statistics."""

    print()
    print(name)

    print(
        "n:",
        len(values),
    )

    print(
        "Min:",
        f"{min(values):.6f}",
    )

    print(
        "Q1:",
        f"{percentile(values, 0.25):.6f}",
    )

    print(
        "Median:",
        f"{median(values):.6f}",
    )

    print(
        "Mean:",
        f"{mean(values):.6f}",
    )

    print(
        "Q3:",
        f"{percentile(values, 0.75):.6f}",
    )

    print(
        "Max:",
        f"{max(values):.6f}",
    )


def compare_groups(
    name: str,
    results: list[PRResult],
) -> None:
    """Print divergence statistics for a PR group."""

    if not results:
        print()
        print(name)
        print("No PRs in group.")
        return

    deltas = [
        result.delta
        for result in results
    ]

    print()
    print("=" * 72)
    print(name)
    print("=" * 72)

    print(
        "PRs:",
        len(results),
    )

    print(
        "Mean full divergence:",
        f"{mean(result.full_divergence for result in results):.6f}",
    )

    print(
        "Mean Python-only divergence:",
        f"{mean(result.python_divergence for result in results):.6f}",
    )

    print(
        "Mean delta:",
        f"{mean(deltas):.6f}",
    )

    print(
        "Median delta:",
        f"{median(deltas):.6f}",
    )

    print(
        "Mean absolute delta:",
        f"{mean(abs(delta) for delta in deltas):.6f}",
    )

    print(
        "Python-only higher:",
        sum(
            delta > 0
            for delta in deltas
        ),
    )

    print(
        "Full higher:",
        sum(
            delta < 0
            for delta in deltas
        ),
    )

    print(
        "Identical:",
        sum(
            math.isclose(
                delta,
                0.0,
                abs_tol=1e-9,
            )
            for delta in deltas
        ),
    )


def main() -> None:
    """Run the heterogeneity experiment."""

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = (
        sqlite3.Row
    )

    prs = connection.execute(
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
    print(
        "IntentInsight Structural-Scope "
        "Heterogeneity Experiment"
    )
    print("=" * 72)
    print()

    print(
        "PRs analysed:",
        len(prs),
    )

    if len(prs) != 703:
        raise RuntimeError(
            f"Expected 703 PRs, "
            f"found {len(prs)}."
        )

    print()
    print("READ-ONLY EXPERIMENT")
    print(
        "No database records will be modified."
    )
    print(
        "No existing embeddings will be modified."
    )
    print(
        "No GitHub requests will be made."
    )

    encoder = IntentEncoder()

    results: list[PRResult] = []

    for index, pr in enumerate(
        prs,
        start=1,
    ):
        repository_id = int(
            pr["repository_id"]
        )

        pull_request_number = int(
            pr["pull_request_number"]
        )

        intent_embedding = json.loads(
            pr["intent_embedding"]
        )

        full_embedding = json.loads(
            pr["full_structural_embedding"]
        )

        rows = connection.execute(
            """
            SELECT
                filename,
                status,
                additions,
                deletions,
                changes
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

        non_python_files = 0
        python_files = 0

        non_python_additions = 0
        non_python_deletions = 0
        non_python_changes = 0

        documentation_files = 0
        configuration_files = 0
        test_files = 0
        other_files = 0
        asset_files = 0

        total_changes = 0

        for row in rows:
            filename = str(
                row["filename"]
            )

            additions = int(
                row["additions"] or 0
            )

            deletions = int(
                row["deletions"] or 0
            )

            changes = int(
                row["changes"] or 0
            )

            total_changes += changes

            if is_python_file(filename):
                python_files += 1
                continue

            non_python_files += 1

            non_python_additions += additions
            non_python_deletions += deletions
            non_python_changes += changes

            category = classify_non_python(
                filename
            )

            if category == "documentation":
                documentation_files += 1

            elif category == "configuration/build":
                configuration_files += 1

            elif category == "tests":
                test_files += 1

            elif category == "assets/frontend":
                asset_files += 1

            else:
                other_files += 1

        python_embedding = (
            build_python_only_embedding(
                rows,
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

        results.append(
            PRResult(
                repository_id=repository_id,
                pull_request_number=(
                    pull_request_number
                ),
                full_divergence=(
                    1.0 - full_similarity
                ),
                python_divergence=(
                    1.0 - python_similarity
                ),
                non_python_files=(
                    non_python_files
                ),
                python_files=python_files,
                non_python_additions=(
                    non_python_additions
                ),
                non_python_deletions=(
                    non_python_deletions
                ),
                non_python_changes=(
                    non_python_changes
                ),
                total_files=len(rows),
                total_changes=total_changes,
                documentation_files=(
                    documentation_files
                ),
                configuration_files=(
                    configuration_files
                ),
                test_files=test_files,
                other_files=other_files,
                asset_files=asset_files,
            )
        )

        if index % 50 == 0:
            print(
                f"{index}/{len(prs)} PRs analysed"
            )

    connection.close()

    # ------------------------------------------------------------
    # Basic groups
    # ------------------------------------------------------------

    no_non_python = [
        result
        for result in results
        if result.non_python_files == 0
    ]

    has_non_python = [
        result
        for result in results
        if result.non_python_files > 0
    ]

    compare_groups(
        "NO NON-PYTHON FILES",
        no_non_python,
    )

    compare_groups(
        "HAS NON-PYTHON FILES",
        has_non_python,
    )

    # ------------------------------------------------------------
    # File-count bands
    # ------------------------------------------------------------

    file_bands = [
        (
            "1 non-Python file",
            lambda r: r.non_python_files == 1,
        ),
        (
            "2-3 non-Python files",
            lambda r: 2 <= r.non_python_files <= 3,
        ),
        (
            "4-10 non-Python files",
            lambda r: 4 <= r.non_python_files <= 10,
        ),
        (
            "11+ non-Python files",
            lambda r: r.non_python_files >= 11,
        ),
    ]

    for name, predicate in file_bands:
        compare_groups(
            name,
            [
                result
                for result in results
                if predicate(result)
            ],
        )

    # ------------------------------------------------------------
    # Non-Python change bands
    # ------------------------------------------------------------

    change_bands = [
        (
            "0 non-Python changes",
            lambda r: r.non_python_changes == 0,
        ),
        (
            "1-10 non-Python changes",
            lambda r: 1 <= r.non_python_changes <= 10,
        ),
        (
            "11-50 non-Python changes",
            lambda r: 11 <= r.non_python_changes <= 50,
        ),
        (
            "51-200 non-Python changes",
            lambda r: 51 <= r.non_python_changes <= 200,
        ),
        (
            "201+ non-Python changes",
            lambda r: r.non_python_changes >= 201,
        ),
    ]

    for name, predicate in change_bands:
        compare_groups(
            name,
            [
                result
                for result in results
                if predicate(result)
            ],
        )

    # ------------------------------------------------------------
    # Non-Python ratio bands
    # ------------------------------------------------------------

    ratio_bands = [
        (
            "0% non-Python",
            lambda r: r.non_python_ratio == 0.0,
        ),
        (
            "1-25% non-Python",
            lambda r: 0.0 < r.non_python_ratio <= 0.25,
        ),
        (
            "26-50% non-Python",
            lambda r: 0.25 < r.non_python_ratio <= 0.50,
        ),
        (
            "51-75% non-Python",
            lambda r: 0.50 < r.non_python_ratio <= 0.75,
        ),
        (
            "76-100% non-Python",
            lambda r: r.non_python_ratio > 0.75,
        ),
    ]

    for name, predicate in ratio_bands:
        compare_groups(
            name,
            [
                result
                for result in results
                if predicate(result)
            ],
        )

    # ------------------------------------------------------------
    # Category presence
    # ------------------------------------------------------------

    category_groups = [
        (
            "DOCUMENTATION PRESENT",
            lambda r: r.documentation_files > 0,
        ),
        (
            "CONFIGURATION/BUILD PRESENT",
            lambda r: r.configuration_files > 0,
        ),
        (
            "TEST FILES PRESENT",
            lambda r: r.test_files > 0,
        ),
        (
            "OTHER NON-PYTHON PRESENT",
            lambda r: r.other_files > 0,
        ),
        (
            "ASSETS/FRONTEND PRESENT",
            lambda r: r.asset_files > 0,
        ),
    ]

    for name, predicate in category_groups:
        compare_groups(
            name,
            [
                result
                for result in results
                if predicate(result)
            ],
        )

    # ------------------------------------------------------------
    # Correlations with the divergence delta
    # ------------------------------------------------------------

    deltas = [
        result.delta
        for result in results
    ]

    predictors = [
        (
            "non_python_files",
            [
                float(
                    result.non_python_files
                )
                for result in results
            ],
        ),
        (
            "non_python_ratio",
            [
                result.non_python_ratio
                for result in results
            ],
        ),
        (
            "non_python_additions",
            [
                float(
                    result.non_python_additions
                )
                for result in results
            ],
        ),
        (
            "non_python_deletions",
            [
                float(
                    result.non_python_deletions
                )
                for result in results
            ],
        ),
        (
            "non_python_changes",
            [
                float(
                    result.non_python_changes
                )
                for result in results
            ],
        ),
        (
            "non_python_change_ratio",
            [
                result.non_python_change_ratio
                for result in results
            ],
        ),
    ]

    print()
    print("=" * 72)
    print("CORRELATION WITH DIVERGENCE DELTA")
    print("=" * 72)

    print(
        "Positive delta means Python-only divergence "
        "is higher than full divergence."
    )

    for name, values in predictors:
        print(
            f"{name}: "
            f"Pearson r = "
            f"{pearson(values, deltas):.6f}"
        )

    # ------------------------------------------------------------
    # Direction by category
    # ------------------------------------------------------------

    print()
    print("=" * 72)
    print("DIRECTION OF EFFECT BY NON-PYTHON CATEGORY")
    print("=" * 72)

    for category_name, predicate in category_groups:
        group = [
            result
            for result in results
            if predicate(result)
        ]

        if not group:
            continue

        category_deltas = [
            result.delta
            for result in group
        ]

        print()
        print(category_name)
        print(
            "PRs:",
            len(group),
        )
        print(
            "Mean delta:",
            f"{mean(category_deltas):.6f}",
        )
        print(
            "Median delta:",
            f"{median(category_deltas):.6f}",
        )
        print(
            "Python-only higher:",
            sum(
                delta > 0
                for delta in category_deltas
            ),
        )
        print(
            "Full higher:",
            sum(
                delta < 0
                for delta in category_deltas
            ),
        )

    # ------------------------------------------------------------
    # Extreme cases
    # ------------------------------------------------------------

    ordered = sorted(
        results,
        key=lambda result: result.delta,
        reverse=True,
    )

    print()
    print("=" * 72)
    print("LARGEST POSITIVE EFFECTS")
    print("=" * 72)

    for result in ordered[:15]:
        print(
            f"PR #{result.pull_request_number}: "
            f"delta={result.delta:+.6f}, "
            f"non_python_files={result.non_python_files}, "
            f"non_python_changes={result.non_python_changes}, "
            f"non_python_ratio={result.non_python_ratio:.3f}, "
            f"docs={result.documentation_files}, "
            f"config={result.configuration_files}, "
            f"tests={result.test_files}, "
            f"other={result.other_files}, "
            f"assets={result.asset_files}"
        )

    print()
    print("=" * 72)
    print("LARGEST NEGATIVE EFFECTS")
    print("=" * 72)

    for result in ordered[-15:][::-1]:
        print(
            f"PR #{result.pull_request_number}: "
            f"delta={result.delta:+.6f}, "
            f"non_python_files={result.non_python_files}, "
            f"non_python_changes={result.non_python_changes}, "
            f"non_python_ratio={result.non_python_ratio:.3f}, "
            f"docs={result.documentation_files}, "
            f"config={result.configuration_files}, "
            f"tests={result.test_files}, "
            f"other={result.other_files}, "
            f"assets={result.asset_files}"
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