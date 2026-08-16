"""Research overview: the complete study story, not a metric dashboard."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from intentinsight.presentation.dashboard.components import (
    callout,
    header,
    metric_row,
    section,
)
from intentinsight.presentation.dashboard.data.repository import (
    load_database_counts,
    load_rework_analysis,
)


# =============================================================================
# PAGE PATHS
# =============================================================================
#
# Resolve the same absolute page-source paths used by app.py. Streamlit
# requires st.page_link() targets to match pages registered in st.navigation().
# =============================================================================

PAGE_DIR = Path(__file__).resolve().parent

EXPLORER_PAGE = str(PAGE_DIR / "pr_explorer.py")
DIVERGENCE_PAGE = str(PAGE_DIR / "divergence.py")
EVIDENCE_PAGE = str(PAGE_DIR / "evidence.py")
METHODOLOGY_PAGE = str(PAGE_DIR / "methodology.py")


# =============================================================================
# HEADER
# =============================================================================

header(
    "INTENTINSIGHT · RESEARCH WORKBENCH",
    "Semantic–Structural Divergence in Pull Requests",
    (
        "IntentInsight investigates whether the structural impact implemented "
        "by a Pull Request is aligned with the developer intent expressed in "
        "its title and description, and whether that relationship adds "
        "information about subsequent structural rework."
    ),
)


# =============================================================================
# THE STUDY
# =============================================================================

section(
    "What is this research about?",
    (
        "A Pull Request contains a textual account of what a developer intends "
        "to change. The repository state records what actually changed. "
        "IntentInsight places those two views of the same development event "
        "into comparable representations: transformer-based semantic "
        "embeddings for intent and structural information extracted from "
        "changed Python modules for implemented impact. Their comparison "
        "produces the Intent–Impact Divergence measure."
    ),
    "THE STUDY",
)


# =============================================================================
# INTENT → IMPACT → COMPARISON
# =============================================================================

intent_col, impact_col, comparison_col = st.columns(
    3,
    gap="medium",
)

with intent_col:
    with st.container(border=True):
        st.caption("01 · INTENT")
        st.subheader("Developer description")
        st.write(
            "The textual representation of what the developer intends "
            "to change."
        )

with impact_col:
    with st.container(border=True):
        st.caption("02 · IMPACT")
        st.subheader("Changed structure")
        st.write(
            "The structural representation of what the Pull Request "
            "actually changed."
        )

with comparison_col:
    with st.container(border=True):
        st.caption("03 · COMPARISON")
        st.subheader("Divergence")
        st.write(
            "The comparison between semantic intent and implemented "
            "structural impact."
        )


# =============================================================================
# RESEARCH QUESTIONS
# =============================================================================

section(
    "Research questions",
    (
        "These are the established questions of the empirical study. "
        "They are kept intact in the Workbench rather than replaced by "
        "product-style questions."
    ),
    "FOUR QUESTIONS",
)

rqs = [
    (
        "RQ1",
        "Can developer intent and implemented structural impact be represented consistently?",
        "Coverage and representation evidence across the complete matched study population.",
    ),
    (
        "RQ2",
        "Does Intent–Impact Divergence capture meaningful semantic–structural characteristics of Pull Requests?",
        "Observed pairing compared with a 10,000-permutation random-pairing null model.",
    ),
    (
        "RQ3",
        "Is the divergence measure robust to historical reconstruction and structural-scope confounders?",
        "Historical reconstruction plus structural-scope analysis.",
    ),
    (
        "RQ4",
        "Does Intent–Impact Divergence provide incremental predictive value for subsequent structural rework?",
        "Chronological 90-day downstream evaluation with a paired permutation test.",
    ),
]

for code, question, method in rqs:

    with st.container(border=True):

        st.caption(code)

        st.markdown(
            f"**{question}**"
        )

        st.caption(
            f"Tested through: {method}"
        )


# =============================================================================
# EVIDENCE PATH
# =============================================================================

section(
    "What was expected — and what was found?",
    (
        "The important part of the study is not whether every expectation "
        "was confirmed. It is the separation of what the evidence supports "
        "from what it does not."
    ),
    "EVIDENCE PATH",
)


expectations = [
    (
        "RQ1 · Representation",
        "The study required a complete, consistently paired representation "
        "of developer intent and implemented structural impact.",
        "703 eligible Pull Requests have 703 semantic representations, "
        "703 structural representations and 703 matching PR keys. "
        "The paired analytical population is complete.",
    ),
    (
        "RQ2 · Meaningful structure",
        "If the observed pairing contains meaningful structure, its "
        "semantic–structural similarity should differ from arbitrary "
        "pairings of the same representations.",
        "Observed mean similarity was 0.307207 versus 0.241821 under "
        "random pairing; the difference was +0.065386 with permutation "
        "p = 0.0001 across 10,000 permutations.",
    ),
    (
        "RQ3 · Robustness",
        "A structural representation tied to the historical Pull Request "
        "state should survive reconstruction and should not be explained "
        "only by a current repository snapshot.",
        "Historical reconstruction achieved exact module-profile "
        "equivalence for 703/703 Pull Requests. Current and historical "
        "divergence correlated at r = 0.944004; 47.65% of values were "
        "identical.",
    ),
    (
        "RQ4 · Predictive value",
        "If divergence adds downstream information, adding it to the "
        "baseline model should improve performance on the selected "
        "90-day structural-rework outcome.",
        "Baseline ROC-AUC was 0.564427; baseline + divergence was "
        "0.560606. The observed difference was −0.003821, with paired "
        "permutation p = 0.729627. No statistically detectable "
        "incremental predictive value was found.",
    ),
]


for title, expected, found in expectations:

    with st.container(border=True):

        st.caption(title)

        st.markdown("**Expected**")

        st.write(expected)

        st.markdown("**Found**")

        st.write(found)


# =============================================================================
# STUDY STATE
# =============================================================================

counts = load_database_counts()
rework = load_rework_analysis()

section(
    "Study at a glance",
    (
        "These values describe the validated analytical population and "
        "downstream study boundary. They are not newly recomputed by "
        "the interface."
    ),
    "STUDY STATE",
)

eligible = int(
    counts.get("eligible_prs", 703) or 703
)

intent_n = int(
    counts.get("intent_representations", 703) or 703
)

structure_n = int(
    counts.get("structural_representations", 703) or 703
)

rework_n = (
    int(rework.shape[0])
    if not rework.empty
    else 702
)

metric_row(
    [
        (
            "Eligible Pull Requests",
            f"{eligible:,}",
            "complete paired study population",
        ),
        (
            "Semantic representations",
            f"{intent_n:,}",
            "transformer-based intent representation",
        ),
        (
            "Structural representations",
            f"{structure_n:,}",
            "changed-module structural representation",
        ),
        (
            "Observable downstream cases",
            f"{rework_n:,}",
            "90-day structural-rework analysis",
        ),
    ]
)


# =============================================================================
# CENTRAL FINDING
# =============================================================================

section(
    "The study's central finding",
    None,
    "INTERPRETATION",
)

callout(
    "What the evidence says",
    (
        "Intent and structural impact exhibit non-random alignment, and "
        "the structural representation survives historical reconstruction. "
        "However, the tested divergence measure did not demonstrate "
        "statistically detectable incremental predictive value for the "
        "selected 90-day structural-rework outcome. The result is therefore "
        "a finding about the construct and its tested downstream usefulness "
        "— not a claim that IntentInsight predicts rework."
    ),
)


# =============================================================================
# BOUNDARIES
# =============================================================================

section(
    "What this study does not claim",
    None,
    "BOUNDARIES",
)

boundaries = [
    "Non-random alignment does not establish causality.",
    "A validated divergence construct is not automatically a code-quality score.",
    "The null-model result does not establish downstream predictive usefulness.",
    "The negative downstream result is bounded by the selected outcome, split, representations and evaluation design.",
    "The study does not claim that divergence is useful for every possible future engineering outcome.",
]

for item in boundaries:
    st.markdown(f"- {item}")


# =============================================================================
# FOLLOW THE EVIDENCE
# =============================================================================

section(
    "Follow the evidence",
    (
        "Move directly from the study overview into the underlying "
        "analytical views."
    ),
    "NEXT",
)


follow_cols = st.columns(
    4,
    gap="medium",
)


# -----------------------------------------------------------------------------
# Explorer
# -----------------------------------------------------------------------------

with follow_cols[0]:

    with st.container(border=True):

        st.caption("EXPLORER")

        st.subheader("Pull Request Explorer")

        st.write(
            "Inspect the 703 individual Pull Requests and explore "
            "their persisted analytical records."
        )

        st.page_link(
            EXPLORER_PAGE,
            label="Open Explorer",
            icon=":material/search:",
            width="stretch",
        )


# -----------------------------------------------------------------------------
# Divergence
# -----------------------------------------------------------------------------

with follow_cols[1]:

    with st.container(border=True):

        st.caption("DIVERGENCE")

        st.subheader("Divergence Analysis")

        st.write(
            "Inspect the Intent–Impact construct, its distribution, "
            "and its analytical interpretation."
        )

        st.page_link(
            DIVERGENCE_PAGE,
            label="Open Divergence",
            icon=":material/analytics:",
            width="stretch",
        )


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

with follow_cols[2]:

    with st.container(border=True):

        st.caption("VALIDATION")

        st.subheader("Evidence & Validation")

        st.write(
            "Trace the statistical evidence, robustness checks, "
            "null model and downstream evaluation."
        )

        st.page_link(
            EVIDENCE_PAGE,
            label="Open Validation",
            icon=":material/fact_check:",
            width="stretch",
        )


# -----------------------------------------------------------------------------
# Methodology
# -----------------------------------------------------------------------------

with follow_cols[3]:

    with st.container(border=True):

        st.caption("METHODOLOGY")

        st.subheader("Methodology")

        st.write(
            "Read the operational definitions, representation pipeline, "
            "study design and research boundaries."
        )

        st.page_link(
            METHODOLOGY_PAGE,
            label="Open Methodology",
            icon=":material/account_tree:",
            width="stretch",
        )


# =============================================================================
# FINAL NOTE
# =============================================================================

st.caption(
    "The Workbench navigation and the evidence links above operate on "
    "the registered Streamlit pages; research artifacts remain read-only."
)
