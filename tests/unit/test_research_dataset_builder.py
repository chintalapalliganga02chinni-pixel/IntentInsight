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


def _pull_request() -> PullRequest:
    """Create a representative merged pull request."""
    return PullRequest(
        repository="example/repository",
        number=42,
        title="Improve architecture",
        description="Improve application structure.",
        author="developer",
        state="closed",
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
        merged_at=datetime(
            2026,
            1,
            2,
            tzinfo=timezone.utc,
        ),
        merge_commit_sha="abc123",
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


def test_builder_creates_eligible_research_record() -> None:
    """The builder should combine PR and file-level evidence."""
    file_miner = Mock(spec=PullRequestFileMiner)

    source_file = _source_file()

    file_miner.mine_pull_request_files.return_value = (
        PullRequestFileSummary(
            files=(source_file,),
            source_files=(source_file,),
            test_files=(),
            documentation_files=(),
            configuration_files=(),
            other_files=(),
        )
    )

    builder = ResearchDatasetBuilder(
        file_miner=file_miner,
        eligibility_service=PullRequestEligibilityService(),
    )

    record = builder.build_record(_pull_request())

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