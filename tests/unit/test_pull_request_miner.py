"""Unit tests for the pull request miner."""

from __future__ import annotations

from unittest.mock import Mock

from intentinsight.application.services.pull_request_miner import (
    PullRequestMiner,
)


def _pull_request(
        number: int,
        *,
        merged: bool = True,
) -> dict:
    """Create a minimal GitHub-style pull request response."""
    return {
        "number": number,
        "title": f"Pull request {number}",
        "body": f"Description for PR {number}.",
        "user": {
            "login": "developer",
        },
        "state": "closed" if merged else "open",
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-11T10:00:00Z",
        "merged_at": "2026-01-11T12:00:00Z" if merged else None,
        "merge_commit_sha": "abc123" if merged else None,
        "commits": 2,
        "changed_files": 3,
        "additions": 20,
        "deletions": 5,
    }


def test_miner_maps_pull_requests_from_single_page() -> None:
    """The miner should map pull requests from one API page."""
    github_client = Mock()

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
    assert results[1].number == 2

    github_client.list_pull_requests.assert_called_once_with(
        owner="example",
        repository="repository",
        state="all",
        page=1,
        per_page=100,
    )


def test_miner_handles_multiple_pages() -> None:
    """The miner should continue until a short page is received."""
    github_client = Mock()

    github_client.list_pull_requests.side_effect = [
        [_pull_request(1), _pull_request(2)],
        [_pull_request(3)],
    ]

    miner = PullRequestMiner(github_client)

    results = miner.mine_repository(
        owner="example",
        repository="repository",
        per_page=2,
    )

    assert [result.number for result in results] == [1, 2, 3]

    assert github_client.list_pull_requests.call_count == 2