"""Application service for screening GitHub repositories."""

from __future__ import annotations

from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)
from intentinsight.infrastructure.github.client import GitHubClient
from intentinsight.infrastructure.github.repository_screening import (
    RepositoryScreeningResult,
)


class RepositoryScreeningService:
    """Evaluate candidate repositories for research suitability."""

    def __init__(
            self,
            github_client: GitHubClient,
            pull_request_miner: PullRequestMiner,
    ) -> None:
        self._github_client = github_client
        self._pull_request_miner = pull_request_miner

    def screen_repository(
            self,
            owner: str,
            repository: str,
    ) -> RepositoryScreeningResult:
        """Collect repository-level research suitability information."""
        repository_info = self._github_client.get_repository(
            owner,
            repository,
        )

        pull_requests = self._pull_request_miner.mine_repository(
            owner=owner,
            repository=repository,
            state="all",
            per_page=100,
        )

        merged_pull_requests = [
            pull_request
            for pull_request in pull_requests
            if pull_request.is_merged
        ]

        created_dates = [
            pull_request.created_at
            for pull_request in pull_requests
        ]

        return RepositoryScreeningResult(
            owner=repository_info.owner,
            name=repository_info.name,
            full_name=repository_info.full_name,
            default_branch=repository_info.default_branch,
            is_private=repository_info.private,
            url=repository_info.url,
            stars=repository_info.stars,
            forks=repository_info.forks,
            open_issues=repository_info.open_issues,
            total_pull_requests=len(pull_requests),
            merged_pull_requests=len(merged_pull_requests),
            first_pull_request_created_at=(
                min(created_dates).isoformat()
                if created_dates
                else None
            ),
            latest_pull_request_created_at=(
                max(created_dates).isoformat()
                if created_dates
                else None
            ),
            has_sufficient_history=len(merged_pull_requests) >= 50,
        )