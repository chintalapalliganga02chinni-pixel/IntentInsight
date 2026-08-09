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

        return response.json()

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

    @staticmethod
    def _raise_for_api_error(response: httpx.Response) -> None:
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