"""Unit tests for pull request mining."""

from __future__ import annotations

from unittest.mock import Mock

from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)
from intentinsight.infrastructure.github.client import GitHubClient


def _pull_request(number: int) -> dict:
    """Create a representative GitHub pull request response."""
    return {
        "number": number,
        "title": f"Pull request {number}",
        "body": "Improve application structure.",
        "user": {
            "login": "developer",
        },
        "state": "closed",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "merged_at": "2026-01-02T00:00:00Z",
        "merge_commit_sha": f"sha-{number}",
        "commits": 3,
        "changed_files": 2,
        "additions": 25,
        "deletions": 8,
    }


def test_miner_maps_pull_requests_from_single_page() -> None:
    """The miner should map pull requests from one API page."""
    github_client = Mock(spec=GitHubClient)

    github_client.list_pull_requests.return_value = [
        _pull_request(1),
        _pull_request(2),
    ]

    miner = PullRequestMiner(github_client)

    results = miner.mine_repository(
        owner="example",
        repository="repository",
        per_page=100,
    )

    assert len(results) == 2

    assert results[0].number == 1
    assert results[0].repository == "example/repository"
    assert results[0].title == "Pull request 1"

    assert results[1].number == 2
    assert results[1].repository == "example/repository"
    assert results[1].title == "Pull request 2"

    github_client.list_pull_requests.assert_called_once_with(
        owner="example",
        repository="repository",
        state="all",
        page=1,
        per_page=100,
    )


def test_miner_handles_multiple_pages() -> None:
    """The miner should continue until a short page is received."""
    github_client = Mock(spec=GitHubClient)

    github_client.list_pull_requests.side_effect = [
        [
            _pull_request(1),
            _pull_request(2),
        ],
        [
            _pull_request(3),
        ],
    ]

    miner = PullRequestMiner(github_client)

    results = miner.mine_repository(
        owner="example",
        repository="repository",
        per_page=2,
    )

    assert len(results) == 3
    assert [result.number for result in results] == [1, 2, 3]

    assert github_client.list_pull_requests.call_count == 2

    github_client.list_pull_requests.assert_any_call(
        owner="example",
        repository="repository",
        state="all",
        page=1,
        per_page=2,
    )

    github_client.list_pull_requests.assert_any_call(
        owner="example",
        repository="repository",
        state="all",
        page=2,
        per_page=2,
    )


def test_miner_does_not_require_detail_request_for_merged_pr() -> None:
    """Merged PRs should use listing metadata without extra API requests."""
    github_client = Mock(spec=GitHubClient)

    github_client.list_pull_requests.return_value = [
        {
            "number": 42,
            "title": "Improve architecture",
            "body": "Improve application structure.",
            "user": {
                "login": "developer",
            },
            "state": "closed",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
            "merged_at": "2026-01-02T00:00:00Z",
            "merge_commit_sha": None,
            "commits": 3,
            "changed_files": 2,
            "additions": 25,
            "deletions": 8,
        }
    ]

    miner = PullRequestMiner(github_client)

    results = miner.mine_repository(
        owner="example",
        repository="repository",
    )

    assert len(results) == 1
    assert results[0].number == 42
    assert results[0].repository == "example/repository"
    assert results[0].is_merged is True
    assert results[0].merge_commit_sha is None

    github_client.get_pull_request.assert_not_called()