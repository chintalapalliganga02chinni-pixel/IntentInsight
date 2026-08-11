"""Build research observations from mined pull requests."""

from __future__ import annotations

from intentinsight.application.services.pull_request_file_miner import (
    PullRequestFileMiner,
)
from intentinsight.domain.models.pull_request import PullRequest
from intentinsight.domain.models.pull_request_file_summary import (
    PullRequestFileSummary,
)
from intentinsight.domain.models.research_record import ResearchRecord
from intentinsight.domain.services.pull_request_eligibility_service import (
    PullRequestEligibilityService,
)


class ResearchDatasetBuilder:
    """Convert mined pull requests into research observations."""

    def __init__(
            self,
            file_miner: PullRequestFileMiner,
            eligibility_service: PullRequestEligibilityService,
    ) -> None:
        self._file_miner = file_miner
        self._eligibility_service = eligibility_service

    def build_record(
            self,
            pull_request: PullRequest,
    ) -> ResearchRecord:
        """Build one research record from a pull request."""

        owner, repository = pull_request.repository.split(
            "/",
            maxsplit=1,
        )

        file_summary = self._empty_file_summary()

        # A merged_at timestamp is sufficient to establish that the
        # pull request was merged. GitHub does not always provide
        # merge_commit_sha for historical pull requests.
        if pull_request.is_merged:
            file_summary = self._file_miner.mine_pull_request_files(
                owner=owner,
                repository=repository,
                pull_request_number=pull_request.number,
            )

        eligibility = self._eligibility_service.evaluate(
            pull_request=pull_request,
            file_summary=file_summary,
        )

        return ResearchRecord(
            repository=pull_request.repository,
            pull_request_number=pull_request.number,
            title=pull_request.title,
            description=pull_request.description,
            author=pull_request.author,
            is_merged=pull_request.is_merged,
            merge_commit_sha=pull_request.merge_commit_sha,
            total_files=file_summary.total_files,
            source_file_count=file_summary.source_file_count,
            test_file_count=file_summary.test_file_count,
            documentation_file_count=(
                file_summary.documentation_file_count
            ),
            configuration_file_count=(
                file_summary.configuration_file_count
            ),
            other_file_count=file_summary.other_file_count,
            additions=pull_request.additions,
            deletions=pull_request.deletions,
            commits_count=pull_request.commits_count,
            eligible=eligibility.is_eligible,
            exclusion_reason=eligibility.reason,
        )

    @staticmethod
    def _empty_file_summary() -> PullRequestFileSummary:
        """Create an empty file summary."""
        return PullRequestFileSummary(
            files=(),
            source_files=(),
            test_files=(),
            documentation_files=(),
            configuration_files=(),
            other_files=(),
        )