"""Read validated research artifacts for the presentation layer."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pandas as pd

from intentinsight.application.workbench.models import (
    ArtifactDescriptor,
    HistoricalComparison,
    NullModelSummary,
    PredictiveEvaluation,
    StudyOverview,
)


DEFAULT_ARTIFACT_FILENAMES: Final[dict[str, str]] = {
    "rework_90d": "rework_90d_analysis.csv",
    "rework_models": "rework_90d_model_results.csv",
    "structural_scope": "structural_scope_analysis.csv",
    "structural_random_control": "structural_random_control_analysis.csv",
    "reconstruction": "reconstruction_validation.csv",
    "reconstruction_100": "reconstruction_validation_100.csv",
    "validated_summary": "research_summary.json",
}


class ResearchArtifactStore:
    """Stable read API over the validated study artifacts."""

    def __init__(self, artifact_root: str | Path, *, artifact_filenames: dict[str, str] | None = None) -> None:
        self._root = Path(artifact_root).resolve()
        self._filenames = {**DEFAULT_ARTIFACT_FILENAMES, **(artifact_filenames or {})}

    @property
    def root(self) -> Path:
        """Return the artifact root used by the Workbench."""
        return self._root

    def describe_artifacts(self) -> tuple[ArtifactDescriptor, ...]:
        return tuple(
            ArtifactDescriptor(key, filename, self._root / filename, (self._root / filename).is_file())
            for key, filename in self._filenames.items()
        )

    def load_rework_analysis(self) -> pd.DataFrame:
        return self._read_csv("rework_90d")

    def load_predictive_models(self) -> pd.DataFrame:
        return self._read_csv("rework_models")

    def load_structural_scope_analysis(self) -> pd.DataFrame:
        return self._read_csv("structural_scope")

    def load_structural_random_control(self) -> pd.DataFrame:
        return self._read_csv("structural_random_control")

    def load_reconstruction_validation(self) -> pd.DataFrame:
        return self._read_csv("reconstruction")

    def load_reconstruction_validation_100(self) -> pd.DataFrame:
        return self._read_csv("reconstruction_100")

    def load_validated_summary(self) -> dict[str, object]:
        path = self._path_for("validated_summary")
        if not path.is_file():
            raise FileNotFoundError(f"Validated research summary '{path.name}' was not found in {self._root}.")
        return json.loads(path.read_text(encoding="utf-8"))

    def study_overview(self) -> StudyOverview:
        scope = self.load_structural_scope_analysis()
        rework = self.load_rework_analysis()
        models = self.load_predictive_models()
        summary = self.load_validated_summary()

        if len(scope) != 703:
            raise ValueError(f"Expected 703 eligible PRs in the structural-scope artifact, found {len(scope)}.")
        if len(rework) != 702:
            raise ValueError(f"Expected 702 observable downstream cases, found {len(rework)}.")

        baseline = self._model_row(models, "baseline")
        divergence = self._model_row(models, "baseline_plus_divergence")
        historical = summary["historical_comparison"]
        null_model = summary["null_model"]
        predictive = summary["predictive_evaluation"]
        reconstruction = summary["historical_reconstruction"]

        divergence_values = pd.to_numeric(scope["full_divergence"], errors="raise")
        rework_values = pd.to_numeric(rework["rework_90d"], errors="raise")

        return StudyOverview(
            eligible_pull_requests=len(scope),
            downstream_observations=len(rework),
            right_censored_excluded=int(summary["study"]["right_censored_excluded"]),
            observed_rework=int(rework_values.sum()),
            observed_no_rework=int((rework_values == 0).sum()),
            current_divergence_mean=float(divergence_values.mean()),
            current_divergence_median=float(divergence_values.median()),
            historical=HistoricalComparison(**historical),
            reconstruction_equivalent_pull_requests=int(reconstruction["exact_module_profile_equivalence"]),
            reconstruction_total_pull_requests=int(reconstruction["eligible_pull_requests"]),
            null_model=NullModelSummary(**null_model),
            predictive_evaluation=PredictiveEvaluation(
                baseline_roc_auc=float(baseline["roc_auc"]),
                divergence_roc_auc=float(divergence["roc_auc"]),
                **predictive,
            ),
        )

    @staticmethod
    def _model_row(models: pd.DataFrame, name: str) -> pd.Series:
        rows = models.loc[models["model"] == name]
        if len(rows) != 1:
            raise ValueError(f"Expected exactly one '{name}' model row, found {len(rows)}.")
        return rows.iloc[0]

    def _read_csv(self, key: str) -> pd.DataFrame:
        path = self._path_for(key)
        if not path.is_file():
            raise FileNotFoundError(f"Research artifact '{path.name}' was not found in {self._root}.")
        return pd.read_csv(path)

    def _path_for(self, key: str) -> Path:
        try:
            return self._root / self._filenames[key]
        except KeyError as exc:
            raise KeyError(f"Unknown research artifact: {key}") from exc
