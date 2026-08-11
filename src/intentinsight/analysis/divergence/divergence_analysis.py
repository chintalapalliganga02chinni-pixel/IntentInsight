"""Mathematical analysis of semantic intent and structural impact."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DivergenceMetrics:
    """Computed metrics for one pull request."""

    intent_similarity: float
    intent_impact_divergence: float

    module_count: int
    changed_file_count: int

    module_entropy: float
    module_concentration: float
    top_module_weight: float

    package_count: int
    cross_package_spread: int


def _dot(
    left: list[float],
    right: list[float],
) -> float:
    """Calculate a vector dot product."""

    if len(left) != len(right):
        raise ValueError(
            "Vectors must have identical dimensions."
        )

    return sum(
        left_value * right_value
        for left_value, right_value in zip(
            left,
            right,
            strict=True,
        )
    )


def _magnitude(
    vector: list[float],
) -> float:
    """Calculate Euclidean vector magnitude."""

    return math.sqrt(
        sum(value * value for value in vector)
    )


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    """
    Calculate cosine similarity.

    The result is theoretically in [-1, 1].
    """

    left_magnitude = _magnitude(left)
    right_magnitude = _magnitude(right)

    if left_magnitude == 0 or right_magnitude == 0:
        raise ValueError(
            "Cosine similarity is undefined for a zero vector."
        )

    similarity = (
        _dot(left, right)
        / (left_magnitude * right_magnitude)
    )

    # Protect against tiny floating-point excursions.
    return max(-1.0, min(1.0, similarity))


def divergence_from_similarity(
    similarity: float,
) -> float:
    """
    Convert cosine similarity into a divergence score.

    D = 1 - cosine_similarity.

    A value near 0 indicates strong alignment.
    Larger values indicate greater divergence.
    """

    if similarity < -1.000001 or similarity > 1.000001:
        raise ValueError(
            "Cosine similarity must be in [-1, 1]."
        )

    similarity = max(-1.0, min(1.0, similarity))

    return 1.0 - similarity


def normalized_entropy(
    weights: list[float],
) -> float:
    """
    Calculate normalized Shannon entropy.

    The result is in [0, 1] for a non-empty positive
    distribution.

    0 means concentrated in one module.
    1 means approximately uniform distribution.
    """

    positive_weights = [
        float(weight)
        for weight in weights
        if float(weight) > 0
    ]

    if len(positive_weights) <= 1:
        return 0.0

    total = sum(positive_weights)

    if total <= 0:
        return 0.0

    probabilities = [
        weight / total
        for weight in positive_weights
    ]

    entropy = -sum(
        probability * math.log(probability)
        for probability in probabilities
    )

    maximum_entropy = math.log(
        len(probabilities)
    )

    if maximum_entropy == 0:
        return 0.0

    return entropy / maximum_entropy


def module_concentration(
    weights: list[float],
) -> float:
    """
    Calculate the share of total impact attributable
    to the most heavily impacted module.
    """

    positive_weights = [
        float(weight)
        for weight in weights
        if float(weight) > 0
    ]

    if not positive_weights:
        return 0.0

    total = sum(positive_weights)

    if total <= 0:
        return 0.0

    return max(positive_weights) / total


def module_package_identity(
    module: str,
) -> str:
    """
    Derive a reproducible top-level package/path identity.

    This is intentionally described as a path-derived package
    identity, not as a claim about true software architecture.
    """

    parts = [
        part
        for part in module.split(".")
        if part
    ]

    if not parts:
        return "<unknown>"

    return parts[0]


def calculate_divergence_metrics(
    intent_embedding: list[float],
    structural_embedding: list[float],
    module_profile: list[dict[str, Any]],
    changed_file_count: int,
) -> DivergenceMetrics:
    """Calculate the complete first-generation divergence profile."""

    similarity = cosine_similarity(
        intent_embedding,
        structural_embedding,
    )

    divergence = divergence_from_similarity(
        similarity,
    )

    modules = [
        item
        for item in module_profile
        if isinstance(item, dict)
    ]

    weights = [
        float(item.get("weight", 0.0))
        for item in modules
    ]

    module_names = [
        str(item.get("module", "<unknown>"))
        for item in modules
    ]

    packages = {
        module_package_identity(module)
        for module in module_names
    }

    return DivergenceMetrics(
        intent_similarity=similarity,
        intent_impact_divergence=divergence,
        module_count=len(modules),
        changed_file_count=changed_file_count,
        module_entropy=normalized_entropy(weights),
        module_concentration=module_concentration(weights),
        top_module_weight=max(weights, default=0.0),
        package_count=len(packages),
        cross_package_spread=max(0, len(packages) - 1),
    )


def parse_embedding(
    value: str,
) -> list[float]:
    """Decode an embedding stored as JSON."""

    decoded = json.loads(value)

    if not isinstance(decoded, list):
        raise ValueError(
            "Embedding JSON must contain a list."
        )

    return [
        float(item)
        for item in decoded
    ]


def parse_module_profile(
    value: str,
) -> list[dict[str, Any]]:
    """Decode the stored module profile."""

    decoded = json.loads(value)

    if not isinstance(decoded, list):
        raise ValueError(
            "Module profile JSON must contain a list."
        )

    return [
        item
        for item in decoded
        if isinstance(item, dict)
    ]


def utc_now() -> str:
    """Return a UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()