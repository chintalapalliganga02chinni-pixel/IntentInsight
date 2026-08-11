"""Structural profile of historically reconstructed PR impact."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HistoricalImpactModule:
    """Structural impact attributed to one module."""

    module: str
    package: str
    file_count: int
    additions: int
    deletions: int
    changes: int
    statuses: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalImpactProfile:
    """Structural profile derived from PR-attributed file changes."""

    modules: tuple[HistoricalImpactModule, ...]

    non_python_file_count: int
    non_python_additions: int
    non_python_deletions: int
    non_python_changes: int

    @property
    def module_count(self) -> int:
        """Return the number of affected Python modules."""
        return len(self.modules)

    @property
    def package_count(self) -> int:
        """Return the number of distinct affected packages."""
        return len({
            module.package
            for module in self.modules
        })

    @property
    def total_files(self) -> int:
        """Return the total number of changed files."""
        return (
                sum(
                    module.file_count
                    for module in self.modules
                )
                + self.non_python_file_count
        )

    @property
    def additions(self) -> int:
        """Return total additions across all changed files."""
        return (
                sum(
                    module.additions
                    for module in self.modules
                )
                + self.non_python_additions
        )

    @property
    def deletions(self) -> int:
        """Return total deletions across all changed files."""
        return (
                sum(
                    module.deletions
                    for module in self.modules
                )
                + self.non_python_deletions
        )

    @property
    def total_changes(self) -> int:
        """Return total changes across all changed files."""
        return (
                sum(
                    module.changes
                    for module in self.modules
                )
                + self.non_python_changes
        )