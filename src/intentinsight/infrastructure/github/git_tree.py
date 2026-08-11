"""Models for GitHub Git tree responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GitTreeEntry:
    """One entry in a Git tree."""

    path: str
    mode: str
    entry_type: str
    sha: str
    size: int | None = None