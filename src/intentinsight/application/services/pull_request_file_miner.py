"""Application service for mining pull-request file changes."""

from __future__ import annotations

from intentinsight.domain.models.pull_request_file_summary import (
    PullRequestFileSummary,
)

from intentinsight.analysis.features.file_classifier import (
    FileCategory,
    classify_file,
)
from intentinsight.infrastructure.github.client import GitHubClient
from intentinsight.infrastructure.github.models import PullRequestFile


class PullRequestFileMiner:
    """Mine and classify files changed by pull requests."""

    def __init__(self, github_client: GitHubClient) -> None:
        self._github_client = github_client

    def mine_pull_request_files(
            self,
            owner: str,
            repository: str,
            pull_request_number: int,
            *,
            per_page: int = 100,
    ) -> PullRequestFileSummary:
        """Retrieve and classify all files changed by a pull request."""
        files: list[PullRequestFile] = []

        page = 1

        while True:
            current_page = self._github_client.list_pull_request_files(
                owner=owner,
                repository=repository,
                pull_request_number=pull_request_number,
                page=page,
                per_page=per_page,
            )

            if not current_page:
                break

            files.extend(current_page)

            if len(current_page) < per_page:
                break

            page += 1

        categorized: dict[FileCategory, list[PullRequestFile]] = {
            category: []
            for category in FileCategory
        }

        for file in files:
            categorized[classify_file(file)].append(file)

        return PullRequestFileSummary(
            files=tuple(files),
            source_files=tuple(
                categorized[FileCategory.SOURCE_CODE]
            ),
            test_files=tuple(
                categorized[FileCategory.TEST]
            ),
            documentation_files=tuple(
                categorized[FileCategory.DOCUMENTATION]
            ),
            configuration_files=tuple(
                categorized[FileCategory.CONFIGURATION]
            ),
            other_files=tuple(
                categorized[FileCategory.OTHER]
            ),
        )