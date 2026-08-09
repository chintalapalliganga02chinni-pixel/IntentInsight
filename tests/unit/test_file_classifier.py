"""Unit tests for changed-file classification."""

from __future__ import annotations

from intentinsight.analysis.features.file_classifier import (
    FileCategory,
    classify_file,
)
from intentinsight.infrastructure.github.models import PullRequestFile


def _file(filename: str) -> PullRequestFile:
    """Create a minimal pull request file."""
    return PullRequestFile(
        filename=filename,
        status="modified",
        additions=10,
        deletions=2,
        changes=12,
        sha="abc123",
    )


def test_python_source_file_is_classified_as_source_code() -> None:
    """Python application code should be source code."""
    assert classify_file(_file("src/application.py")) == (
        FileCategory.SOURCE_CODE
    )


def test_test_file_is_classified_as_test() -> None:
    """Files under tests should be classified as tests."""
    assert classify_file(_file("tests/test_application.py")) == (
        FileCategory.TEST
    )


def test_documentation_file_is_classified_as_documentation() -> None:
    """Markdown documentation should be classified as documentation."""
    assert classify_file(_file("README.md")) == (
        FileCategory.DOCUMENTATION
    )


def test_docs_directory_is_classified_as_documentation() -> None:
    """Files inside docs should be classified as documentation."""
    assert classify_file(_file("docs/guide.rst")) == (
        FileCategory.DOCUMENTATION
    )


def test_configuration_file_is_classified_as_configuration() -> None:
    """Project configuration should be classified appropriately."""
    assert classify_file(_file("pyproject.toml")) == (
        FileCategory.CONFIGURATION
    )


def test_github_workflow_is_classified_as_configuration() -> None:
    """GitHub workflow files should be configuration."""
    assert classify_file(
        _file(".github/workflows/ci.yml")
    ) == FileCategory.CONFIGURATION


def test_unknown_file_is_classified_as_other() -> None:
    """Unknown file types should remain in the dataset as other."""
    assert classify_file(_file("assets/logo.png")) == (
        FileCategory.OTHER
    )


def test_test_files_take_precedence_over_source_extension() -> None:
    """A Python test file should be classified as a test."""
    assert classify_file(_file("tests/example.py")) == (
        FileCategory.TEST
    )