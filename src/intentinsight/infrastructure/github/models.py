"""Response models for GitHub integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryInfo:
    """Basic information about a GitHub repository."""

    owner: str
    name: str
    full_name: str
    default_branch: str
    private: bool
    url: str
    stars: int = 0
    forks: int = 0
    open_issues: int = 0


@dataclass(frozen=True)
class PullRequestFile:
    """Information about a file changed by a pull request."""

    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    sha: str