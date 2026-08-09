"""Unit tests for pull-request file mining."""

from __future__ import annotations

from unittest.mock import Mock

from intentinsight.application.services.pull_request_file_miner import (
    PullRequestFileMiner,
)
from intentinsight.domain.models.pull_request_file_summary import (
    PullRequestFileSummary,
)

from intentinsight.infrastructure.github.client import GitHubClient
from intentinsight.infrastructure.github.models import PullRequestFile


def _file(filename: str) -> PullRequestFile:
    """Create a minimal changed-file model."""
    return PullRequestFile(
        filename=filename,
        status="modified",
        additions=10,
        deletions=2,
        changes=12,
        sha="abc123",
    )


def test_miner_classifies_pull_request_files() -> None:
    """The miner should aggregate files by research category."""
    github_client = Mock(spec=GitHubClient)

    github_client.list_pull_request_files.return_value = [
        _file("src/application.py"),
        _file("tests/test_application.py"),
        _file("README.md"),
        _file("pyproject.toml"),
        _file("assets/logo.png"),
    ]

    miner = PullRequestFileMiner(github_client)

    result = miner.mine_pull_request_files(
        owner="example",
        repository="repository",
        pull_request_number=42,
    )

    assert result.total_files == 5
    assert result.source_file_count == 1
    assert result.test_file_count == 1
    assert result.documentation_file_count == 1
    assert result.configuration_file_count == 1
    assert result.other_file_count == 1
    assert result.has_source_code_changes is True

    assert result.source_files[0].filename == "src/application.py"
    assert result.test_files[0].filename == (
        "tests/test_application.py"
    )
    assert result.documentation_files[0].filename == "README.md"


def test_miner_handles_multiple_file_pages() -> None:
    """The miner should retrieve all file pages."""
    github_client = Mock(spec=GitHubClient)

    github_client.list_pull_request_files.side_effect = [
        [
            _file("src/application.py"),
            _file("src/service.py"),
        ],
        [
            _file("tests/test_application.py"),
        ],
        [],
    ]

    miner = PullRequestFileMiner(github_client)

    result = miner.mine_pull_request_files(
        owner="example",
        repository="repository",
        pull_request_number=42,
        per_page=2,
    )

    assert result.total_files == 3
    assert result.source_file_count == 2
    assert result.test_file_count == 1

    assert github_client.list_pull_request_files.call_count == 2