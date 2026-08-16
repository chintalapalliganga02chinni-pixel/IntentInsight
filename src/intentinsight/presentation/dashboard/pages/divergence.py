"""Construct-level divergence analysis."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from intentinsight.presentation.dashboard.components import callout, header, metric_row, section
from intentinsight.presentation.dashboard.data.repository import load_pr_overview, load_structural_scope_results

header(
    "EVIDENCE · CONSTRUCT",
    "Intent–Impact Divergence",
    "Inspect how the measured construct varies across the 703-Pull-Request analytical population and how it relates to structural scope.",
)

section(
    "What is being measured?",
    "Divergence compares a semantic representation of developer intent with a structural representation of implemented impact. It is an analytical measure of the relationship between the two representations; it is not, by itself, a quality judgement.",
    "OPERATIONAL DEFINITION",
)

st.markdown(
    '<div class="ii-result-row">'
    '<div class="ii-result"><div class="ii-result-label">Intent</div><div class="ii-result-value">Transformer embedding</div></div>'
    '<div class="ii-result"><div class="ii-result-label">Impact</div><div class="ii-result-value">Changed Python structure</div></div>'
    '<div class="ii-result"><div class="ii-result-label">Measure</div><div class="ii-result-value">D = 1 − similarity</div></div>'
    '</div>', unsafe_allow_html=True,
)

pr = load_pr_overview()
scope = load_structural_scope_results()

values = pd.Series(dtype="float64")
if not scope.empty and "full_divergence" in scope.columns:
    values = pd.to_numeric(scope["full_divergence"], errors="coerce").dropna()
elif not pr.empty and "intent_impact_divergence" in pr.columns:
    values = pd.to_numeric(pr["intent_impact_divergence"], errors="coerce").dropna()

section(
    "Distribution",
    "The distribution is descriptive. It shows how the construct varies across the study population; it does not imply that higher divergence causes later rework.",
    "703 OBSERVATIONS",
)
if not values.empty:
    metric_row([
        ("Mean", f"{values.mean():.4f}", "current structural representation"),
        ("Median", f"{values.median():.4f}", "50th percentile"),
        ("10th percentile", f"{values.quantile(.10):.4f}", "lower tail"),
        ("90th percentile", f"{values.quantile(.90):.4f}", "upper tail"),
    ])
    bins = pd.cut(values, bins=20, include_lowest=True).value_counts().sort_index()
    chart = pd.DataFrame({"Pull Requests": bins.to_numpy()}, index=[str(x) for x in bins.index])
    st.bar_chart(chart, height=320, use_container_width=True)
else:
    st.info("The persisted structural-scope artifact is not available to this page.")

section(
    "Structural scope and divergence",
    "The structural-scope artifact allows inspection of whether the construct varies with observable properties of the implemented change. These are analytical associations, not causal claims.",
    "SCOPE ANALYSIS",
)
if not scope.empty:
    preferred = [
        c for c in [
            "full_divergence", "python_divergence", "delta", "module_count",
            "total_files", "python_files", "non_python_files", "total_changes",
            "python_changes", "non_python_change_ratio", "non_python_ratio",
        ] if c in scope.columns
    ]
    if preferred:
        st.dataframe(scope[preferred].describe().T.round(4), use_container_width=True)

    edge_cols = [c for c in ["repository_id", "pull_request_number", "full_divergence", "python_divergence", "delta", "module_count", "total_changes"] if c in scope.columns]
    if edge_cols:
        st.markdown("#### Highest-divergence observations")
        st.caption("Inspection points only. A high value is not automatically anomalous or problematic.")
        st.dataframe(scope.sort_values("full_divergence", ascending=False)[edge_cols].head(15), hide_index=True, use_container_width=True)

section("Interpretation", None, "RESEARCH BOUNDARY")
callout(
    "A measure, not a verdict",
    "The construct is useful because it can be examined empirically. Its observed relationship with the representations is evaluated separately from the question of whether it improves downstream prediction.",
)
