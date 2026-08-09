"""Domain model representing one research dataset observation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchRecord:
    """One pull request observation prepared for research analysis."""

    repository: str
    pull_request_number: int
    title: str
    description: str
    author: str

    is_merged: bool
    merge_commit_sha: str | None

    total_files: int
    source_file_count: int
    test_file_count: int
    documentation_file_count: int
    configuration_file_count: int
    other_file_count: int

    additions: int
    deletions: int
    commits_count: int

    eligible: bool
    exclusion_reason: str | None