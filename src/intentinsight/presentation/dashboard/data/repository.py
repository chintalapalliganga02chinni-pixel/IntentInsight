"""
Read-only data access for the IntentInsight Research Workbench.

The presentation layer reads already validated research artifacts.

It does not:
    - recalculate research metrics
    - modify the database
    - train models
    - make GitHub requests
    - invent missing observations

The research pipeline remains the source of truth.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from intentinsight.infrastructure.configuration.settings import load_settings
from intentinsight.infrastructure.database.connection import DatabaseConnection


# ============================================================================
# Project / database configuration
# ============================================================================


def _project_root() -> Path:
    """
    Return the IntentInsight project root directory.

    repository.py lives at:

        src/
          intentinsight/
            presentation/
              dashboard/
                data/
                  repository.py

    parents[5] therefore resolves to the project root.
    """

    return Path(__file__).resolve().parents[5]


def _database_path(database_url: str) -> str:
    """Convert the configured SQLite URL into a filesystem path."""

    prefix = "sqlite:///"

    if not database_url.startswith(prefix):
        raise ValueError(
            "IntentInsight currently supports SQLite database URLs only."
        )

    path = database_url[len(prefix):]

    if not path:
        raise ValueError(
            "DATABASE_URL contains an empty SQLite path."
        )

    return path


@st.cache_resource
def _database_manager() -> DatabaseConnection:
    """Create the configured database connection manager."""

    settings = load_settings()

    return DatabaseConnection(
        _database_path(settings.database_url)
    )


def _connect() -> sqlite3.Connection:
    """Open a read connection to the IntentInsight database."""

    connection = _database_manager().connect()
    connection.row_factory = sqlite3.Row

    return connection


# ============================================================================
# Generic helpers
# ============================================================================


def _query_dataframe(
        connection: sqlite3.Connection,
        query: str,
        parameters: tuple[Any, ...] = (),
) -> pd.DataFrame:
    """Execute a SELECT query and return the result as a DataFrame."""

    rows = connection.execute(
        query,
        parameters,
    ).fetchall()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [dict(row) for row in rows]
    )


def _query_dicts(
        connection: sqlite3.Connection,
        query: str,
        parameters: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    """Execute a SELECT query and return dictionaries."""

    rows = connection.execute(
        query,
        parameters,
    ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def _parse_json(value: Any) -> Any:
    """Safely decode a persisted JSON value."""

    if value is None:
        return None

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(str(value))
    except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
    ):
        return None


def _first_existing_column(
        frame: pd.DataFrame,
        candidates: list[str],
) -> str | None:
    """Return the first candidate column present in a DataFrame."""

    for candidate in candidates:
        if candidate in frame.columns:
            return candidate

    return None


def _normalise_key(
        value: Any,
) -> str:
    """
    Normalise a repository / PR identifier for artifact joins.

    This deliberately remains conservative: it does not infer missing
    identifiers.
    """

    if value is None:
        return ""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value).strip()


# ============================================================================
# Database overview
# ============================================================================


@st.cache_data(ttl=30)
def load_database_counts() -> dict[str, int]:
    """Load high-level counts from the persisted research database."""

    connection = _connect()

    try:
        queries = {
            "repositories": """
                            SELECT COUNT(*) AS count
                            FROM repositories
                            """,
            "pull_requests": """
                             SELECT COUNT(*) AS count
                             FROM pull_requests
                             """,
            "research_records": """
                                SELECT COUNT(*) AS count
                                FROM research_records
                                """,
            "eligible_prs": """
                            SELECT COUNT(*) AS count
                            FROM research_records
                            WHERE eligible = 1
                            """,
            "intent_representations": """
                                      SELECT COUNT(*) AS count
                                      FROM pull_request_intents
                                      """,
            "structural_representations": """
                                          SELECT COUNT(*) AS count
                                          FROM pull_request_structures
                                          """,
            "divergence_records": """
                                  SELECT COUNT(*) AS count
                                  FROM intent_impact_divergence
                                  """,
        }

        result: dict[str, int] = {}

        for name, query in queries.items():
            row = connection.execute(query).fetchone()

            result[name] = (
                int(row["count"])
                if row is not None
                else 0
            )

        return result

    finally:
        connection.close()


# ============================================================================
# Pull Request population
# ============================================================================


@st.cache_data(ttl=30)
def load_pr_overview() -> pd.DataFrame:
    """
    Load the eligible analytical Pull Request population.

    Intent, structural and divergence values are read from persisted
    research tables.
    """

    connection = _connect()

    try:
        query = """
                SELECT
                    pr.repository_id,
                    pr.number,

                    r.full_name AS repository,
                    r.owner AS repository_owner,
                    r.name AS repository_name,

                    pr.title,
                    pr.author,
                    pr.state,
                    pr.created_at,
                    pr.updated_at,
                    pr.merged_at,

                    pr.commits_count,
                    pr.changed_files_count,
                    pr.additions,
                    pr.deletions,

                    intents.model_name
                                AS intent_model_name,

                    intents.model_version
                                AS intent_model_version,

                    structures.module_count,

                    structures.changed_file_count
                                AS structural_changed_file_count,

                    structures.total_additions,
                    structures.total_deletions,
                    structures.total_changes,

                    divergence.intent_similarity,

                    divergence.intent_impact_divergence,

                    divergence.module_entropy,

                    divergence.module_concentration,

                    divergence.top_module_weight,

                    divergence.package_count,

                    divergence.cross_package_spread

                FROM pull_requests AS pr

                         INNER JOIN research_records AS rr
                                    ON rr.repository_id = pr.repository_id
                                        AND rr.pull_request_number = pr.number

                         LEFT JOIN repositories AS r
                                   ON r.id = pr.repository_id

                         LEFT JOIN pull_request_intents AS intents
                                   ON intents.repository_id = pr.repository_id
                                       AND intents.pull_request_number = pr.number

                         LEFT JOIN pull_request_structures AS structures
                                   ON structures.repository_id = pr.repository_id
                                       AND structures.pull_request_number = pr.number

                         LEFT JOIN intent_impact_divergence AS divergence
                                   ON divergence.repository_id = pr.repository_id
                                       AND divergence.pull_request_number = pr.number

                WHERE rr.eligible = 1

                ORDER BY
                    pr.merged_at DESC,
                    pr.number DESC \
                """

        return _query_dataframe(
            connection,
            query,
        )

    finally:
        connection.close()


# ============================================================================
# Pull Request explorer
# ============================================================================


@st.cache_data(ttl=30)
def load_pr_explorer(
        search_text: str = "",
        repository: str = "All repositories",
        divergence_min: float | None = None,
        divergence_max: float | None = None,
        sort_by: str = "merged_at",
        descending: bool = True,
) -> pd.DataFrame:
    """Load and filter the persisted Pull Request population."""

    frame = load_pr_overview().copy()

    if frame.empty:
        return frame

    if repository != "All repositories":
        frame = frame[
            frame["repository"] == repository
            ]

    search = (
        search_text
        .strip()
        .lower()
    )

    if search:
        searchable_columns = [
            "repository",
            "title",
            "author",
        ]

        mask = pd.Series(
            False,
            index=frame.index,
        )

        for column in searchable_columns:
            if column not in frame.columns:
                continue

            mask |= (
                frame[column]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(
                    search,
                    regex=False,
                )
            )

        frame = frame[mask]

    if (
            divergence_min is not None
            and "intent_impact_divergence" in frame.columns
    ):
        frame = frame[
            frame["intent_impact_divergence"]
            .fillna(-1.0)
            >= divergence_min
            ]

    if (
            divergence_max is not None
            and "intent_impact_divergence" in frame.columns
    ):
        frame = frame[
            frame["intent_impact_divergence"]
            .fillna(2.0)
            <= divergence_max
            ]

    if sort_by in frame.columns:
        frame = frame.sort_values(
            by=sort_by,
            ascending=not descending,
            na_position="last",
        )

    return frame.reset_index(drop=True)


# ============================================================================
# Rework artifact loading
# ============================================================================


@st.cache_data(ttl=60)
def load_rework_analysis() -> pd.DataFrame:
    """
    Load the committed 90-day rework analysis.

    The artifact is treated as authoritative. No outcome is inferred here.
    """

    path = (
            _project_root()
            / "rework_90d_analysis.csv"
    )

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


@st.cache_data(ttl=60)
def load_predictive_results() -> pd.DataFrame:
    """Load the committed 90-day predictive model results."""

    path = (
            _project_root()
            / "rework_90d_model_results.csv"
    )

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


@st.cache_data(ttl=60)
def load_random_control_results() -> pd.DataFrame:
    """Load the structural random-control analysis."""

    path = (
            _project_root()
            / "structural_random_control_analysis.csv"
    )

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


@st.cache_data(ttl=60)
def load_structural_scope_results() -> pd.DataFrame:
    """Load the structural-scope analysis."""

    path = (
            _project_root()
            / "structural_scope_analysis.csv"
    )

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


# ============================================================================
# Rework record matching
# ============================================================================


def _match_rework_record(
        repository_id: int,
        pull_request_number: int,
) -> dict[str, Any]:
    """
    Find the persisted 90-day rework record for one Pull Request.

    The function deliberately checks available identifier columns rather
    than assuming one exact CSV schema. It never creates an outcome when
    there is no matching persisted record.
    """

    frame = load_rework_analysis()

    if frame.empty:
        return {}

    repo_number = _normalise_key(pull_request_number)

    # ------------------------------------------------------------------------
    # Direct repository-id + PR-number match
    # ------------------------------------------------------------------------

    repository_id_column = _first_existing_column(
        frame,
        [
            "repository_id",
            "repo_id",
            "repository",
        ],
    )

    number_column = _first_existing_column(
        frame,
        [
            "pull_request_number",
            "pr_number",
            "number",
        ],
    )

    if repository_id_column and number_column:
        mask = (
                       frame[repository_id_column]
                       .map(_normalise_key)
                       == _normalise_key(repository_id)
               ) & (
                       frame[number_column]
                       .map(_normalise_key)
                       == repo_number
               )

        matches = frame.loc[mask]

        if not matches.empty:
            return matches.iloc[0].to_dict()

    # ------------------------------------------------------------------------
    # Full-name + PR-number match
    # ------------------------------------------------------------------------

    full_name_column = _first_existing_column(
        frame,
        [
            "repository",
            "repo",
            "full_name",
            "repository_full_name",
        ],
    )

    if full_name_column and number_column:
        # Obtain the canonical repository name from the database.
        connection = _connect()

        try:
            row = connection.execute(
                """
                SELECT full_name
                FROM repositories
                WHERE id = ?
                LIMIT 1
                """,
                (repository_id,),
            ).fetchone()
        finally:
            connection.close()

        if row is not None:
            repository_name = _normalise_key(
                row["full_name"]
            )

            mask = (
                           frame[full_name_column]
                           .map(_normalise_key)
                           == repository_name
                   ) & (
                           frame[number_column]
                           .map(_normalise_key)
                           == repo_number
                   )

            matches = frame.loc[mask]

            if not matches.empty:
                return matches.iloc[0].to_dict()

    return {}


# ============================================================================
# Individual Pull Request detail
# ============================================================================


@st.cache_data(ttl=30)
def load_pr_detail(
        repository_id: int,
        pull_request_number: int,
) -> dict[str, Any] | None:
    """
    Load all persisted evidence available for one Pull Request.

    This combines the relational database record with the committed
    90-day rework artifact. It does not calculate or infer any research
    metric.
    """

    connection = _connect()

    try:
        query = """
                SELECT
                    pr.repository_id,
                    pr.number,

                    r.full_name AS repository,
                    r.owner AS repository_owner,
                    r.name AS repository_name,
                    r.html_url AS repository_url,

                    pr.title,
                    pr.description,
                    pr.author,
                    pr.state,

                    pr.created_at,
                    pr.updated_at,
                    pr.merged_at,
                    pr.merge_commit_sha,

                    pr.commits_count,
                    pr.changed_files_count,
                    pr.additions,
                    pr.deletions,

                    rr.eligible,
                    rr.exclusion_reason,

                    intents.title
                                AS intent_title,

                    intents.description
                                AS intent_description,

                    intents.combined_text
                                AS intent_combined_text,

                    intents.model_name
                                AS intent_model_name,

                    intents.model_version
                                AS intent_model_version,

                    intents.embedding_dimension
                                AS intent_embedding_dimension,

                    intents.embedding_json
                                AS intent_embedding_json,

                    structures.module_count,

                    structures.changed_file_count
                                AS structural_changed_file_count,

                    structures.total_additions,
                    structures.total_deletions,
                    structures.total_changes,

                    structures.modified_file_count,
                    structures.added_file_count,
                    structures.removed_file_count,
                    structures.renamed_file_count,

                    structures.module_profile_json,

                    structures.structural_text,

                    structures.model_name
                                AS structural_model_name,

                    structures.model_version
                                AS structural_model_version,

                    structures.embedding_dimension
                                AS structural_embedding_dimension,

                    structures.embedding_json
                                AS structural_embedding_json,

                    divergence.intent_similarity,

                    divergence.intent_impact_divergence,

                    divergence.module_count
                                AS divergence_module_count,

                    divergence.changed_file_count
                                AS divergence_changed_file_count,

                    divergence.module_entropy,

                    divergence.module_concentration,

                    divergence.top_module_weight,

                    divergence.package_count,

                    divergence.cross_package_spread

                FROM pull_requests AS pr

                         LEFT JOIN repositories AS r
                                   ON r.id = pr.repository_id

                         LEFT JOIN research_records AS rr
                                   ON rr.repository_id = pr.repository_id
                                       AND rr.pull_request_number = pr.number

                         LEFT JOIN pull_request_intents AS intents
                                   ON intents.repository_id = pr.repository_id
                                       AND intents.pull_request_number = pr.number

                         LEFT JOIN pull_request_structures AS structures
                                   ON structures.repository_id = pr.repository_id
                                       AND structures.pull_request_number = pr.number

                         LEFT JOIN intent_impact_divergence AS divergence
                                   ON divergence.repository_id = pr.repository_id
                                       AND divergence.pull_request_number = pr.number

                WHERE
                    pr.repository_id = ?
                  AND pr.number = ?

                    LIMIT 1 \
                """

        row = connection.execute(
            query,
            (
                repository_id,
                pull_request_number,
            ),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)

        # --------------------------------------------------------------------
        # Semantic representation
        # --------------------------------------------------------------------

        result["intent"] = {
            "title": result.pop(
                "intent_title",
                None,
            ),
            "description": result.pop(
                "intent_description",
                None,
            ),
            "combined_text": result.pop(
                "intent_combined_text",
                None,
            ),
            "model_name": result.pop(
                "intent_model_name",
                None,
            ),
            "model_version": result.pop(
                "intent_model_version",
                None,
            ),
            "embedding_dimension": result.pop(
                "intent_embedding_dimension",
                None,
            ),
            "embedding": _parse_json(
                result.pop(
                    "intent_embedding_json",
                    None,
                )
            ),
        }

        # --------------------------------------------------------------------
        # Structural representation
        # --------------------------------------------------------------------

        result["structure"] = {
            "module_count": result.get(
                "module_count"
            ),
            "changed_file_count": result.pop(
                "structural_changed_file_count",
                None,
            ),
            "total_additions": result.get(
                "total_additions"
            ),
            "total_deletions": result.get(
                "total_deletions"
            ),
            "total_changes": result.get(
                "total_changes"
            ),
            "modified_file_count": result.pop(
                "modified_file_count",
                None,
            ),
            "added_file_count": result.pop(
                "added_file_count",
                None,
            ),
            "removed_file_count": result.pop(
                "removed_file_count",
                None,
            ),
            "renamed_file_count": result.pop(
                "renamed_file_count",
                None,
            ),
            "module_profile_json": result.pop(
                "module_profile_json",
                None,
            ),
            "structural_text": result.pop(
                "structural_text",
                None,
            ),
            "model_name": result.pop(
                "structural_model_name",
                None,
            ),
            "model_version": result.pop(
                "structural_model_version",
                None,
            ),
            "embedding_dimension": result.pop(
                "structural_embedding_dimension",
                None,
            ),
            "embedding": _parse_json(
                result.pop(
                    "structural_embedding_json",
                    None,
                )
            ),
        }

        # --------------------------------------------------------------------
        # Divergence representation
        # --------------------------------------------------------------------

        result["divergence"] = {
            "intent_similarity": result.pop(
                "intent_similarity",
                None,
            ),
            "intent_impact_divergence": result.pop(
                "intent_impact_divergence",
                None,
            ),
            "module_count": result.pop(
                "divergence_module_count",
                None,
            ),
            "changed_file_count": result.pop(
                "divergence_changed_file_count",
                None,
            ),
            "module_entropy": result.pop(
                "module_entropy",
                None,
            ),
            "module_concentration": result.pop(
                "module_concentration",
                None,
            ),
            "top_module_weight": result.pop(
                "top_module_weight",
                None,
            ),
            "package_count": result.pop(
                "package_count",
                None,
            ),
            "cross_package_spread": result.pop(
                "cross_package_spread",
                None,
            ),
        }

        # --------------------------------------------------------------------
        # Changed-file evidence
        # --------------------------------------------------------------------

        result["files"] = _load_pr_files(
            connection=connection,
            repository_id=repository_id,
            pull_request_number=pull_request_number,
        )

    finally:
        connection.close()

    # ------------------------------------------------------------------------
    # Downstream 90-day outcome
    # ------------------------------------------------------------------------

    result["rework"] = _match_rework_record(
        repository_id=repository_id,
        pull_request_number=pull_request_number,
    )

    # ------------------------------------------------------------------------
    # Historical evidence
    #
    # Historical reconstruction remains an artifact-level concern. We do not
    # fabricate a case-specific historical record if one is not persisted.
    # ------------------------------------------------------------------------

    result["historical"] = {}

    return result


def _load_pr_files(
        connection: sqlite3.Connection,
        repository_id: int,
        pull_request_number: int,
) -> list[dict[str, Any]]:
    """Load changed-file evidence for a Pull Request."""

    table = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'pull_request_files'
        """
    ).fetchone()

    if table is None:
        return []

    return _query_dicts(
        connection,
        """
        SELECT
            filename,
            status,
            additions,
            deletions,
            changes,
            sha,
            collected_at
        FROM pull_request_files
        WHERE
            repository_id = ?
          AND pull_request_number = ?
        ORDER BY
            changes DESC,
            filename ASC
        """,
        (
            repository_id,
            pull_request_number,
        ),
    )


# ============================================================================
# Structural module profile
# ============================================================================


def extract_module_profile(
        detail: dict[str, Any],
) -> pd.DataFrame:
    """
    Convert a persisted structural module profile into a DataFrame.

    The profile is evidence extracted from changed-file paths. It is not
    interpreted here as a claim about true repository architecture.
    """

    structure = detail.get("structure") or {}

    profile = _parse_json(
        structure.get("module_profile_json")
    )

    columns = [
        "module",
        "file_count",
        "additions",
        "deletions",
        "changes",
        "weight",
        "statuses",
    ]

    if not isinstance(profile, list):
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(profile)

    for column in columns:
        if column not in frame.columns:
            frame[column] = None

    return frame[columns]


# ============================================================================
# Repository metadata
# ============================================================================


@st.cache_data(ttl=60)
def load_repositories() -> pd.DataFrame:
    """Load repository metadata."""

    connection = _connect()

    try:
        return _query_dataframe(
            connection,
            """
            SELECT
                id,
                owner,
                name,
                full_name,
                default_branch,
                html_url,
                mined_at
            FROM repositories
            ORDER BY full_name
            """,
        )

    finally:
        connection.close()


# ============================================================================
# Collection history
# ============================================================================


@st.cache_data(ttl=60)
def load_collection_runs() -> pd.DataFrame:
    """Load research dataset collection history."""

    connection = _connect()

    try:
        return _query_dataframe(
            connection,
            """
            SELECT
                collection_runs.id,

                repositories.full_name
                    AS repository,

                collection_runs.started_at,
                collection_runs.completed_at,
                collection_runs.status,

                collection_runs.pull_requests_discovered,
                collection_runs.records_created,
                collection_runs.eligible_records,
                collection_runs.excluded_records

            FROM collection_runs

                     LEFT JOIN repositories
                               ON repositories.id =
                                  collection_runs.repository_id

            ORDER BY
                collection_runs.started_at DESC
            """,
        )

    finally:
        connection.close()


# ============================================================================
# Cache management
# ============================================================================


def clear_repository_cache() -> None:
    """Clear all presentation-layer cached data."""

    load_database_counts.clear()
    load_pr_overview.clear()
    load_pr_explorer.clear()
    load_pr_detail.clear()

    load_repositories.clear()

    load_predictive_results.clear()
    load_rework_analysis.clear()
    load_random_control_results.clear()
    load_structural_scope_results.clear()

    load_collection_runs.clear()