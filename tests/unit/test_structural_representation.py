"""Tests for structural pull-request representations."""

from unittest.mock import Mock

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.structural.structural_representation import (
    StructuralRepresentationBuilder,
)


def test_structural_representation_aggregates_changed_files() -> None:
    """Changed files should aggregate into module-level impact."""

    encoder = Mock(spec=IntentEncoder)

    encoder.encode_many.side_effect = lambda texts: [
        [1.0, 0.0, 0.0]
        for _ in texts
    ]

    builder = StructuralRepresentationBuilder(
        encoder=encoder,
    )

    result = builder.build(
        [
            {
                "filename": "flask/app.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15,
            },
            {
                "filename": "flask/app.py",
                "status": "modified",
                "additions": 2,
                "deletions": 1,
                "changes": 3,
            },
            {
                "filename": "flask/ctx.py",
                "status": "added",
                "additions": 20,
                "deletions": 0,
                "changes": 20,
            },
        ]
    )

    assert result["changed_file_count"] == 3
    assert result["module_count"] == 2
    assert result["total_additions"] == 32
    assert result["total_deletions"] == 6
    assert result["total_changes"] == 38
    assert result["modified_file_count"] == 2
    assert result["added_file_count"] == 1

    modules = result["modules"]

    assert "flask.app" in modules
    assert "flask.ctx" in modules

    assert len(result["embedding"]) == 3


def test_empty_structural_representation_is_supported() -> None:
    """An empty file set should produce a deterministic representation."""

    encoder = Mock(spec=IntentEncoder)

    builder = StructuralRepresentationBuilder(
        encoder=encoder,
    )

    result = builder.build([])

    assert result["changed_file_count"] == 0
    assert result["module_count"] == 0
    assert result["total_changes"] == 0
    assert result["modules"] == []
    assert result["embedding"] == [0.0] * 384