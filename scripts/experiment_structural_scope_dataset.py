"""Build a read-only per-PR structural-scope analysis dataset."""

from __future__ import annotations

import csv
import json
import math
import sqlite3
from pathlib import Path

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.structural.module_path import filename_to_module


DB = "intentinsight.db"
OUTPUT = Path("structural_scope_analysis.csv")
DIMENSION = 384


def is_python(filename: str) -> bool:
    filename = filename.replace("\\", "/").lower()
    return filename.endswith((".py", ".pyi"))


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Embedding dimensions differ.")

    dot = sum(x * y for x, y in zip(a, b, strict=True))

    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))

    if na == 0 or nb == 0:
        return 0.0

    return dot / (na * nb)


def python_embedding(
    rows: list[sqlite3.Row],
    encoder: IntentEncoder,
) -> list[float]:

    module_changes: dict[str, int] = {}

    for row in rows:
        filename = str(row["filename"])

        if not is_python(filename):
            continue

        module = filename_to_module(filename)

        module_changes[module] = (
            module_changes.get(module, 0)
            + int(row["changes"] or 0)
        )

    if not module_changes:
        return [0.0] * DIMENSION

    modules = sorted(module_changes)

    embeddings = encoder.encode_many(
        [
            module.replace(".", " ")
            for module in modules
        ]
    )

    weights = [
        1.0 + math.log1p(
            max(module_changes[module], 0)
        )
        for module in modules
    ]

    total_weight = sum(weights)

    if total_weight <= 0:
        return [0.0] * len(embeddings[0])

    result = [0.0] * len(embeddings[0])

    for weight, embedding in zip(
        weights,
        embeddings,
        strict=True,
    ):
        weight /= total_weight

        for i, value in enumerate(embedding):
            result[i] += weight * value

    magnitude = math.sqrt(
        sum(value * value for value in result)
    )

    if magnitude == 0:
        return result

    return [
        value / magnitude
        for value in result
    ]


def classify(filename: str) -> str:
    value = filename.replace("\\", "/").lower()

    name = value.rsplit("/", 1)[-1]

    if (
        value.startswith("docs/")
        or value.startswith("doc/")
        or value.endswith(
            (".rst", ".md", ".markdown", ".adoc")
        )
    ):
        return "documentation"

    if (
        name in {
            "pyproject.toml",
            "setup.cfg",
            "tox.ini",
            ".pre-commit-config.yaml",
            ".pre-commit-config.yml",
        }
        or value.startswith(
            (".github/", "requirements/")
        )
        or value.endswith(
            (".toml", ".ini", ".cfg", ".yaml", ".yml")
        )
    ):
        return "configuration_build"

    if (
        value.startswith(("test/", "tests/"))
        or "/tests/" in value
    ):
        return "tests"

    if value.endswith(
        (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".css",
            ".scss",
            ".js",
        )
    ):
        return "assets_frontend"

    return "other"


def main() -> None:
    print("=" * 72)
    print("IntentInsight Structural Scope Dataset")
    print("=" * 72)
    print()
    print("READ-ONLY")
    print("No database records will be modified.")
    print("No GitHub requests will be made.")
    print()

    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row

    prs = connection.execute(
        """
        SELECT
            rr.repository_id,
            rr.pull_request_number,
            rr.total_files,
            rr.additions,
            rr.deletions,
            structures.embedding_json
        FROM research_records AS rr
        JOIN pull_request_structures AS structures
          ON structures.repository_id = rr.repository_id
         AND structures.pull_request_number = rr.pull_request_number
        WHERE rr.eligible = 1
        ORDER BY
            rr.repository_id,
            rr.pull_request_number
        """
    ).fetchall()

    if len(prs) != 703:
        raise RuntimeError(
            f"Expected 703 PRs, found {len(prs)}."
        )

    print(f"PRs analysed: {len(prs)}")

    encoder = IntentEncoder()

    rows_out = []

    for index, pr in enumerate(prs, start=1):

        repository_id = int(pr["repository_id"])
        pr_number = int(pr["pull_request_number"])

        intent_row = connection.execute(
            """
            SELECT embedding_json
            FROM pull_request_intents
            WHERE repository_id = ?
              AND pull_request_number = ?
            """,
            (repository_id, pr_number),
        ).fetchone()

        if intent_row is None:
            raise RuntimeError(
                f"Missing intent embedding for PR #{pr_number}"
            )

        intent = json.loads(
            intent_row["embedding_json"]
        )

        full_embedding = json.loads(
            pr["embedding_json"]
        )

        files = connection.execute(
            """
            SELECT
                filename,
                additions,
                deletions,
                changes
            FROM pull_request_files
            WHERE repository_id = ?
              AND pull_request_number = ?
            ORDER BY id
            """,
            (repository_id, pr_number),
        ).fetchall()

        python_files = 0
        non_python_files = 0

        python_changes = 0
        non_python_changes = 0

        documentation_files = 0
        configuration_files = 0
        test_files = 0
        assets_files = 0
        other_files = 0

        for file in files:

            filename = str(file["filename"])

            changes = int(
                file["changes"] or 0
            )

            if is_python(filename):
                python_files += 1
                python_changes += changes
            else:
                non_python_files += 1
                non_python_changes += changes

                category = classify(filename)

                if category == "documentation":
                    documentation_files += 1
                elif category == "configuration_build":
                    configuration_files += 1
                elif category == "tests":
                    test_files += 1
                elif category == "assets_frontend":
                    assets_files += 1
                else:
                    other_files += 1

        py_embedding = python_embedding(
            files,
            encoder,
        )

        full_similarity = cosine(
            intent,
            full_embedding,
        )

        python_similarity = cosine(
            intent,
            py_embedding,
        )

        full_divergence = (
            1.0 - full_similarity
        )

        python_divergence = (
            1.0 - python_similarity
        )

        total_files = len(files)
        total_changes = sum(
            int(file["changes"] or 0)
            for file in files
        )

        non_python_ratio = (
            non_python_files / total_files
            if total_files
            else 0.0
        )

        non_python_change_ratio = (
            non_python_changes / total_changes
            if total_changes
            else 0.0
        )

        rows_out.append(
            {
                "repository_id": repository_id,
                "pull_request_number": pr_number,
                "full_divergence": full_divergence,
                "python_divergence": python_divergence,
                "delta": (
                    python_divergence
                    - full_divergence
                ),
                "total_files": total_files,
                "python_files": python_files,
                "non_python_files": non_python_files,
                "total_changes": total_changes,
                "python_changes": python_changes,
                "non_python_changes": non_python_changes,
                "non_python_ratio": non_python_ratio,
                "non_python_change_ratio": (
                    non_python_change_ratio
                ),
                "module_count": int(
                    connection.execute(
                        """
                        SELECT module_count
                        FROM pull_request_structures
                        WHERE repository_id = ?
                          AND pull_request_number = ?
                        """,
                        (repository_id, pr_number),
                    ).fetchone()["module_count"]
                ),
                "documentation_files": documentation_files,
                "configuration_files": configuration_files,
                "test_files": test_files,
                "assets_files": assets_files,
                "other_files": other_files,
            }
        )

        if index % 50 == 0:
            print(
                f"{index}/{len(prs)} PRs processed"
            )

    connection.close()

    fields = list(rows_out[0].keys())

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows_out)

    print()
    print("=" * 72)
    print("COMPLETE")
    print("=" * 72)
    print()
    print(f"Rows written: {len(rows_out)}")
    print(f"Output: {OUTPUT}")
    print()
    print("Database was not modified.")


if __name__ == "__main__":
    main()