"""Unit tests for research dataset construction."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

from intentinsight.application.services.pull_request_file_miner import (
    PullRequestFileMiner,
)
from intentinsight.application.services.research_dataset_builder import (
    ResearchDatasetBuilder,
)
from intentinsight.domain.models.pull_request import PullRequest
from intentinsight.domain.models.pull_request_file_summary import (
    PullRequestFileSummary,
)
from intentinsight.domain.services.pull_request_eligibility_service import (
    PullRequestEligibilityService,
)
from intentinsight.infrastructure.github.models import PullRequestFile


def _pull_request(
        *,
        merged: bool = True,
        merge_commit_sha: str | None = "abc123",
) -> PullRequest:
    """Create a representative pull request."""
    return PullRequest(
        repository="example/repository",
        number=42,
        title="Improve architecture",
        description="Improve application structure.",
        author="developer",
        state="closed" if merged else "open",
        created_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        updated_at=datetime(
            2026,
            1,
            2,
            tzinfo=timezone.utc,
        ),
        merged_at=(
            datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            )
            if merged
            else None
        ),
        merge_commit_sha=merge_commit_sha,
        commits_count=3,
        changed_files_count=2,
        additions=25,
        deletions=8,
    )


def _source_file() -> PullRequestFile:
    """Create a representative source file."""
    return PullRequestFile(
        filename="src/application.py",
        status="modified",
        additions=20,
        deletions=5,
        changes=25,
        sha="file123",
    )


def _source_file_summary() -> PullRequestFileSummary:
    """Create a representative source-file summary."""
    source_file = _source_file()

    return PullRequestFileSummary(
        files=(source_file,),
        source_files=(source_file,),
        test_files=(),
        documentation_files=(),
        configuration_files=(),
        other_files=(),
    )


def test_builder_creates_eligible_research_record() -> None:
    """The builder should combine PR and file-level evidence."""
    file_miner = Mock(spec=PullRequestFileMiner)

    file_miner.mine_pull_request_files.return_value = (
        _source_file_summary()
    )

    builder = ResearchDatasetBuilder(
        file_miner=file_miner,
        eligibility_service=PullRequestEligibilityService(),
    )

    record = builder.build_record(
        _pull_request()
    )

    assert record.repository == "example/repository"
    assert record.pull_request_number == 42
    assert record.title == "Improve architecture"
    assert record.total_files == 1
    assert record.source_file_count == 1
    assert record.additions == 25
    assert record.deletions == 8
    assert record.commits_count == 3
    assert record.eligible is True
    assert record.exclusion_reason is None

    file_miner.mine_pull_request_files.assert_called_once_with(
        owner="example",
        repository="repository",
        pull_request_number=42,
    )


def test_builder_mines_files_for_merged_pr_without_merge_commit() -> None:
    """Merged PRs should be mined even without a merge commit SHA."""
    file_miner = Mock(spec=PullRequestFileMiner)

    file_miner.mine_pull_request_files.return_value = (
        _source_file_summary()
    )

    builder = ResearchDatasetBuilder(
        file_miner=file_miner,
        eligibility_service=PullRequestEligibilityService(),
    )

    pull_request = _pull_request(
        merged=True,
        merge_commit_sha=None,
    )

    record = builder.build_record(pull_request)

    assert record.is_merged is True
    assert record.merge_commit_sha is None
    assert record.total_files == 1
    assert record.source_file_count == 1
    assert record.eligible is True
    assert record.exclusion_reason is None

    file_miner.mine_pull_request_files.assert_called_once_with(
        owner="example",
        repository="repository",
        pull_request_number=42,
    )


def test_builder_does_not_mine_files_for_unmerged_pr() -> None:
    """Unmerged PRs should not trigger file API requests."""
    file_miner = Mock(spec=PullRequestFileMiner)

    builder = ResearchDatasetBuilder(
        file_miner=file_miner,
        eligibility_service=PullRequestEligibilityService(),
    )

    pull_request = _pull_request(
        merged=False,
        merge_commit_sha=None,
    )

    record = builder.build_record(pull_request)

    assert record.eligible is False
    assert record.exclusion_reason == "not_merged"
    assert record.total_files == 0
    assert record.source_file_count == 0

    file_miner.mine_pull_request_files.assert_not_called()