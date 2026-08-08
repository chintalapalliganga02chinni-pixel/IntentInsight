"""Integration tests for the GitHub client."""

from __future__ import annotations

import pytest

from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.github.client import GitHubClient


@pytest.mark.integration
def test_github_authentication() -> None:
    """Verify that the configured GitHub token can authenticate."""
    try:
        settings = load_settings()
    except ValueError as exc:
        pytest.skip(str(exc))

    with GitHubClient(settings) as client:
        user = client.get_authenticated_user()

    assert isinstance(user, dict)
    assert user.get("login")

@pytest.mark.integration
def test_github_repository_access() -> None:
    """Verify that the client can retrieve repository metadata."""
    try:
        settings = load_settings()
    except ValueError as exc:
        pytest.skip(str(exc))

    with GitHubClient(settings) as client:
        repository = client.get_repository(
            owner="chintalapalliganga02chinni-pixel",
            repository="IntentInsight",
        )

    assert repository.full_name == (
        "chintalapalliganga02chinni-pixel/IntentInsight"
    )
    assert repository.default_branch == "main"
    assert repository.private is False