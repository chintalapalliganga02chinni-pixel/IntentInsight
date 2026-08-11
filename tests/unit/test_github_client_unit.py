"""Unit tests for the GitHub API client."""

from __future__ import annotations

import httpx

from intentinsight.infrastructure.configuration.settings import Settings
from intentinsight.infrastructure.github.client import GitHubClient


def _settings() -> Settings:
    """Create test settings."""
    return Settings(
        github_token="test-token",
        github_api_url="https://api.github.com",
        github_api_version="2022-11-28",
        database_url="sqlite:///./test.db",
        log_level="INFO",
    )


def test_list_pull_requests_returns_api_data() -> None:
    """The client should return pull requests from the GitHub API."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/repos/example/repository/pulls"
        )
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

    with httpx.Client(
            base_url="https://api.github.com",
            transport=transport,
    ) as http_client:
        client = GitHubClient(
            _settings(),
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
        assert request.url.path == (
            "/repos/example/repository/pulls/42/files"
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

    with httpx.Client(
            base_url="https://api.github.com",
            transport=transport,
    ) as http_client:
        client = GitHubClient(
            _settings(),
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


def test_get_pull_request_returns_detailed_api_data() -> None:
    """The client should retrieve detailed pull-request metadata."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/repos/example/repository/pulls/42"
        )

        return httpx.Response(
            200,
            json={
                "number": 42,
                "title": "Improve architecture",
                "merged_at": "2026-01-02T00:00:00Z",
                "merge_commit_sha": "abc123",
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
            base_url="https://api.github.com",
            transport=transport,
    ) as http_client:
        client = GitHubClient(
            _settings(),
            client=http_client,
        )

        pull_request = client.get_pull_request(
            owner="example",
            repository="repository",
            pull_request_number=42,
        )

    assert pull_request["number"] == 42
    assert pull_request["merged_at"] == (
        "2026-01-02T00:00:00Z"
    )
    assert pull_request["merge_commit_sha"] == "abc123"


def test_get_commit_tree_returns_tree_entries() -> None:
    """The client should retrieve and map a Git commit tree."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/repos/example/repository/git/trees/abc123"
        )
        assert request.url.params["recursive"] == "1"

        return httpx.Response(
            200,
            json={
                "sha": "abc123",
                "tree": [
                    {
                        "path": "src/example.py",
                        "mode": "100644",
                        "type": "blob",
                        "sha": "blob123",
                        "size": 120,
                    },
                    {
                        "path": "src",
                        "mode": "040000",
                        "type": "tree",
                        "sha": "tree123",
                    },
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
            base_url="https://api.github.com",
            transport=transport,
    ) as http_client:
        client = GitHubClient(
            _settings(),
            client=http_client,
        )

        tree = client.get_commit_tree(
            owner="example",
            repository="repository",
            commit_sha="abc123",
        )

    assert len(tree) == 2

    assert tree[0].path == "src/example.py"
    assert tree[0].entry_type == "blob"
    assert tree[0].sha == "blob123"
    assert tree[0].size == 120

    assert tree[1].path == "src"
    assert tree[1].entry_type == "tree"
    assert tree[1].sha == "tree123"
    def test_compare_commits_returns_comparison() -> None:
        """The client should retrieve and map a GitHub comparison."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/repos/example/repository/compare/"
            "base123...head456"
        )

        return httpx.Response(
            200,
            json={
                "status": "diverged",
                "ahead_by": 5,
                "behind_by": 3,
                "merge_base_commit": {
                    "sha": "mergebase123",
                },
                "files": [
                    {
                        "filename": "src/example.py",
                        "status": "modified",
                        "additions": 5,
                        "deletions": 2,
                        "changes": 7,
                        "sha": "headfile123",
                    },
                    {
                        "filename": "src/new.py",
                        "status": "added",
                        "additions": 10,
                        "deletions": 0,
                        "changes": 10,
                        "sha": "newfile123",
                    },
                    {
                        "filename": "src/renamed.py",
                        "previous_filename": "src/old.py",
                        "status": "renamed",
                        "additions": 2,
                        "deletions": 2,
                        "changes": 4,
                        "sha": "renamed123",
                    },
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
            base_url="https://api.github.com",
            transport=transport,
    ) as http_client:
        client = GitHubClient(
            _settings(),
            client=http_client,
        )

        comparison = client.compare_commits(
            owner="example",
            repository="repository",
            base_sha="base123",
            head_sha="head456",
        )

    assert comparison.base_sha == "base123"
    assert comparison.head_sha == "head456"
    assert comparison.merge_base_sha == "mergebase123"
    assert comparison.status == "diverged"
    assert comparison.ahead_by == 5
    assert comparison.behind_by == 3

    assert len(comparison.files) == 3

    assert comparison.files[0].filename == "src/example.py"
    assert comparison.files[0].status == "modified"
    assert comparison.files[0].additions == 5
    assert comparison.files[0].deletions == 2
    assert comparison.files[0].changes == 7
    assert comparison.files[0].sha == "headfile123"
    assert comparison.files[0].previous_filename is None

    assert comparison.files[1].filename == "src/new.py"
    assert comparison.files[1].status == "added"

    assert comparison.files[2].filename == "src/renamed.py"
    assert comparison.files[2].status == "renamed"
    assert comparison.files[2].previous_filename == "src/old.py"
def test_compare_commits_returns_comparison() -> None:
    """The client should retrieve and map a GitHub comparison."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/repos/example/repository/compare/"
            "base123...head456"
        )

        return httpx.Response(
            200,
            json={
                "status": "diverged",
                "ahead_by": 5,
                "behind_by": 3,
                "merge_base_commit": {
                    "sha": "mergebase123",
                },
                "files": [
                    {
                        "filename": "src/example.py",
                        "status": "modified",
                        "additions": 5,
                        "deletions": 2,
                        "changes": 7,
                        "sha": "headfile123",
                    },
                    {
                        "filename": "src/new.py",
                        "status": "added",
                        "additions": 10,
                        "deletions": 0,
                        "changes": 10,
                        "sha": "newfile123",
                    },
                    {
                        "filename": "src/renamed.py",
                        "previous_filename": "src/old.py",
                        "status": "renamed",
                        "additions": 2,
                        "deletions": 2,
                        "changes": 4,
                        "sha": "renamed123",
                    },
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        base_url="https://api.github.com",
        transport=transport,
    ) as http_client:
        client = GitHubClient(
            _settings(),
            client=http_client,
        )

        comparison = client.compare_commits(
            owner="example",
            repository="repository",
            base_sha="base123",
            head_sha="head456",
        )

    assert comparison.base_sha == "base123"
    assert comparison.head_sha == "head456"
    assert comparison.merge_base_sha == "mergebase123"
    assert comparison.status == "diverged"
    assert comparison.ahead_by == 5
    assert comparison.behind_by == 3

    assert len(comparison.files) == 3

    assert comparison.files[0].filename == "src/example.py"
    assert comparison.files[0].status == "modified"
    assert comparison.files[0].additions == 5
    assert comparison.files[0].deletions == 2
    assert comparison.files[0].changes == 7
    assert comparison.files[0].sha == "headfile123"
    assert comparison.files[0].previous_filename is None

    assert comparison.files[1].filename == "src/new.py"
    assert comparison.files[1].status == "added"

    assert comparison.files[2].filename == "src/renamed.py"
    assert comparison.files[2].status == "renamed"
    assert comparison.files[2].previous_filename == "src/old.py"