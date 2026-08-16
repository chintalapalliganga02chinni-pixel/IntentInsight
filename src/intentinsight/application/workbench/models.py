"""Application read models for the IntentInsight Research Workbench."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactDescriptor:
    key: str
    filename: str
    path: Path
    exists: bool


@dataclass(frozen=True)
class PredictiveEvaluation:
    baseline_roc_auc: float
    divergence_roc_auc: float
    roc_auc_difference: float
    bootstrap_ci_lower: float
    bootstrap_ci_upper: float
    paired_permutation_p_value: float


@dataclass(frozen=True)
class HistoricalComparison:
    current_mean: float
    current_median: float
    historical_mean: float
    historical_median: float
    correlation: float
    identical_profiles: int
    historical_higher: int
    historical_lower: int
    total_pull_requests: int


@dataclass(frozen=True)
class NullModelSummary:
    permutations: int
    observed_similarity: float
    random_mean_similarity: float
    random_std: float
    percentile_2_5: float
    percentile_97_5: float
    observed_minus_random: float
    standardized_effect: float
    permutation_p_value: float


@dataclass(frozen=True)
class StudyOverview:
    eligible_pull_requests: int
    downstream_observations: int
    right_censored_excluded: int
    observed_rework: int
    observed_no_rework: int
    current_divergence_mean: float
    current_divergence_median: float
    historical: HistoricalComparison
    reconstruction_equivalent_pull_requests: int | None
    reconstruction_total_pull_requests: int | None
    null_model: NullModelSummary
    predictive_evaluation: PredictiveEvaluation


@dataclass(frozen=True)
class PullRequestAnalysis:
    repository_id: int
    repository_name: str
    number: int
    title: str
    description: str
    author: str
    state: str
    created_at: str
    updated_at: str
    merged_at: str | None
    merge_commit_sha: str | None
    base_sha: str | None
    head_sha: str | None
    commits_count: int
    changed_files_count: int
    additions: int
    deletions: int
    intent_text: str | None
    intent_model: str | None
    intent_embedding_dimension: int | None
    structural_text: str | None
    structural_model: str | None
    module_count: int | None
    module_profile: tuple[dict[str, Any], ...]
    divergence: float | None
    similarity: float | None
    module_entropy: float | None
    module_concentration: float | None
    top_module_weight: float | None
    package_count: int | None
    cross_package_spread: int | None
    rework_90d: bool | None
    rework_pr_count_90d: int | None
    reworked_module_count_90d: int | None
    days_to_first_rework: float | None
    historical_validation: dict[str, Any] | None
    changed_files: tuple[dict[str, Any], ...]
