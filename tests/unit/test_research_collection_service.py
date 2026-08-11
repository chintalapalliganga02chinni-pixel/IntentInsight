"""Unit tests for research collection service."""

from __future__ import annotations

from unittest.mock import Mock

from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)
from intentinsight.application.services.research_collection_service import (
    ResearchCollectionService,
)
from intentinsight.application.services.research_dataset_builder import (
    ResearchDatasetBuilder,
)
from intentinsight.domain.models.research_record import ResearchRecord
from intentinsight.infrastructure.database.repositories import (
    CollectionRunRepository,
    PullRequestRepository,
    ResearchRecordRepository,
)


def test_collection_service_persists_mined_research_records() -> None:
    """The collection service should persist mined research records."""

    pull_request_miner = Mock(spec=PullRequestMiner)
    dataset_builder = Mock(spec=ResearchDatasetBuilder)
    pull_request_repository = Mock(spec=PullRequestRepository)
    research_record_repository = Mock(spec=ResearchRecordRepository)
    collection_run_repository = Mock(spec=CollectionRunRepository)

    # This is a new research record, so the collection service
    # should process it rather than skip it.
    research_record_repository.exists.return_value = False

    # The repository is responsible for reporting the current
    # dataset totals after collection.
    research_record_repository.count_eligible.return_value = 1
    research_record_repository.count_excluded.return_value = 0

    pull_request = Mock()
    pull_request_miner.mine_repository.return_value = [
        pull_request
    ]

    record = ResearchRecord(
        repository="example/repository",
        pull_request_number=42,
        title="Improve architecture",
        description="Improve application structure.",
        author="developer",
        is_merged=True,
        merge_commit_sha="abc123",
        total_files=2,
        source_file_count=1,
        test_file_count=1,
        documentation_file_count=0,
        configuration_file_count=0,
        other_file_count=0,
        additions=25,
        deletions=8,
        commits_count=3,
        eligible=True,
        exclusion_reason=None,
    )

    dataset_builder.build_record.return_value = record
    collection_run_repository.save.return_value = 7

    service = ResearchCollectionService(
        pull_request_miner=pull_request_miner,
        dataset_builder=dataset_builder,
        pull_request_repository=pull_request_repository,
        research_record_repository=research_record_repository,
        collection_run_repository=collection_run_repository,
    )

    summary = service.collect(
        owner="example",
        repository="repository",
        repository_id=1,
    )

    assert summary.pull_requests_discovered == 1
    assert summary.records_created == 1
    assert summary.records_skipped == 0
    assert summary.eligible_records == 1
    assert summary.excluded_records == 0
    assert summary.collection_run_id == 7

    pull_request_miner.mine_repository.assert_called_once_with(
        owner="example",
        repository="repository",
        state="all",
    )

    research_record_repository.exists.assert_called_once_with(
        repository_id=1,
        pull_request_number=pull_request.number,
    )

    pull_request_repository.save.assert_called_once_with(
        repository_id=1,
        pull_request=pull_request,
    )

    dataset_builder.build_record.assert_called_once_with(
        pull_request,
    )

    research_record_repository.save.assert_called_once_with(
        repository_id=1,
        record=record,
    )

    collection_run_repository.save.assert_called_once()


def test_collection_service_skips_existing_research_records() -> None:
    """Existing research records should not be mined again."""

    pull_request_miner = Mock(spec=PullRequestMiner)
    dataset_builder = Mock(spec=ResearchDatasetBuilder)
    pull_request_repository = Mock(spec=PullRequestRepository)
    research_record_repository = Mock(
        spec=ResearchRecordRepository
    )
    collection_run_repository = Mock(
        spec=CollectionRunRepository
    )

    pull_request = Mock()
    pull_request.number = 42

    pull_request_miner.mine_repository.return_value = [
        pull_request
    ]

    # This record already exists in the database.
    research_record_repository.exists.return_value = True

    research_record_repository.count_eligible.return_value = 1
    research_record_repository.count_excluded.return_value = 0
    collection_run_repository.save.return_value = 8

    service = ResearchCollectionService(
        pull_request_miner=pull_request_miner,
        dataset_builder=dataset_builder,
        pull_request_repository=pull_request_repository,
        research_record_repository=research_record_repository,
        collection_run_repository=collection_run_repository,
    )

    summary = service.collect(
        owner="example",
        repository="repository",
        repository_id=1,
    )

    assert summary.pull_requests_discovered == 1
    assert summary.records_created == 0
    assert summary.records_skipped == 1
    assert summary.eligible_records == 1
    assert summary.excluded_records == 0
    assert summary.collection_run_id == 8

    pull_request_repository.save.assert_not_called()
    dataset_builder.build_record.assert_not_called()
    research_record_repository.save.assert_not_called()

    collection_run_repository.save.assert_called_once()