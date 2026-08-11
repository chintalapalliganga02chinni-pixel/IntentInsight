"""Tests for intent-impact divergence analysis."""

import math

import pytest

from intentinsight.analysis.divergence.divergence_analysis import (
    calculate_divergence_metrics,
    cosine_similarity,
    divergence_from_similarity,
    module_concentration,
    normalized_entropy,
)


def test_identical_vectors_have_perfect_similarity() -> None:
    """Identical vectors should have cosine similarity of one."""

    assert cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0],
    ) == pytest.approx(1.0)


def test_orthogonal_vectors_have_zero_similarity() -> None:
    """Orthogonal vectors should have zero similarity."""

    assert cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    ) == pytest.approx(0.0)


def test_opposite_vectors_have_maximum_divergence() -> None:
    """Opposite vectors should produce divergence of two."""

    similarity = cosine_similarity(
        [1.0, 0.0],
        [-1.0, 0.0],
    )

    assert similarity == pytest.approx(-1.0)

    assert divergence_from_similarity(
        similarity
    ) == pytest.approx(2.0)


def test_identical_vectors_have_zero_divergence() -> None:
    """Perfect semantic alignment should have zero divergence."""

    assert divergence_from_similarity(
        1.0
    ) == pytest.approx(0.0)


def test_normalized_entropy_is_zero_for_one_module() -> None:
    """A single impacted module has zero normalized entropy."""

    assert normalized_entropy(
        [10.0]
    ) == pytest.approx(0.0)


def test_normalized_entropy_is_one_for_uniform_distribution() -> None:
    """Uniform module impact should have maximum entropy."""

    assert normalized_entropy(
        [1.0, 1.0, 1.0, 1.0]
    ) == pytest.approx(1.0)


def test_module_concentration_is_dominant_share() -> None:
    """Concentration should equal the largest impact share."""

    assert module_concentration(
        [70.0, 20.0, 10.0]
    ) == pytest.approx(0.7)


def test_complete_divergence_profile() -> None:
    """The full divergence profile should be computed consistently."""

    result = calculate_divergence_metrics(
        intent_embedding=[1.0, 0.0, 0.0],
        structural_embedding=[1.0, 0.0, 0.0],
        module_profile=[
            {
                "module": "flask.app",
                "weight": 3.0,
            },
            {
                "module": "flask.ctx",
                "weight": 1.0,
            },
        ],
        changed_file_count=3,
    )

    assert result.intent_similarity == pytest.approx(1.0)
    assert result.intent_impact_divergence == pytest.approx(0.0)

    assert result.module_count == 2
    assert result.changed_file_count == 3

    assert result.module_entropy > 0.0
    assert result.module_concentration == pytest.approx(0.75)

    # Both modules belong to the same top-level path namespace.
    assert result.package_count == 1
    assert result.cross_package_spread == 0


def test_zero_vector_is_rejected() -> None:
    """Zero vectors cannot produce a cosine similarity."""

    with pytest.raises(ValueError):
        cosine_similarity(
            [0.0, 0.0],
            [1.0, 0.0],
        )


def test_dimension_mismatch_is_rejected() -> None:
    """Vectors with different dimensions must be rejected."""

    with pytest.raises(ValueError):
        cosine_similarity(
            [1.0, 0.0],
            [1.0],
        )