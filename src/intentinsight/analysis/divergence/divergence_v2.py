"""Intent–Impact Divergence V2 research metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DivergenceProfile:
    semantic_alignment: float
    semantic_divergence: float

    scope_anomaly: float
    dispersion_anomaly: float
    historical_novelty: float
    boundary_anomaly: float

    observed_files: int
    observed_modules: int
    observed_packages: int
    observed_changes: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "semantic_alignment": self.semantic_alignment,
            "semantic_divergence": self.semantic_divergence,
            "scope_anomaly": self.scope_anomaly,
            "dispersion_anomaly": self.dispersion_anomaly,
            "historical_novelty": self.historical_novelty,
            "boundary_anomaly": self.boundary_anomaly,
            "observed_files": self.observed_files,
            "observed_modules": self.observed_modules,
            "observed_packages": self.observed_packages,
            "observed_changes": self.observed_changes,
        }


def cosine_to_divergence(similarity: float) -> float:
    """Convert cosine similarity into semantic divergence."""
    similarity = max(-1.0, min(1.0, float(similarity)))
    return 1.0 - similarity


def robust_z(value: float, median: float, mad: float) -> float:
    """Robust standardized anomaly using median absolute deviation."""
    if mad <= 0:
        return 0.0
    return 0.67448975 * (value - median) / mad


def log1p_value(value: float) -> float:
    """Stable logarithmic transformation for non-negative quantities."""
    return math.log1p(max(0.0, float(value)))
