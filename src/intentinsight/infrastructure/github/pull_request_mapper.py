"""Mapping between GitHub API responses and domain pull requests."""

from __future__ import annotations

from datetime import datetime

from intentinsight.domain.models import PullRequest


def map_pull_request(
        repository: str,
        data: dict,
) -> PullRequest:
    """Convert a GitHub pull request response into a domain model."""
    user = data.get("user") or {}

    created_at = _parse_required_datetime(data.get("created_at"))
    updated_at = _parse_required_datetime(data.get("updated_at"))
    merged_at = _parse_optional_datetime(data.get("merged_at"))

    return PullRequest(
        repository=repository,
        number=int(data["number"]),
        title=data.get("title") or "",
        description=data.get("body") or "",
        author=user.get("login") or "unknown",
        state=data.get("state") or "unknown",
        created_at=created_at,
        updated_at=updated_at,
        merged_at=merged_at,
        merge_commit_sha=data.get("merge_commit_sha"),
        commits_count=int(data.get("commits", 0)),
        changed_files_count=int(data.get("changed_files", 0)),
        additions=int(data.get("additions", 0)),
        deletions=int(data.get("deletions", 0)),
    )


def _parse_required_datetime(value: str | None) -> datetime:
    """Parse a required GitHub ISO-8601 timestamp."""
    if not value:
        raise ValueError(
            "Expected a required GitHub timestamp but received no value."
        )

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
    """Parse an optional GitHub ISO-8601 timestamp."""
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))