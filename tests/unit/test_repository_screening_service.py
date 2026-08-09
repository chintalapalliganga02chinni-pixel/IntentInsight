"""Unit tests for repository screening."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)
from intentinsight.application.services.repository_screening_service import (
    RepositoryScreeningService,
)
from intentinsight.domain.models import PullRequest
from intentinsight.infrastructure.github.models import RepositoryInfo


def _make_pull_request(
        number: int,
        *,
        merged: bool,
        created_at: str,
) -> PullRequest:
    """Create a minimal pull request for screening tests."""
    timestamp = datetime.fromisoformat(
        created_at.replace("Z", "+00:00"),
    )

    return PullRequest(
        repository="example/repository",
        number=number,
        title=f"Pull request {number}",
        description="Test pull request",
        author="developer",
        state="closed" if merged else "open",
        created_at=timestamp,
        updated_at=timestamp,
        merged_at=timestamp if merged else None,
        merge_commit_sha="abc123" if merged else None,
        commits_count=1,
        changed_files_count=1,
        additions=10,
        deletions=2,
    )


def test_repository_screening_counts_merged_pull_requests() -> None:
    """Repository screening should use the complete PR mining service."""
    github_client = Mock(spec=["get_repository"])
    pull_request_miner = Mock(spec=PullRequestMiner)

    github_client.get_repository.return_value = RepositoryInfo(
        owner="example",
        name="repository",
        full_name="example/repository",
        default_branch="main",
        private=False,
        url="https://github.com/example/repository",
        stars=100,
        forks=20,
        open_issues=5,
    )

    pull_request_miner.mine_repository.return_value = [
        _make_pull_request(
            1,
            merged=True,
            created_at="2025-01-01T10:00:00Z",
        ),
        _make_pull_request(
            2,
            merged=False,
            created_at="2025-02-01T10:00:00Z",
        ),
        _make_pull_request(
            3,
            merged=True,
            created_at="2025-03-01T10:00:00Z",
        ),
    ]

    service = RepositoryScreeningService(
        github_client=github_client,
        pull_request_miner=pull_request_miner,
    )

    result = service.screen_repository(
        owner="example",
        repository="repository",
    )

    assert result.total_pull_requests == 3
    assert result.merged_pull_requests == 2
    assert result.first_pull_request_created_at == (
        "2025-01-01T10:00:00+00:00"
    )
    assert result.latest_pull_request_created_at == (
        "2025-03-01T10:00:00+00:00"
    )
    assert result.merged_pull_request_ratio == 2 / 3
    assert result.has_sufficient_history is False

    pull_request_miner.mine_repository.assert_called_once_with(
        owner="example",
        repository="repository",
        state="all",
        per_page=100,
    )