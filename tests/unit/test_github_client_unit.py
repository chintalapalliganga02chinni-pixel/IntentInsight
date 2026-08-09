"""Unit tests for the GitHub API client."""

from __future__ import annotations

import httpx

from intentinsight.infrastructure.configuration.settings import Settings
from intentinsight.infrastructure.github.client import GitHubClient


def test_list_pull_requests_returns_api_data() -> None:
    """The client should return pull requests from the GitHub API."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/example/repository/pulls"
        assert request.url.params["state"] == "all"
        assert request.url.params["page"] == "1"
        assert request.url.params["per_page"] == "100"

        return httpx.Response(
            200,
            json=[
                {
                    "number": 1,
                    "title": "Improve architecture",
                }
            ],
        )

    transport = httpx.MockTransport(handler)

    settings = Settings(
        github_token="test-token",
        github_api_url="https://api.github.com",
        github_api_version="2022-11-28",
        database_url="sqlite:///./test.db",
        log_level="INFO",
    )

    with httpx.Client(
            base_url=settings.github_api_url,
            transport=transport,
    ) as http_client:
        client = GitHubClient(
            settings,
            client=http_client,
        )

        pull_requests = client.list_pull_requests(
            owner="example",
            repository="repository",
        )

    assert len(pull_requests) == 1
    assert pull_requests[0]["number"] == 1
    assert pull_requests[0]["title"] == "Improve architecture"


def test_list_pull_request_files_returns_file_models() -> None:
    """The client should map GitHub PR file data to response models."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert (
                request.url.path
                == "/repos/example/repository/pulls/42/files"
        )
        assert request.url.params["page"] == "1"
        assert request.url.params["per_page"] == "100"

        return httpx.Response(
            200,
            json=[
                {
                    "sha": "abc123",
                    "filename": "src/example.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 4,
                    "changes": 14,
                },
                {
                    "sha": "def456",
                    "filename": "tests/test_example.py",
                    "status": "added",
                    "additions": 20,
                    "deletions": 0,
                    "changes": 20,
                },
            ],
        )

    transport = httpx.MockTransport(handler)

    settings = Settings(
        github_token="test-token",
        github_api_url="https://api.github.com",
        github_api_version="2022-11-28",
        database_url="sqlite:///./test.db",
        log_level="INFO",
    )

    with httpx.Client(
            base_url=settings.github_api_url,
            transport=transport,
    ) as http_client:
        client = GitHubClient(
            settings,
            client=http_client,
        )

        files = client.list_pull_request_files(
            owner="example",
            repository="repository",
            pull_request_number=42,
        )

    assert len(files) == 2

    assert files[0].filename == "src/example.py"
    assert files[0].status == "modified"
    assert files[0].additions == 10
    assert files[0].deletions == 4
    assert files[0].changes == 14
    assert files[0].sha == "abc123"

    assert files[1].filename == "tests/test_example.py"
    assert files[1].status == "added"