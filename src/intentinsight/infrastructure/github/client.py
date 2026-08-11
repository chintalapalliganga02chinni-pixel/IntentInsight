"""GitHub REST API client."""

from __future__ import annotations

from typing import Any

import httpx

from intentinsight.infrastructure.configuration.settings import Settings
from intentinsight.infrastructure.github.exceptions import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
)
from intentinsight.infrastructure.github.git_comparison import (
    GitComparison,
    GitComparisonFile,
)
from intentinsight.infrastructure.github.git_tree import GitTreeEntry
from intentinsight.infrastructure.github.models import (
    PullRequestFile,
    RepositoryInfo,
)


class GitHubClient:
    """Small, focused client for the GitHub REST API."""

    def __init__(
            self,
            settings: Settings,
            client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or httpx.Client(
            base_url=settings.github_api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {settings.github_token}",
                "X-GitHub-Api-Version": settings.github_api_version,
            },
            timeout=30.0,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "GitHubClient":
        """Enter the client context manager."""
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: Any,
    ) -> None:
        """Close the client when leaving the context."""
        self.close()

    def get_authenticated_user(self) -> dict[str, Any]:
        """Verify authentication and return the authenticated user."""
        response = self._client.get("/user")

        if response.status_code == 401:
            raise GitHubAuthenticationError(
                "GitHub authentication failed. "
                "Check the configured GITHUB_TOKEN."
            )

        self._raise_for_api_error(response)

        data = response.json()

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "GitHub API returned an unexpected user response."
            )

        return data

    def get_repository(
            self,
            owner: str,
            repository: str,
    ) -> RepositoryInfo:
        """Retrieve basic repository information."""
        response = self._client.get(
            f"/repos/{owner}/{repository}",
        )

        self._raise_for_api_error(response)

        data = response.json()

        return RepositoryInfo(
            owner=owner,
            name=repository,
            full_name=data["full_name"],
            default_branch=data["default_branch"],
            private=data["private"],
            url=data["html_url"],
            stars=int(data.get("stargazers_count", 0)),
            forks=int(data.get("forks_count", 0)),
            open_issues=int(data.get("open_issues_count", 0)),
        )

    def list_pull_requests(
            self,
            owner: str,
            repository: str,
            *,
            state: str = "all",
            page: int = 1,
            per_page: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve one page of pull requests from a repository."""
        if not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100.")

        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1."
            )

        response = self._client.get(
            f"/repos/{owner}/{repository}/pulls",
            params={
                "state": state,
                "page": page,
                "per_page": per_page,
                "sort": "created",
                "direction": "asc",
            },
        )

        self._raise_for_api_error(response)

        data = response.json()

        if not isinstance(data, list):
            raise GitHubAPIError(
                "GitHub API returned an unexpected pull request response."
            )

        return data

    def get_pull_request(
            self,
            owner: str,
            repository: str,
            pull_request_number: int,
    ) -> dict[str, Any]:
        """Retrieve detailed information about one pull request."""
        if pull_request_number < 1:
            raise ValueError(
                "pull_request_number must be greater than or equal to 1."
            )

        response = self._client.get(
            f"/repos/{owner}/{repository}/pulls/"
            f"{pull_request_number}",
        )

        self._raise_for_api_error(response)

        data = response.json()

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "GitHub API returned an unexpected pull request response."
            )

        return data

    def list_pull_request_files(
            self,
            owner: str,
            repository: str,
            pull_request_number: int,
            *,
            page: int = 1,
            per_page: int = 100,
    ) -> list[PullRequestFile]:
        """Retrieve one page of files changed by a pull request."""
        if pull_request_number < 1:
            raise ValueError(
                "pull_request_number must be greater than or equal to 1."
            )

        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1."
            )

        if not 1 <= per_page <= 100:
            raise ValueError(
                "per_page must be between 1 and 100."
            )

        response = self._client.get(
            f"/repos/{owner}/{repository}/pulls/"
            f"{pull_request_number}/files",
            params={
                "page": page,
                "per_page": per_page,
            },
        )

        self._raise_for_api_error(response)

        data = response.json()

        if not isinstance(data, list):
            raise GitHubAPIError(
                "GitHub API returned an unexpected pull request "
                "files response."
            )

        return [
            PullRequestFile(
                filename=str(item["filename"]),
                status=str(item["status"]),
                additions=int(item.get("additions", 0)),
                deletions=int(item.get("deletions", 0)),
                changes=int(item.get("changes", 0)),
                sha=str(item["sha"]),
            )
            for item in data
        ]

    def get_commit_tree(
            self,
            owner: str,
            repository: str,
            commit_sha: str,
            *,
            recursive: bool = True,
    ) -> list[GitTreeEntry]:
        """Retrieve the Git tree associated with a commit."""

        if not commit_sha:
            raise ValueError("commit_sha must not be empty.")

        params: dict[str, str] = {}

        if recursive:
            params["recursive"] = "1"

        response = self._client.get(
            f"/repos/{owner}/{repository}/git/trees/{commit_sha}",
            params=params,
        )

        self._raise_for_api_error(response)

        data = response.json()

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "GitHub API returned an unexpected Git tree response."
            )

        tree = data.get("tree")

        if not isinstance(tree, list):
            raise GitHubAPIError(
                "GitHub API returned an unexpected Git tree payload."
            )

        entries: list[GitTreeEntry] = []

        for item in tree:
            if not isinstance(item, dict):
                continue

            path = item.get("path")
            mode = item.get("mode")
            entry_type = item.get("type")
            sha = item.get("sha")

            if not all(
                    isinstance(value, str)
                    for value in (
                            path,
                            mode,
                            entry_type,
                            sha,
                    )
            ):
                continue

            size = item.get("size")

            entries.append(
                GitTreeEntry(
                    path=path,
                    mode=mode,
                    entry_type=entry_type,
                    sha=sha,
                    size=int(size) if size is not None else None,
                )
            )

        return entries

    def compare_commits(
            self,
            owner: str,
            repository: str,
            base_sha: str,
            head_sha: str,
    ) -> GitComparison:
        """Compare two Git references using GitHub's comparison API."""

        if not base_sha:
            raise ValueError("base_sha must not be empty.")

        if not head_sha:
            raise ValueError("head_sha must not be empty.")

        response = self._client.get(
            f"/repos/{owner}/{repository}/compare/"
            f"{base_sha}...{head_sha}",
        )

        self._raise_for_api_error(response)

        data = response.json()

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "GitHub API returned an unexpected comparison response."
            )

        merge_base_commit = data.get("merge_base_commit") or {}

        if not isinstance(merge_base_commit, dict):
            merge_base_commit = {}

        merge_base_sha = merge_base_commit.get("sha")

        raw_files = data.get("files") or []

        if not isinstance(raw_files, list):
            raise GitHubAPIError(
                "GitHub API returned an unexpected comparison files "
                "response."
            )

        files: list[GitComparisonFile] = []

        for item in raw_files:
            if not isinstance(item, dict):
                continue

            filename = item.get("filename")
            status = item.get("status")
            sha = item.get("sha")

            if not isinstance(filename, str):
                continue

            if not isinstance(status, str):
                continue

            if not isinstance(sha, str):
                continue

            previous_filename = item.get("previous_filename")

            if previous_filename is not None and not isinstance(
                    previous_filename,
                    str,
            ):
                previous_filename = None

            files.append(
                GitComparisonFile(
                    filename=filename,
                    status=status,
                    additions=int(item.get("additions", 0)),
                    deletions=int(item.get("deletions", 0)),
                    changes=int(item.get("changes", 0)),
                    sha=sha,
                    previous_filename=previous_filename,
                )
            )

        return GitComparison(
            base_sha=base_sha,
            head_sha=head_sha,
            merge_base_sha=(
                str(merge_base_sha)
                if merge_base_sha
                else None
            ),
            status=str(data.get("status") or "unknown"),
            ahead_by=int(data.get("ahead_by", 0)),
            behind_by=int(data.get("behind_by", 0)),
            files=tuple(files),
        )

    @staticmethod
    def _raise_for_api_error(
            response: httpx.Response,
    ) -> None:
        """Translate HTTP failures into application-specific exceptions."""
        if response.status_code == 401:
            raise GitHubAuthenticationError(
                "GitHub authentication failed."
            )

        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")

            if remaining == "0":
                raise GitHubRateLimitError(
                    "GitHub API rate limit has been exceeded."
                )

            raise GitHubAPIError(
                "GitHub API returned HTTP 403 Forbidden."
            )

        if response.status_code >= 400:
            raise GitHubAPIError(
                f"GitHub API request failed with HTTP "
                f"{response.status_code}: {response.text[:500]}"
            )