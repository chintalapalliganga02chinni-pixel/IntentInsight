"""Historical baseline utilities for Intent–Impact Divergence V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class HistoricalBaseline:
    """Robust historical distribution for one structural measure."""

    median: float
    mad: float
    count: int

    @classmethod
    def from_values(
        cls,
        values: Iterable[float],
    ) -> "HistoricalBaseline":
        values = np.asarray(
            list(values),
            dtype=float,
        )

        values = values[np.isfinite(values)]

        if len(values) == 0:
            return cls(
                median=0.0,
                mad=0.0,
                count=0,
            )

        median = float(np.median(values))
        mad = float(
            np.median(
                np.abs(values - median)
            )
        )

        return cls(
            median=median,
            mad=mad,
            count=len(values),
        )

    def robust_z(
        self,
        value: float,
    ) -> float:
        """Return a robust standardized deviation."""

        if self.mad <= 0:
            return 0.0

        return float(
            0.67448975
            * (float(value) - self.median)
            / self.mad
        )


@dataclass(frozen=True)
class StructuralBaseline:
    """Historical baseline for a PR's structural footprint."""

    files: HistoricalBaseline
    modules: HistoricalBaseline
    packages: HistoricalBaseline
    changes: HistoricalBaseline
    dispersion: HistoricalBaseline

    @classmethod
    def from_profiles(
        cls,
        profiles: Sequence[dict[str, float]],
    ) -> "StructuralBaseline":
        """Build a baseline from historical structural profiles."""

        return cls(
            files=HistoricalBaseline.from_values(
                p["files"]
                for p in profiles
            ),
            modules=HistoricalBaseline.from_values(
                p["modules"]
                for p in profiles
            ),
            packages=HistoricalBaseline.from_values(
                p["packages"]
                for p in profiles
            ),
            changes=HistoricalBaseline.from_values(
                p["changes"]
                for p in profiles
            ),
            dispersion=HistoricalBaseline.from_values(
                p["dispersion"]
                for p in profiles
            ),
        )


def anomaly_magnitude(
    z_score: float,
) -> float:
    """Return non-negative anomaly magnitude."""

    return abs(float(z_score))
