"""Models for GitHub commit comparisons."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GitComparisonFile:
    """One file changed in a GitHub commit comparison."""

    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    sha: str
    previous_filename: str | None = None


@dataclass(frozen=True)
class GitComparison:
    """A comparison between two Git references."""

    base_sha: str
    head_sha: str
    merge_base_sha: str | None
    status: str
    ahead_by: int
    behind_by: int
    files: tuple[GitComparisonFile, ...]