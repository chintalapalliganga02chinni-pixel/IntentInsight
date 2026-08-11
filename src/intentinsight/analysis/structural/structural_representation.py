"""Build structural representations from changed pull-request files."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from intentinsight.analysis.intent.intent_encoder import IntentEncoder
from intentinsight.analysis.structural.module_path import filename_to_module


@dataclass(frozen=True)
class ModuleImpact:
    """Aggregated impact information for one structural module."""

    module: str
    file_count: int
    additions: int
    deletions: int
    changes: int
    weight: float
    statuses: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        """Convert the module impact to JSON-compatible data."""

        return {
            "module": self.module,
            "file_count": self.file_count,
            "additions": self.additions,
            "deletions": self.deletions,
            "changes": self.changes,
            "weight": self.weight,
            "statuses": self.statuses,
        }


class StructuralRepresentationBuilder:
    """
    Construct a structural representation of a pull request.

    The representation is based only on observed changed-file data.
    It does not claim that a path is a true architectural component.
    """

    def __init__(
        self,
        encoder: IntentEncoder,
    ) -> None:
        self._encoder = encoder

    def build(
        self,
        file_rows: list[dict[str, object]],
    ) -> dict[str, object]:
        """Build one structural representation."""

        module_data: dict[str, dict[str, object]] = defaultdict(
            lambda: {
                "file_count": 0,
                "additions": 0,
                "deletions": 0,
                "changes": 0,
                "weight": 0.0,
                "statuses": Counter(),
            }
        )

        total_additions = 0
        total_deletions = 0
        total_changes = 0

        status_counts: Counter[str] = Counter()

        for row in file_rows:
            filename = str(row["filename"])
            status = str(row["status"])

            additions = int(row["additions"] or 0)
            deletions = int(row["deletions"] or 0)
            changes = int(row["changes"] or 0)

            module = filename_to_module(filename)

            # Log scaling prevents one enormous file from dominating
            # the structural representation.
            weight = 1.0 + math.log1p(max(changes, 0))

            item = module_data[module]

            item["file_count"] = int(item["file_count"]) + 1
            item["additions"] = int(item["additions"]) + additions
            item["deletions"] = int(item["deletions"]) + deletions
            item["changes"] = int(item["changes"]) + changes
            item["weight"] = float(item["weight"]) + weight

            statuses = item["statuses"]
            assert isinstance(statuses, Counter)
            statuses[status] += 1

            total_additions += additions
            total_deletions += deletions
            total_changes += changes
            status_counts[status] += 1

        impacts: list[ModuleImpact] = []

        for module, data in module_data.items():
            statuses = data["statuses"]

            assert isinstance(statuses, Counter)

            impacts.append(
                ModuleImpact(
                    module=module,
                    file_count=int(data["file_count"]),
                    additions=int(data["additions"]),
                    deletions=int(data["deletions"]),
                    changes=int(data["changes"]),
                    weight=float(data["weight"]),
                    statuses=dict(statuses),
                )
            )

        impacts.sort(
            key=lambda item: (
                -item.weight,
                item.module,
            )
        )

        modules = [impact.module for impact in impacts]

        structural_text = self._build_structural_text(impacts)

        structural_embedding = self._build_embedding(
            impacts,
        )

        return {
            "module_count": len(impacts),
            "changed_file_count": len(file_rows),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_changes": total_changes,
            "modified_file_count": status_counts["modified"],
            "added_file_count": status_counts["added"],
            "removed_file_count": status_counts["removed"],
            "renamed_file_count": status_counts["renamed"],
            "modules": modules,
            "module_profile": [
                impact.as_dict()
                for impact in impacts
            ],
            "structural_text": structural_text,
            "embedding": structural_embedding,
        }

    @staticmethod
    def _build_structural_text(
        impacts: list[ModuleImpact],
    ) -> str:
        """Create deterministic text representing the structural footprint."""

        if not impacts:
            return "Changed modules: <none>"

        lines = ["Changed modules:"]

        for impact in impacts:
            lines.append(
                f"- {impact.module} "
                f"(files={impact.file_count}, "
                f"changes={impact.changes}, "
                f"weight={impact.weight:.4f})"
            )

        return "\n".join(lines)

    def _build_embedding(
        self,
        impacts: list[ModuleImpact],
    ) -> list[float]:
        """
        Build a weighted structural embedding.

        Each module is represented in the same semantic embedding space
        as the PR intent. Impact-weighted averaging creates the structural
        footprint vector.
        """

        if not impacts:
            return [0.0] * 384

        module_texts = [
            impact.module.replace(".", " ")
            for impact in impacts
        ]

        embeddings = self._encoder.encode_many(
            module_texts,
        )

        dimension = len(embeddings[0])

        weighted = [0.0] * dimension
        total_weight = sum(
            impact.weight
            for impact in impacts
        )

        if total_weight <= 0:
            return [0.0] * dimension

        for impact, embedding in zip(
            impacts,
            embeddings,
            strict=True,
        ):
            normalized_weight = impact.weight / total_weight

            for index, value in enumerate(embedding):
                weighted[index] += (
                    normalized_weight * value
                )

        magnitude = math.sqrt(
            sum(value * value for value in weighted)
        )

        if magnitude == 0:
            return weighted

        return [
            value / magnitude
            for value in weighted
        ]


def utc_now() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()