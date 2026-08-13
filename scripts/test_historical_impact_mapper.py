from intentinsight.domain.services.historical_impact_mapper import (
    comparison_to_historical_impact,
)
from intentinsight.infrastructure.github.git_comparison import (
    GitComparison,
    GitComparisonFile,
)


comparison = GitComparison(
    base_sha="base123",
    head_sha="head456",
    merge_base_sha="merge789",
    status="ahead",
    ahead_by=3,
    behind_by=0,
    files=(
        GitComparisonFile(
            filename="src/example/foo.py",
            status="modified",
            additions=20,
            deletions=5,
            changes=25,
            sha="abc123",
        ),
        GitComparisonFile(
            filename="src/example/bar.py",
            status="renamed",
            additions=10,
            deletions=2,
            changes=12,
            sha="def456",
            previous_filename="src/old/bar.py",
        ),
    ),
)

impact = comparison_to_historical_impact(
    repository="example/project",
    pull_request_number=42,
    comparison=comparison,
)

assert impact.repository == "example/project"
assert impact.pull_request_number == 42
assert impact.base_sha == "base123"
assert impact.head_sha == "head456"
assert impact.merge_base_sha == "merge789"
assert impact.comparison_status == "ahead"
assert impact.ahead_by == 3
assert impact.behind_by == 0

assert impact.total_files == 2
assert impact.additions == 30
assert impact.deletions == 7
assert impact.total_changes == 37
assert impact.renamed_file_count == 1

assert impact.files[1].previous_filename == "src/old/bar.py"

print("HistoricalImpact mapper test PASSED.")
