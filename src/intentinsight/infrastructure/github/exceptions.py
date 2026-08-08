"""Exceptions raised by the GitHub infrastructure layer."""

from __future__ import annotations


class GitHubError(Exception):
    """Base exception for GitHub integration errors."""


class GitHubAuthenticationError(GitHubError):
    """Raised when GitHub authentication fails."""


class GitHubAPIError(GitHubError):
    """Raised when the GitHub API returns an unexpected response."""


class GitHubRateLimitError(GitHubAPIError):
    """Raised when the GitHub API rate limit has been exceeded."""