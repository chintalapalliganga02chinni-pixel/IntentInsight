"""Classification of files changed by pull requests."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath

from intentinsight.infrastructure.github.models import PullRequestFile


class FileCategory(StrEnum):
    """Research-oriented categories for changed files."""

    SOURCE_CODE = "source_code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    OTHER = "other"


SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".kt",
    ".kts",
    ".go",
    ".rs",
    ".c",
    ".h",
    ".cpp",
    ".cc",
    ".cxx",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
}

DOCUMENTATION_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
    ".adoc",
}

CONFIGURATION_FILENAMES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "pytest.ini",
    "package.json",
    "tsconfig.json",
    "pom.xml",
    "build.gradle",
    "cargo.toml",
    "go.mod",
    "requirements.txt",
}

CONFIGURATION_DIRECTORIES = {
    ".github",
}


def classify_file(file: PullRequestFile) -> FileCategory:
    """Classify one changed file for research analysis."""
    path = PurePosixPath(file.filename)
    filename = path.name.lower()

    if _is_test_file(path):
        return FileCategory.TEST

    if _is_documentation_file(path):
        return FileCategory.DOCUMENTATION

    if _is_configuration_file(path):
        return FileCategory.CONFIGURATION

    if path.suffix.lower() in SOURCE_EXTENSIONS:
        return FileCategory.SOURCE_CODE

    return FileCategory.OTHER


def _is_test_file(path: PurePosixPath) -> bool:
    """Return whether a path represents a test file."""
    parts = {part.lower() for part in path.parts}
    filename = path.name.lower()

    return (
            "tests" in parts
            or "test" in parts
            or filename.startswith("test_")
            or filename.startswith("test.")
            or filename.endswith("_test.py")
            or filename.endswith("_test.js")
            or filename.endswith("_test.ts")
    )


def _is_documentation_file(path: PurePosixPath) -> bool:
    """Return whether a path represents documentation."""
    parts = {part.lower() for part in path.parts}

    return (
            "docs" in parts
            or path.suffix.lower() in DOCUMENTATION_EXTENSIONS
    )


def _is_configuration_file(path: PurePosixPath) -> bool:
    """Return whether a path represents configuration."""
    parts = {part.lower() for part in path.parts}
    filename = path.name.lower()

    return (
            filename in CONFIGURATION_FILENAMES
            or any(directory in parts for directory in CONFIGURATION_DIRECTORIES)
    )