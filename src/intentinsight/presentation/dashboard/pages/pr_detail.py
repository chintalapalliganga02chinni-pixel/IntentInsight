"""Individual Pull Request case file."""
from __future__ import annotations

import html
import json
from typing import Any

import streamlit as st

from intentinsight.presentation.dashboard.components import (
    callout,
    header,
    metric_row,
    section,
)
from intentinsight.presentation.dashboard.data.repository import (
    extract_module_profile,
    load_pr_detail,
    load_pr_overview,
)


# ============================================================================
# Helpers
# ============================================================================

def _escape(value: object) -> str:
    return html.escape(str(value))


def _number(
        mapping: dict[str, Any] | None,
        keys: list[str],
        decimals: int = 4,
) -> str:
    """Return the first available numeric value without inventing one."""

    if not mapping:
        return "—"

    for key in keys:
        value = mapping.get(key)

        if value is None or value == "":
            continue

        try:
            number = float(value)

            if decimals == 0:
                return f"{int(number):,}"

            return f"{number:,.{decimals}f}"

        except (TypeError, ValueError):
            return str(value)

    return "—"


def _text(
        mapping: dict[str, Any] | None,
        keys: list[str],
) -> str:
    """Return the first non-empty textual value."""

    if not mapping:
        return "—"

    for key in keys:
        value = mapping.get(key)

        if value is None:
            continue

        text = str(value).strip()

        if text:
            return text

    return "—"


def _outcome_value(
        mapping: dict[str, Any] | None,
) -> str:
    """Format the persisted downstream outcome without converting missingness to 0."""

    if not mapping:
        return "Not observable"

    for key in (
            "rework_90d",
            "rework",
            "outcome",
            "rework_outcome",
            "has_rework",
            "target",
    ):
        if key not in mapping:
            continue

        value = mapping.get(key)

        if value is None or value == "":
            continue

        if isinstance(value, bool):
            return "Rework observed" if value else "No rework observed"

        text = str(value).strip()

        lowered = text.lower()

        if lowered in {"1", "true", "yes"}:
            return "Rework observed"

        if lowered in {"0", "false", "no"}:
            return "No rework observed"

        return text

    return "Not observable"


# ============================================================================
# Page
# ============================================================================

header(
    "EXPLORE · CASE FILE",
    "Pull Request Detail",
    (
        "Inspect one observation across its expressed intent, implemented "
        "structural impact, divergence, historical evidence and downstream "
        "outcome where available."
    ),
)


# ============================================================================
# Population
# ============================================================================

population = load_pr_overview()

if population.empty:
    st.error(
        "The persisted Pull Request study population could not be loaded."
    )
    st.stop()


options: list[tuple[str, int, str, int]] = []

for _, row in population.iterrows():
    repository = str(row.get("repository", ""))

    try:
        number = int(
            row.get(
                "number",
                row.get("pull_request_number", 0),
            )
        )
    except (TypeError, ValueError):
        number = 0

    title = str(row.get("title", ""))

    try:
        repository_id = int(row.get("repository_id", 0))
    except (TypeError, ValueError):
        repository_id = 0

    options.append(
        (
            repository,
            number,
            title,
            repository_id,
        )
    )


labels = [
    f"{repository} #{number} · {title}"
    for repository, number, title, _ in options
]

choice = st.selectbox(
    "Pull Request",
    labels,
    index=0,
)

selected_index = labels.index(choice)

repository, number, title, repository_id = options[selected_index]


# ============================================================================
# Persisted case
# ============================================================================

detail = load_pr_detail(
    repository_id,
    number,
)

if not detail:
    st.error(
        "No persisted detail record was found for this Pull Request."
    )
    st.stop()


section(
    title,
    f"{repository} · Pull Request #{number}",
    "CASE",
)


# ============================================================================
# Evidence groups
# ============================================================================

intent = detail.get("intent") or {}
structure = detail.get("structure") or {}
divergence = detail.get("divergence") or {}
rework = detail.get("rework") or {}
historical = (
        detail.get("historical")
        or detail.get("reconstruction")
        or {}
)

pr = (
        detail.get("pull_request")
        or detail.get("pr")
        or detail
)


# ============================================================================
# Case metrics
# ============================================================================

metric_row(
    [
        (
            "Divergence",
            _number(
                divergence,
                [
                    "intent_impact_divergence",
                    "full_divergence",
                    "divergence",
                ],
            ),
            "persisted Intent–Impact measure",
        ),
        (
            "Intent similarity",
            _number(
                divergence,
                [
                    "intent_similarity",
                    "similarity",
                ],
            ),
            "semantic comparison",
        ),
        (
            "Changed modules",
            _number(
                structure,
                [
                    "module_count",
                    "divergence_module_count",
                ],
                decimals=0,
            ),
            "structural scope",
        ),
        (
            "90-day rework",
            _outcome_value(rework),
            "downstream outcome where observable",
        ),
    ]
)


# ============================================================================
# Developer intent
# ============================================================================

section(
    "Developer intent",
    (
        "The text below is the actual Pull Request intent used by the study "
        "representation."
    ),
    "OBSERVED TEXT",
)

intent_text = (
        pr.get("description")
        or intent.get("description")
        or intent.get("combined_text")
        or pr.get("title")
        or intent.get("title")
        or "No intent text available."
)

st.markdown(
    (
        '<div class="ii-card">'
        '<div style="color:#c0c9d3;line-height:1.7;">'
        f"{_escape(intent_text)}"
        "</div>"
        "</div>"
    ),
    unsafe_allow_html=True,
)


# ============================================================================
# Structural impact
# ============================================================================

section(
    "Structural impact",
    (
        "The structural representation is derived from changed Python "
        "modules and persisted with the analytical record."
    ),
    "IMPLEMENTED CHANGE",
)

metric_row(
    [
        (
            "Files changed",
            _number(
                structure,
                [
                    "changed_file_count",
                ],
                decimals=0,
            ),
            "structural files represented",
        ),
        (
            "Additions",
            _number(
                structure,
                [
                    "total_additions",
                ],
                decimals=0,
            ),
            "lines added",
        ),
        (
            "Deletions",
            _number(
                structure,
                [
                    "total_deletions",
                ],
                decimals=0,
            ),
            "lines deleted",
        ),
        (
            "Total changes",
            _number(
                structure,
                [
                    "total_changes",
                ],
                decimals=0,
            ),
            "structural change count",
        ),
    ]
)


# ============================================================================
# Changed files
# ============================================================================

files = detail.get("files") or []

if files:
    section(
        "Changed files",
        (
            "File-level evidence underlying the structural representation. "
            "The Workbench reports the persisted evidence without "
            "reinterpreting it."
        ),
        "FILE EVIDENCE",
    )

    file_frame = files

    st.dataframe(
        file_frame,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================================
# Module profile
# ============================================================================

profile_frame = extract_module_profile(detail)

if not profile_frame.empty:
    section(
        "Structural module profile",
        (
            "The module profile shows how the changed files were grouped "
            "for the structural representation."
        ),
        "STRUCTURAL REPRESENTATION",
    )

    st.dataframe(
        profile_frame,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================================
# Historical context
# ============================================================================

section(
    "Historical context",
    (
        "Where persisted reconstruction evidence is available, the case file "
        "shows it alongside the current representation rather than treating "
        "the current repository state as sufficient by default."
    ),
    "ROBUSTNESS",
)

if historical:
    st.json(historical)
else:
    st.caption(
        "Historical detail is not persisted for this case in the current "
        "presentation repository."
    )


# ============================================================================
# Downstream outcome
# ============================================================================

section(
    "Downstream outcome",
    (
        "The 90-day outcome is shown as persisted by the study. "
        "Unavailable observations remain unavailable and are not converted "
        "into negative outcomes."
    ),
    "90-DAY REWORK",
)

if rework:
    outcome = _outcome_value(rework)

    callout(
        "Observed outcome",
        outcome,
    )

    # Keep the underlying persisted record visible for reproducibility.
    with st.expander("View persisted outcome record"):
        st.json(rework)

else:
    callout(
        "Outcome boundary",
        (
            "The downstream outcome is unavailable for this observation. "
            "This is distinct from observing no rework; right-censored or "
            "otherwise non-observable cases must not be silently treated "
            "as negative outcomes."
        ),
        "warning",
    )


# ============================================================================
# Representation provenance
# ============================================================================

section(
    "Representation provenance",
    None,
    "TRACEABILITY",
)

c1, c2 = st.columns(2)

with c1:
    st.markdown(
        f"""
        <div class="ii-card">
            <div class="ii-card-label">SEMANTIC REPRESENTATION</div>
            <div style="margin-top:.45rem;line-height:1.6;">
                Model:
                <strong>{_escape(_text(intent, ["model_name"]))}</strong>
            </div>
            <div style="line-height:1.6;">
                Version:
                <strong>{_escape(_text(intent, ["model_version"]))}</strong>
            </div>
            <div style="line-height:1.6;">
                Dimensions:
                <strong>{_number(intent, ["embedding_dimension"], 0)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="ii-card">
            <div class="ii-card-label">STRUCTURAL REPRESENTATION</div>
            <div style="margin-top:.45rem;line-height:1.6;">
                Model:
                <strong>{_escape(_text(structure, ["model_name"]))}</strong>
            </div>
            <div style="line-height:1.6;">
                Version:
                <strong>{_escape(_text(structure, ["model_version"]))}</strong>
            </div>
            <div style="line-height:1.6;">
                Dimensions:
                <strong>{_number(structure, ["embedding_dimension"], 0)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
