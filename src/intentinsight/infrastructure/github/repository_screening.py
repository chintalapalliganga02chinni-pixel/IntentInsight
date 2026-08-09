"""Repository screening models for research dataset selection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryScreeningResult:
    """Research-oriented summary of a candidate GitHub repository."""

    owner: str
    name: str
    full_name: str
    default_branch: str
    is_private: bool
    url: str

    stars: int
    forks: int
    open_issues: int

    total_pull_requests: int
    merged_pull_requests: int

    first_pull_request_created_at: str | None
    latest_pull_request_created_at: str | None

    has_sufficient_history: bool

    @property
    def merged_pull_request_ratio(self) -> float:
        """Return the proportion of observed pull requests that were merged."""
        if self.total_pull_requests == 0:
            return 0.0

        return self.merged_pull_requests / self.total_pull_requests