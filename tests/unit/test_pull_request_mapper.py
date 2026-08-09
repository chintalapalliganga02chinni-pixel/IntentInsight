"""Tests for GitHub pull request mapping."""

from intentinsight.infrastructure.github.pull_request_mapper import (
    map_pull_request,
)


def test_github_pull_request_is_mapped_to_domain_model() -> None:
    """GitHub pull request data is converted correctly."""
    data = {
        "number": 123,
        "title": "Improve dependency handling",
        "body": "Refactor dependency resolution.",
        "user": {
            "login": "developer",
        },
        "state": "closed",
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-11T12:00:00Z",
        "merged_at": "2026-01-11T12:30:00Z",
        "merge_commit_sha": "abc123",
        "commits": 4,
        "changed_files": 7,
        "additions": 120,
        "deletions": 50,
    }

    pull_request = map_pull_request(
        repository="example/repository",
        data=data,
    )

    assert pull_request.number == 123
    assert pull_request.title == "Improve dependency handling"
    assert pull_request.description == "Refactor dependency resolution."
    assert pull_request.author == "developer"
    assert pull_request.is_merged is True
    assert pull_request.commits_count == 4
    assert pull_request.changed_files_count == 7
    assert pull_request.additions == 120
    assert pull_request.deletions == 50


def test_missing_pull_request_description_becomes_empty_string() -> None:
    """A missing PR body should not prevent mapping."""
    data = {
        "number": 124,
        "title": "Documentation update",
        "body": None,
        "user": {
            "login": "developer",
        },
        "state": "open",
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-10T10:00:00Z",
        "merged_at": None,
        "merge_commit_sha": None,
        "commits": 1,
        "changed_files": 1,
        "additions": 10,
        "deletions": 2,
    }

    pull_request = map_pull_request(
        repository="example/repository",
        data=data,
    )

    assert pull_request.description == ""
    assert pull_request.is_merged is False