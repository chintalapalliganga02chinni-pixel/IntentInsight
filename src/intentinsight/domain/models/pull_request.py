"""Domain model representing a pull request."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PullRequest:
    """Represents the research-relevant attributes of a pull request."""

    repository: str
    number: int
    title: str
    description: str
    author: str
    state: str
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None
    merge_commit_sha: str | None
    commits_count: int
    changed_files_count: int
    additions: int
    deletions: int

    @property
    def is_merged(self) -> bool:
        """Return whether the pull request was merged."""
        return self.merged_at is not None