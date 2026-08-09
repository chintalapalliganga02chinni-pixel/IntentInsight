"""Unit tests for pull-request research eligibility."""

from __future__ import annotations

from datetime import datetime, timezone

from intentinsight.domain.models.pull_request import PullRequest
from intentinsight.domain.models.pull_request_eligibility import (
    EligibilityStatus,
    ExclusionReason,
)
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
    """Create a minimal pull request for testing."""
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
        commits_count=1,
        changed_files_count=1,
        additions=10,
        deletions=2,
    )


def _source_file() -> PullRequestFile:
    """Create a source-code file for testing."""
    return PullRequestFile(
        filename="src/application.py",
        status="modified",
        additions=10,
        deletions=2,
        changes=12,
        sha="abc123",
    )


def test_merged_source_changing_pr_is_eligible() -> None:
    """A merged PR with source changes should be eligible."""
    source_file = _source_file()

    summary = PullRequestFileSummary(
        files=(source_file,),
        source_files=(source_file,),
        test_files=(),
        documentation_files=(),
        configuration_files=(),
        other_files=(),
    )

    result = PullRequestEligibilityService().evaluate(
        _pull_request(),
        summary,
    )

    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.is_eligible is True
    assert result.reason is None


def test_unmerged_pr_is_excluded() -> None:
    """Unmerged pull requests should be excluded."""
    source_file = _source_file()

    summary = PullRequestFileSummary(
        files=(source_file,),
        source_files=(source_file,),
        test_files=(),
        documentation_files=(),
        configuration_files=(),
        other_files=(),
    )

    result = PullRequestEligibilityService().evaluate(
        _pull_request(merged=False),
        summary,
    )

    assert result.status == EligibilityStatus.EXCLUDED
    assert result.reason == ExclusionReason.NOT_MERGED.value


def test_pr_without_merge_commit_is_excluded() -> None:
    """A missing merge commit should exclude the PR."""
    source_file = _source_file()

    summary = PullRequestFileSummary(
        files=(source_file,),
        source_files=(source_file,),
        test_files=(),
        documentation_files=(),
        configuration_files=(),
        other_files=(),
    )

    result = PullRequestEligibilityService().evaluate(
        _pull_request(merge_commit_sha=None),
        summary,
    )

    assert result.status == EligibilityStatus.EXCLUDED
    assert result.reason == ExclusionReason.NO_MERGE_COMMIT.value


def test_pr_without_changed_files_is_excluded() -> None:
    """A PR with no changed files should be excluded."""
    summary = PullRequestFileSummary(
        files=(),
        source_files=(),
        test_files=(),
        documentation_files=(),
        configuration_files=(),
        other_files=(),
    )

    result = PullRequestEligibilityService().evaluate(
        _pull_request(),
        summary,
    )

    assert result.status == EligibilityStatus.EXCLUDED
    assert result.reason == ExclusionReason.NO_CHANGED_FILES.value


def test_documentation_only_pr_is_excluded() -> None:
    """A documentation-only PR should not enter the main dataset."""
    documentation_file = PullRequestFile(
        filename="README.md",
        status="modified",
        additions=10,
        deletions=2,
        changes=12,
        sha="abc123",
    )

    summary = PullRequestFileSummary(
        files=(documentation_file,),
        source_files=(),
        test_files=(),
        documentation_files=(documentation_file,),
        configuration_files=(),
        other_files=(),
    )

    result = PullRequestEligibilityService().evaluate(
        _pull_request(),
        summary,
    )

    assert result.status == EligibilityStatus.EXCLUDED
    assert result.reason == (
        ExclusionReason.NO_SOURCE_CODE_CHANGES.value
    )