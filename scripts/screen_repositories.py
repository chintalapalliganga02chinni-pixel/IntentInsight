"""Screen candidate GitHub repositories for research suitability."""

from __future__ import annotations

from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)
from intentinsight.application.services.repository_screening_service import (
    RepositoryScreeningService,
)
from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient


CANDIDATE_REPOSITORIES = [
    ("pallets", "flask"),
    ("psf", "requests"),
    ("pytest-dev", "pytest"),
    ("pydantic", "pydantic"),
]


def main() -> None:
    """Screen all configured candidate repositories."""
    settings = load_settings()

    with GitHubClient(settings) as github_client:
        pull_request_miner = PullRequestMiner(github_client)

        screening_service = RepositoryScreeningService(
            github_client=github_client,
            pull_request_miner=pull_request_miner,
        )

        print()
        print("=" * 100)
        print("IntentInsight — Repository Screening")
        print("=" * 100)
        print()

        for owner, repository in CANDIDATE_REPOSITORIES:
            print(f"Screening {owner}/{repository} ...")

            result = screening_service.screen_repository(
                owner=owner,
                repository=repository,
            )

            print()
            print(f"Repository:       {result.full_name}")
            print(f"URL:              {result.url}")
            print(f"Default branch:   {result.default_branch}")
            print(f"Stars:            {result.stars:,}")
            print(f"Forks:            {result.forks:,}")
            print(f"Open issues:      {result.open_issues:,}")
            print(f"Total PRs:        {result.total_pull_requests:,}")
            print(f"Merged PRs:       {result.merged_pull_requests:,}")
            print(
                "Merged ratio:     "
                f"{result.merged_pull_request_ratio:.2%}"
            )
            print(
                "First PR:         "
                f"{result.first_pull_request_created_at}"
            )
            print(
                "Latest PR:        "
                f"{result.latest_pull_request_created_at}"
            )
            print(
                "Sufficient history:"
                f" {result.has_sufficient_history}"
            )
            print()
            print("-" * 100)
            print()


if __name__ == "__main__":
    main()