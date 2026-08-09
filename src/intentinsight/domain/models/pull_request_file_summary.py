"""Domain model for pull-request file analysis."""

from __future__ import annotations

from dataclasses import dataclass

from intentinsight.infrastructure.github.models import PullRequestFile


@dataclass(frozen=True)
class PullRequestFileSummary:
    """Aggregated file-level information for one pull request."""

    files: tuple[PullRequestFile, ...]
    source_files: tuple[PullRequestFile, ...]
    test_files: tuple[PullRequestFile, ...]
    documentation_files: tuple[PullRequestFile, ...]
    configuration_files: tuple[PullRequestFile, ...]
    other_files: tuple[PullRequestFile, ...]

    @property
    def total_files(self) -> int:
        """Return the total number of changed files."""
        return len(self.files)

    @property
    def source_file_count(self) -> int:
        """Return the number of source-code files."""
        return len(self.source_files)

    @property
    def test_file_count(self) -> int:
        """Return the number of test files."""
        return len(self.test_files)

    @property
    def documentation_file_count(self) -> int:
        """Return the number of documentation files."""
        return len(self.documentation_files)

    @property
    def configuration_file_count(self) -> int:
        """Return the number of configuration files."""
        return len(self.configuration_files)

    @property
    def other_file_count(self) -> int:
        """Return the number of other files."""
        return len(self.other_files)

    @property
    def has_source_code_changes(self) -> bool:
        """Return whether the PR changes at least one source file."""
        return bool(self.source_files)