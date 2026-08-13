"""Build structural profiles from historically reconstructed PR impact."""

from __future__ import annotations

from collections import defaultdict

from intentinsight.domain.models.historical_impact import (
    HistoricalImpact,
)
from intentinsight.domain.models.historical_impact_profile import (
    HistoricalImpactModule,
    HistoricalImpactProfile,
)
from intentinsight.domain.services.historical_impact_mapper import (
    module_to_package,
    path_to_module,
)


def build_historical_impact_profile(
    impact: HistoricalImpact,
) -> HistoricalImpactProfile:
    """Build a module/package structural profile from PR impact."""

    module_data: dict[
        str,
        dict[str, object],
    ] = defaultdict(
        lambda: {
            "file_count": 0,
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "statuses": set(),
        }
    )

    non_python_file_count = 0
    non_python_additions = 0
    non_python_deletions = 0
    non_python_changes = 0

    for changed_file in impact.files:
        module = path_to_module(
            changed_file.filename
        )

        if module is None:
            non_python_file_count += 1
            non_python_additions += changed_file.additions
            non_python_deletions += changed_file.deletions
            non_python_changes += changed_file.changes
            continue

        data = module_data[module]

        data["file_count"] = (
            int(data["file_count"]) + 1
        )
        data["additions"] = (
            int(data["additions"])
            + changed_file.additions
        )
        data["deletions"] = (
            int(data["deletions"])
            + changed_file.deletions
        )
        data["changes"] = (
            int(data["changes"])
            + changed_file.changes
        )

        statuses = data["statuses"]
        assert isinstance(statuses, set)
        statuses.add(changed_file.status)

    modules: list[HistoricalImpactModule] = []

    for module in sorted(module_data):
        data = module_data[module]

        statuses = data["statuses"]
        assert isinstance(statuses, set)

        modules.append(
            HistoricalImpactModule(
                module=module,
                package=module_to_package(module),
                file_count=int(data["file_count"]),
                additions=int(data["additions"]),
                deletions=int(data["deletions"]),
                changes=int(data["changes"]),
                statuses=tuple(sorted(statuses)),
            )
        )

    return HistoricalImpactProfile(
        modules=tuple(modules),
        non_python_file_count=non_python_file_count,
        non_python_additions=non_python_additions,
        non_python_deletions=non_python_deletions,
        non_python_changes=non_python_changes,
    )
