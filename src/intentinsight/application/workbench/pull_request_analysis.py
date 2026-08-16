"""Application read service for the Pull Request Explorer."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

import pandas as pd

from intentinsight.application.workbench.models import PullRequestAnalysis
from intentinsight.application.workbench.research_results import ResearchArtifactStore


class PullRequestAnalysisService:
    """Compose inspectable analytical views from persisted project data."""

    def __init__(self, connection: sqlite3.Connection, artifacts: ResearchArtifactStore) -> None:
        self._connection = connection
        self._artifacts = artifacts

    def search(
        self,
        query: str = "",
        *,
        min_divergence: float | None = None,
        max_divergence: float | None = None,
        rework_status: str = "All",
        limit: int = 703,
    ) -> pd.DataFrame:
        query = query.strip()
        like = f"%{query}%"
        conditions = [
            "rr.eligible = 1",
            "(? = '' OR CAST(pr.number AS TEXT) LIKE ? OR pr.title LIKE ? OR r.full_name LIKE ?)",
        ]
        params: list[object] = [query, like, like, like]

        if min_divergence is not None:
            conditions.append("d.intent_impact_divergence >= ?")
            params.append(float(min_divergence))
        if max_divergence is not None:
            conditions.append("d.intent_impact_divergence <= ?")
            params.append(float(max_divergence))

        params.append(int(limit))
        rows = self._connection.execute(
            f"""
            SELECT r.id AS repository_id, r.full_name AS repository, pr.number, pr.title,
                   pr.merged_at, d.intent_impact_divergence AS divergence,
                   d.intent_similarity AS similarity, d.module_count
            FROM pull_requests AS pr
            JOIN repositories AS r ON r.id = pr.repository_id
            JOIN research_records AS rr ON rr.repository_id = pr.repository_id
                AND rr.pull_request_number = pr.number
            LEFT JOIN intent_impact_divergence AS d ON d.repository_id = pr.repository_id
                AND d.pull_request_number = pr.number
            WHERE {' AND '.join(conditions)}
            ORDER BY pr.merged_at DESC, pr.number DESC
            LIMIT ?
            """,
            params,
        ).fetchall()

        frame = pd.DataFrame([dict(row) for row in rows])
        if frame.empty:
            return frame

        rework = self._artifacts.load_rework_analysis()[
            ["repository_id", "pull_request_number", "rework_90d"]
        ]
        frame = frame.merge(
            rework,
            how="left",
            left_on=["repository_id", "number"],
            right_on=["repository_id", "pull_request_number"],
        ).drop(columns=["pull_request_number"], errors="ignore")

        if rework_status == "Reworked":
            frame = frame[frame["rework_90d"] == 1]
        elif rework_status == "No observed rework":
            frame = frame[frame["rework_90d"] == 0]
        elif rework_status == "No downstream observation":
            frame = frame[frame["rework_90d"].isna()]

        frame["rework_90d"] = frame["rework_90d"].map({1: "Yes", 0: "No"}).fillna("—")
        return frame

    def get(self, repository_id: int, pull_request_number: int) -> PullRequestAnalysis | None:
        row = self._connection.execute(
            """
            SELECT
                r.full_name AS repository_name,
                pr.*,
                i.combined_text AS intent_text,
                i.model_name AS intent_model,
                i.embedding_dimension AS intent_embedding_dimension,
                s.structural_text,
                s.model_name AS structural_model,
                s.module_count,
                s.module_profile_json,
                d.intent_impact_divergence AS divergence,
                d.intent_similarity AS similarity,
                d.module_entropy,
                d.module_concentration,
                d.top_module_weight,
                d.package_count,
                d.cross_package_spread
            FROM pull_requests AS pr
            JOIN repositories AS r ON r.id = pr.repository_id
            LEFT JOIN pull_request_intents AS i
              ON i.repository_id = pr.repository_id AND i.pull_request_number = pr.number
            LEFT JOIN pull_request_structures AS s
              ON s.repository_id = pr.repository_id AND s.pull_request_number = pr.number
            LEFT JOIN intent_impact_divergence AS d
              ON d.repository_id = pr.repository_id AND d.pull_request_number = pr.number
            WHERE pr.repository_id = ? AND pr.number = ?
            """,
            (repository_id, pull_request_number),
        ).fetchone()
        if row is None:
            return None

        row_dict = dict(row)
        files = self._connection.execute(
            """
            SELECT filename, status, additions, deletions, changes
            FROM pull_request_files
            WHERE repository_id = ? AND pull_request_number = ?
            ORDER BY changes DESC, filename
            """,
            (repository_id, pull_request_number),
        ).fetchall()
        downstream = self._rework_row(repository_id, pull_request_number)
        historical = self._historical_row(pull_request_number)

        return PullRequestAnalysis(
            repository_id=repository_id,
            repository_name=str(row_dict["repository_name"]),
            number=int(row_dict["number"]),
            title=str(row_dict["title"]),
            description=str(row_dict["description"] or ""),
            author=str(row_dict["author"]),
            state=str(row_dict["state"]),
            created_at=str(row_dict["created_at"]),
            updated_at=str(row_dict["updated_at"]),
            merged_at=row_dict["merged_at"],
            merge_commit_sha=row_dict["merge_commit_sha"],
            base_sha=row_dict["base_sha"],
            head_sha=row_dict["head_sha"],
            commits_count=int(row_dict["commits_count"]),
            changed_files_count=int(row_dict["changed_files_count"]),
            additions=int(row_dict["additions"]),
            deletions=int(row_dict["deletions"]),
            intent_text=row_dict.get("intent_text"),
            intent_model=row_dict.get("intent_model"),
            intent_embedding_dimension=self._int_or_none(row_dict.get("intent_embedding_dimension")),
            structural_text=row_dict.get("structural_text"),
            structural_model=row_dict.get("structural_model"),
            module_count=self._int_or_none(row_dict.get("module_count")),
            module_profile=self._module_profile(row_dict.get("module_profile_json")),
            divergence=self._float_or_none(row_dict.get("divergence")),
            similarity=self._float_or_none(row_dict.get("similarity")),
            module_entropy=self._float_or_none(row_dict.get("module_entropy")),
            module_concentration=self._float_or_none(row_dict.get("module_concentration")),
            top_module_weight=self._float_or_none(row_dict.get("top_module_weight")),
            package_count=self._int_or_none(row_dict.get("package_count")),
            cross_package_spread=self._int_or_none(row_dict.get("cross_package_spread")),
            rework_90d=None if downstream is None else bool(int(downstream["rework_90d"])),
            rework_pr_count_90d=None if downstream is None else self._int_or_none(downstream["rework_pr_count_90d"]),
            reworked_module_count_90d=None if downstream is None else self._int_or_none(downstream["reworked_module_count_90d"]),
            days_to_first_rework=None if downstream is None else self._float_or_none(downstream["days_to_first_rework"]),
            historical_validation=historical,
            changed_files=tuple(dict(file) for file in files),
        )

    def _rework_row(self, repository_id: int, number: int) -> dict[str, Any] | None:
        frame = self._artifacts.load_rework_analysis()
        rows = frame[(frame.repository_id == repository_id) & (frame.pull_request_number == number)]
        return None if rows.empty else rows.iloc[0].to_dict()

    def _historical_row(self, number: int) -> dict[str, Any] | None:
        for loader in (self._artifacts.load_reconstruction_validation_100, self._artifacts.load_reconstruction_validation):
            frame = loader()
            if "pr_number" not in frame.columns:
                continue
            rows = frame[frame.pr_number == number]
            if not rows.empty:
                return rows.iloc[0].to_dict()
        return None

    @staticmethod
    def _module_profile(value: object) -> tuple[dict[str, Any], ...]:
        if not value:
            return ()
        try:
            parsed = json.loads(str(value))
        except (TypeError, json.JSONDecodeError):
            return ()
        return tuple(item for item in parsed if isinstance(item, dict)) if isinstance(parsed, list) else ()

    @staticmethod
    def _int_or_none(value: object) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def _float_or_none(value: object) -> float | None:
        return None if value is None else float(value)
