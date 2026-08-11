"""Unit tests for pull-request research eligibility."""

from __future__ import annotations

from datetime import datetime, timezone

from intentinsight.domain.models.pull_request import PullRequest
from intentinsight.domain.models.pull_request_eligibility import (
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
    """Create a summary containing one source-code file."""
    source_file = _source_file()

    return PullRequestFileSummary(
        files=(source_file,),
        source_files=(source_file,),
        test_files=(),
        documentation_files=(),
        configuration_files=(),
        other_files=(),
    )


def _documentation_only_summary() -> PullRequestFileSummary:
    """Create a summary containing only documentation."""
    documentation_file = PullRequestFile(
        filename="README.md",
        status="modified",
        additions=5,
        deletions=2,
        changes=7,
        sha="docs123",
    )

    return PullRequestFileSummary(
        files=(documentation_file,),
        source_files=(),
        test_files=(),
        documentation_files=(documentation_file,),
        configuration_files=(),
        other_files=(),
    )


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


def test_merged_source_changing_pr_is_eligible() -> None:
    """A merged PR changing source code should be eligible."""

    service = PullRequestEligibilityService()

    result = service.evaluate(
        pull_request=_pull_request(),
        file_summary=_source_file_summary(),
    )

    assert result.is_eligible is True
    assert result.reason is None


def test_merged_pr_without_merge_commit_is_eligible() -> None:
    """A merged PR remains eligible when merge SHA metadata is unavailable."""

    service = PullRequestEligibilityService()

    result = service.evaluate(
        pull_request=_pull_request(
            merged=True,
            merge_commit_sha=None,
        ),
        file_summary=_source_file_summary(),
    )

    assert result.is_eligible is True
    assert result.reason is None


def test_unmerged_pr_is_excluded() -> None:
    """An unmerged PR should be excluded."""

    service = PullRequestEligibilityService()

    result = service.evaluate(
        pull_request=_pull_request(
            merged=False,
            merge_commit_sha=None,
        ),
        file_summary=_source_file_summary(),
    )

    assert result.is_eligible is False
    assert result.reason == ExclusionReason.NOT_MERGED


def test_pr_without_changed_files_is_excluded() -> None:
    """A PR without changed files should be excluded."""

    service = PullRequestEligibilityService()

    result = service.evaluate(
        pull_request=_pull_request(),
        file_summary=_empty_file_summary(),
    )

    assert result.is_eligible is False
    assert result.reason == ExclusionReason.NO_CHANGED_FILES


def test_documentation_only_pr_is_excluded() -> None:
    """A PR changing only documentation should be excluded."""

    service = PullRequestEligibilityService()

    result = service.evaluate(
        pull_request=_pull_request(),
        file_summary=_documentation_only_summary(),
    )

    assert result.is_eligible is False
    assert result.reason == ExclusionReason.NO_SOURCE_CODE_CHANGES