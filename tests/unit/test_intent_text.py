"""Tests for semantic intent text construction."""

from intentinsight.analysis.intent.intent_text import (
    build_intent_text,
)


def test_intent_text_contains_title_and_description() -> None:
    """Intent text should contain both title and description."""

    result = build_intent_text(
        title="Improve request validation",
        description="Reject malformed requests earlier.",
    )

    assert "Improve request validation" in result
    assert "Reject malformed requests earlier." in result
    assert "Pull request title:" in result
    assert "Pull request description:" in result


def test_intent_text_handles_empty_description() -> None:
    """Intent text should remain valid without a description."""

    result = build_intent_text(
        title="Fix request handling",
        description="",
    )

    assert "Fix request handling" in result
    assert "Pull request title:" in result
    assert "Pull request description:" not in result