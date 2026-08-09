"""Tests for the pull request domain model."""

from datetime import datetime, timezone

from intentinsight.domain.models import PullRequest


def test_merged_pull_request_is_detected() -> None:
    """A pull request with a merge timestamp is considered merged."""
    pull_request = PullRequest(
        repository="example/repository",
        number=42,
        title="Improve dependency handling",
        description="Refactor dependency resolution.",
        author="developer",
        state="closed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        merged_at=datetime.now(timezone.utc),
        merge_commit_sha="abc123",
        commits_count=3,
        changed_files_count=5,
        additions=100,
        deletions=40,
    )

    assert pull_request.is_merged is True


def test_unmerged_pull_request_is_detected() -> None:
    """A pull request without a merge timestamp is not merged."""
    now = datetime.now(timezone.utc)

    pull_request = PullRequest(
        repository="example/repository",
        number=43,
        title="Update documentation",
        description="Improve documentation.",
        author="developer",
        state="open",
        created_at=now,
        updated_at=now,
        merged_at=None,
        merge_commit_sha=None,
        commits_count=1,
        changed_files_count=1,
        additions=10,
        deletions=2,
    )

    assert pull_request.is_merged is False