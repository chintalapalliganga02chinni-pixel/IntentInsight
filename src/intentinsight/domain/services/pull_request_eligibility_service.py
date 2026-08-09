"""Research eligibility service for pull requests."""

from __future__ import annotations

from intentinsight.domain.models.pull_request import PullRequest
from intentinsight.domain.models.pull_request_eligibility import (
    ExclusionReason,
    PullRequestEligibility,
)
from intentinsight.domain.models.pull_request_file_summary import (
    PullRequestFileSummary,
)


class PullRequestEligibilityService:
    """Determine whether a pull request belongs in the main dataset."""

    def evaluate(
            self,
            pull_request: PullRequest,
            file_summary: PullRequestFileSummary,
    ) -> PullRequestEligibility:
        """Evaluate research eligibility."""

        if not pull_request.is_merged:
            return PullRequestEligibility.excluded(
                ExclusionReason.NOT_MERGED
            )

        if pull_request.merge_commit_sha is None:
            return PullRequestEligibility.excluded(
                ExclusionReason.NO_MERGE_COMMIT
            )

        if file_summary.total_files == 0:
            return PullRequestEligibility.excluded(
                ExclusionReason.NO_CHANGED_FILES
            )

        if not file_summary.has_source_code_changes:
            return PullRequestEligibility.excluded(
                ExclusionReason.NO_SOURCE_CODE_CHANGES
            )

        return PullRequestEligibility.eligible()