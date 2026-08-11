"""Domain model for historically reconstructed PR impact."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HistoricalImpactFile:
    """One PR-attributed file change."""

    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    sha: str
    previous_filename: str | None = None


@dataclass(frozen=True)
class HistoricalImpact:
    """Historically grounded structural impact of one pull request."""

    repository: str
    pull_request_number: int

    base_sha: str
    head_sha: str
    merge_base_sha: str | None

    comparison_status: str
    ahead_by: int
    behind_by: int

    files: tuple[HistoricalImpactFile, ...]

    @property
    def total_files(self) -> int:
        """Return the number of PR-attributed changed files."""
        return len(self.files)

    @property
    def added_file_count(self) -> int:
        """Return the number of added files."""
        return sum(
            file.status == "added"
            for file in self.files
        )

    @property
    def modified_file_count(self) -> int:
        """Return the number of modified files."""
        return sum(
            file.status == "modified"
            for file in self.files
        )

    @property
    def removed_file_count(self) -> int:
        """Return the number of removed files."""
        return sum(
            file.status == "removed"
            for file in self.files
        )

    @property
    def renamed_file_count(self) -> int:
        """Return the number of renamed files."""
        return sum(
            file.status == "renamed"
            for file in self.files
        )

    @property
    def additions(self) -> int:
        """Return total additions across PR-attributed files."""
        return sum(file.additions for file in self.files)

    @property
    def deletions(self) -> int:
        """Return total deletions across PR-attributed files."""
        return sum(file.deletions for file in self.files)

    @property
    def total_changes(self) -> int:
        """Return total changed lines across PR-attributed files."""
        return sum(file.changes for file in self.files)