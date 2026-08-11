"""Tests for historical impact structural profiles."""

from intentinsight.domain.models.historical_impact import (
    HistoricalImpact,
    HistoricalImpactFile,
)
from intentinsight.domain.services.historical_impact_profile_builder import (
    build_historical_impact_profile,
)


def _impact(
    *files: HistoricalImpactFile,
) -> HistoricalImpact:
    return HistoricalImpact(
        repository="pallets/flask",
        pull_request_number=113,
        base_sha="base123",
        head_sha="head456",
        merge_base_sha="mergebase123",
        comparison_status="diverged",
        ahead_by=5,
        behind_by=3,
        files=files,
    )


def test_profile_groups_files_by_module() -> None:
    profile = build_historical_impact_profile(
        _impact(
            HistoricalImpactFile(
                filename="flask/helpers.py",
                status="modified",
                additions=5,
                deletions=1,
                changes=6,
                sha="sha1",
            ),
            HistoricalImpactFile(
                filename="flask/helpers.py",
                status="modified",
                additions=2,
                deletions=0,
                changes=2,
                sha="sha2",
            ),
        )
    )

    assert profile.module_count == 1
    assert profile.modules[0].module == "flask.helpers"
    assert profile.modules[0].package == "flask"
    assert profile.modules[0].file_count == 2
    assert profile.modules[0].additions == 7
    assert profile.modules[0].deletions == 1
    assert profile.modules[0].changes == 8


def test_profile_tracks_distinct_packages() -> None:
    profile = build_historical_impact_profile(
        _impact(
            HistoricalImpactFile(
                filename="flask/helpers.py",
                status="modified",
                additions=1,
                deletions=0,
                changes=1,
                sha="sha1",
            ),
            HistoricalImpactFile(
                filename="flask/tests/test_basic.py",
                status="modified",
                additions=2,
                deletions=0,
                changes=2,
                sha="sha2",
            ),
            HistoricalImpactFile(
                filename="docs/index.py",
                status="added",
                additions=3,
                deletions=0,
                changes=3,
                sha="sha3",
            ),
        )
    )

    assert profile.module_count == 3
    assert profile.package_count == 3


def test_profile_preserves_statuses() -> None:
    profile = build_historical_impact_profile(
        _impact(
            HistoricalImpactFile(
                filename="flask/helpers.py",
                status="modified",
                additions=1,
                deletions=1,
                changes=2,
                sha="sha1",
            ),
            HistoricalImpactFile(
                filename="flask/helpers.py",
                status="renamed",
                additions=2,
                deletions=0,
                changes=2,
                sha="sha2",
            ),
        )
    )

    assert profile.modules[0].statuses == (
        "modified",
        "renamed",
    )


def test_profile_counts_non_python_files() -> None:
    profile = build_historical_impact_profile(
        _impact(
            HistoricalImpactFile(
                filename="README",
                status="modified",
                additions=5,
                deletions=2,
                changes=7,
                sha="sha1",
            ),
            HistoricalImpactFile(
                filename="docs/index.rst",
                status="added",
                additions=10,
                deletions=0,
                changes=10,
                sha="sha2",
            ),
            HistoricalImpactFile(
                filename="flask/helpers.py",
                status="modified",
                additions=3,
                deletions=1,
                changes=4,
                sha="sha3",
            ),
        )
    )

    assert profile.module_count == 1
    assert profile.non_python_file_count == 2

    assert profile.non_python_additions == 15
    assert profile.non_python_deletions == 2
    assert profile.non_python_changes == 17

    assert profile.total_files == 3
    assert profile.additions == 18
    assert profile.deletions == 3
    assert profile.total_changes == 21