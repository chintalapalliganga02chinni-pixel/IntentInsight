"""Build the IntentInsight research dataset from GitHub."""

from __future__ import annotations

import sys
from pathlib import Path


# Allow the script to import the src-layout package when executed directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from intentinsight.application.services.pull_request_file_miner import (
    PullRequestFileMiner,
)
from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)
from intentinsight.application.services.research_collection_service import (
    ResearchCollectionService,
)
from intentinsight.application.services.research_dataset_builder import (
    ResearchDatasetBuilder,
)
from intentinsight.domain.services.pull_request_eligibility_service import (
    PullRequestEligibilityService,
)
from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.database.connection import DatabaseConnection
from intentinsight.infrastructure.database.repositories import (
    CollectionRunRepository,
    PullRequestRepository,
    ResearchRecordRepository,
    RepositoryRepository,
)
from intentinsight.infrastructure.database.schema import create_schema
from intentinsight.infrastructure.github.client import GitHubClient


OWNER = "pallets"
REPOSITORY = "flask"


def _database_path(database_url: str) -> str:
    """Convert the configured SQLite URL into a filesystem path."""
    prefix = "sqlite:///"

    if not database_url.startswith(prefix):
        raise ValueError(
            "IntentInsight currently supports SQLite database URLs only."
        )

    path = database_url[len(prefix):]

    if not path:
        raise ValueError(
            "DATABASE_URL contains an empty SQLite path."
        )

    return path


def main() -> None:
    """Build the research dataset for the configured repository."""
    settings = load_settings()

    database_path = _database_path(settings.database_url)

    database = DatabaseConnection(database_path)

    with GitHubClient(settings) as github_client:
        with database.connect() as connection:
            create_schema(connection)

            repository_info = github_client.get_repository(
                owner=OWNER,
                repository=REPOSITORY,
            )

            repository_repository = RepositoryRepository(
                connection
            )

            repository_id = repository_repository.save(
                repository_info
            )

            pull_request_miner = PullRequestMiner(
                github_client
            )

            pull_request_file_miner = PullRequestFileMiner(
                github_client
            )

            eligibility_service = PullRequestEligibilityService()

            dataset_builder = ResearchDatasetBuilder(
                file_miner=pull_request_file_miner,
                eligibility_service=eligibility_service,
            )

            collection_service = ResearchCollectionService(
                pull_request_miner=pull_request_miner,
                dataset_builder=dataset_builder,
                pull_request_repository=PullRequestRepository(
                    connection
                ),
                research_record_repository=ResearchRecordRepository(
                    connection
                ),
                collection_run_repository=CollectionRunRepository(
                    connection
                ),
            )

            summary = collection_service.collect(
                owner=OWNER,
                repository=REPOSITORY,
                repository_id=repository_id,
                state="all",
            )

            print()
            print("# IntentInsight Dataset Collection")
            print()
            print(f"Repository:              {repository_info.full_name}")
            print(f"URL:                     {repository_info.url}")
            print(
                f"Default branch:         "
                f"{repository_info.default_branch}"
            )
            print(f"Stars:                   {repository_info.stars:,}")
            print(f"Forks:                   {repository_info.forks:,}")
            print()
            print(
                "Pull requests discovered: "
                f"{summary.pull_requests_discovered:,}"
            )
            print(
                "Research records created: "
                f"{summary.records_created:,}"
            )
            print(
                "Research records skipped:  "
                f"{summary.records_skipped:,}"
            )
            print(
                "Eligible records:          "
                f"{summary.eligible_records:,}"
            )
            print(
                "Excluded records:          "
                f"{summary.excluded_records:,}"
            )
            print(
                "Collection run ID:         "
                f"{summary.collection_run_id}"
            )
            print()
            print("Collection status: SUCCESS")


if __name__ == "__main__":
    main()