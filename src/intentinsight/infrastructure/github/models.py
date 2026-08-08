"""Response models for GitHub integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryInfo:
    """Basic information about a GitHub repository."""

    owner: str
    name: str
    full_name: str
    default_branch: str
    private: bool
    url: str