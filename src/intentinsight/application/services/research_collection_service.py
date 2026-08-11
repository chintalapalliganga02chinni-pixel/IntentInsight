"""Application service for reproducible research dataset collection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)
from intentinsight.application.services.research_dataset_builder import (
    ResearchDatasetBuilder,
)
from intentinsight.infrastructure.database.repositories import (
    CollectionRunRepository,
    PullRequestRepository,
    ResearchRecordRepository,
)


@dataclass(frozen=True)
class CollectionSummary:
    """Summary of one research dataset collection run."""

    pull_requests_discovered: int
    records_created: int
    records_skipped: int
    eligible_records: int
    excluded_records: int
    collection_run_id: int


class ResearchCollectionService:
    """Orchestrate reproducible research dataset collection."""

    def __init__(
            self,
            pull_request_miner: PullRequestMiner,
            dataset_builder: ResearchDatasetBuilder,
            pull_request_repository: PullRequestRepository,
            research_record_repository: ResearchRecordRepository,
            collection_run_repository: CollectionRunRepository,
    ) -> None:
        self._pull_request_miner = pull_request_miner
        self._dataset_builder = dataset_builder
        self._pull_request_repository = pull_request_repository
        self._research_record_repository = research_record_repository
        self._collection_run_repository = collection_run_repository

    def collect(
            self,
            owner: str,
            repository: str,
            repository_id: int,
            *,
            state: str = "all",
    ) -> CollectionSummary:
        """Collect and persist research observations."""

        started_at = datetime.now(timezone.utc)

        pull_requests = self._pull_request_miner.mine_repository(
            owner=owner,
            repository=repository,
            state=state,
        )

        records_created = 0
        records_skipped = 0

        for pull_request in pull_requests:
            if self._research_record_repository.exists(
                    repository_id=repository_id,
                    pull_request_number=pull_request.number,
            ):
                records_skipped += 1
                continue

            self._pull_request_repository.save(
                repository_id=repository_id,
                pull_request=pull_request,
            )

            record = self._dataset_builder.build_record(
                pull_request,
            )

            self._research_record_repository.save(
                repository_id=repository_id,
                record=record,
            )

            records_created += 1

        eligible_records = (
            self._research_record_repository.count_eligible()
        )

        excluded_records = (
            self._research_record_repository.count_excluded()
        )

        completed_at = datetime.now(timezone.utc)

        collection_run_id = self._collection_run_repository.save(
            repository_id=repository_id,
            started_at=started_at,
            completed_at=completed_at,
            status="success",
            pull_requests_discovered=len(pull_requests),
            records_created=records_created,
            eligible_records=eligible_records,
            excluded_records=excluded_records,
        )

        return CollectionSummary(
            pull_requests_discovered=len(pull_requests),
            records_created=records_created,
            records_skipped=records_skipped,
            eligible_records=eligible_records,
            excluded_records=excluded_records,
            collection_run_id=collection_run_id,
        )