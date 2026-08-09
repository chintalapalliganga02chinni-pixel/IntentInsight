"""Application service for mining pull requests."""

from __future__ import annotations

from collections.abc import Iterator

from intentinsight.domain.models import PullRequest
from intentinsight.infrastructure.github.client import GitHubClient
from intentinsight.infrastructure.github.pull_request_mapper import (
    map_pull_request,
)


class PullRequestMiner:
    """Mine pull requests from a GitHub repository."""

    def __init__(self, github_client: GitHubClient) -> None:
        self._github_client = github_client

    def mine_repository(
            self,
            owner: str,
            repository: str,
            *,
            state: str = "all",
            per_page: int = 100,
    ) -> list[PullRequest]:
        """Retrieve and map all pull requests from a repository."""
        pull_requests: list[PullRequest] = []

        for pull_request in self._iterate_pull_requests(
                owner=owner,
                repository=repository,
                state=state,
                per_page=per_page,
        ):
            pull_requests.append(
                map_pull_request(
                    repository=f"{owner}/{repository}",
                    data=pull_request,
                )
            )

        return pull_requests

    def _iterate_pull_requests(
            self,
            owner: str,
            repository: str,
            *,
            state: str,
            per_page: int,
    ) -> Iterator[dict]:
        """Iterate through all pull-request pages."""
        page = 1

        while True:
            current_page = self._github_client.list_pull_requests(
                owner=owner,
                repository=repository,
                state=state,
                page=page,
                per_page=per_page,
            )

            if not current_page:
                break

            yield from current_page

            if len(current_page) < per_page:
                break

            page += 1