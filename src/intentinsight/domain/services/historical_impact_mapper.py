"""Map GitHub commit comparisons into historical PR impact."""

from __future__ import annotations

from pathlib import PurePosixPath

from intentinsight.analysis.structural.module_path import (
    filename_to_module,
    normalize_filename,
)
from intentinsight.domain.models.historical_impact import (
    HistoricalImpact,
    HistoricalImpactFile,
)
from intentinsight.infrastructure.github.git_comparison import (
    GitComparison,
)


def path_to_module(path: str) -> str | None:
    """Map a Python repository path to a module identity.

    Non-Python files are intentionally excluded from the module profile.
    The canonical path normalization/module conversion remains owned by
    the structural analysis layer.
    """

    normalized = normalize_filename(path)

    if not normalized:
        return None

    suffix = PurePosixPath(normalized).suffix.lower()

    if suffix not in {".py", ".pyi"}:
        return None

    return filename_to_module(normalized)


def module_to_package(module: str) -> str:
    """Return the parent package of a module.

    A top-level module is its own package identity.
    """

    if not module:
        return "<root>"

    if "." not in module:
        return module

    return module.rsplit(".", 1)[0]


def comparison_to_historical_impact(
    *,
    repository: str,
    pull_request_number: int,
    comparison: GitComparison,
) -> HistoricalImpact:
    """Convert a real GitHub commit comparison into HistoricalImpact."""

    files = tuple(
        HistoricalImpactFile(
            filename=file.filename,
            status=file.status,
            additions=file.additions,
            deletions=file.deletions,
            changes=file.changes,
            sha=file.sha,
            previous_filename=file.previous_filename,
        )
        for file in comparison.files
    )

    return HistoricalImpact(
        repository=repository,
        pull_request_number=pull_request_number,
        base_sha=comparison.base_sha,
        head_sha=comparison.head_sha,
        merge_base_sha=comparison.merge_base_sha,
        comparison_status=comparison.status,
        ahead_by=comparison.ahead_by,
        behind_by=comparison.behind_by,
        files=files,
    )
