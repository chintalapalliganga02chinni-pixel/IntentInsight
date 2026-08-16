"""Interactive Pull Request exploration over persisted analytical records."""
from __future__ import annotations

import streamlit as st

from intentinsight.presentation.dashboard.components import header, section
from intentinsight.presentation.dashboard.data.repository import load_pr_explorer, load_repositories

header(
    "EXPLORE · STUDY POPULATION",
    "Pull Request Explorer",
    "Search and filter the actual 703-Pull-Request study population, then open an observation as a case file.",
)

repositories = load_repositories()
repo_names = ["All repositories"]
if not repositories.empty and "full_name" in repositories.columns:
    repo_names += repositories["full_name"].dropna().astype(str).tolist()

c1, c2, c3 = st.columns([1.7, 1.0, .8], gap="small")
with c1:
    search = st.text_input("Search", placeholder="Repository, PR number, title or author")
with c2:
    repository = st.selectbox("Repository", repo_names)
with c3:
    sort = st.selectbox("Sort", ["Divergence", "Recent", "Modules"])

c4, c5 = st.columns(2, gap="small")
with c4:
    minimum = st.number_input(
        "Minimum divergence",
        min_value=0.0,
        max_value=2.0,
        value=0.0,
        step=0.01,
        format="%.2f",
    )
with c5:
    maximum = st.number_input(
        "Maximum divergence",
        min_value=0.0,
        max_value=2.0,
        value=2.0,
        step=0.01,
        format="%.2f",
    )

if minimum > maximum:
    st.error("Minimum divergence cannot exceed maximum divergence.")
    st.stop()

sort_map = {"Divergence": "intent_impact_divergence", "Recent": "merged_at", "Modules": "module_count"}
frame = load_pr_explorer(
    search_text=search,
    repository=repository,
    divergence_min=minimum,
    divergence_max=maximum,
    sort_by=sort_map[sort],
    descending=True,
)

section("Matching observations", f"{len(frame):,} observations match the current filters.", "FILTERED POPULATION")

if frame.empty:
    st.info("No Pull Requests match the current filters.")
    st.stop()

columns = [
    c for c in [
        "repository", "number", "title", "intent_impact_divergence",
        "intent_similarity", "module_count", "rework_90d",
    ] if c in frame.columns
]
display = frame[columns].copy()
rename = {
    "repository": "Repository",
    "number": "PR",
    "title": "Title",
    "intent_impact_divergence": "Divergence",
    "intent_similarity": "Similarity",
    "module_count": "Modules",
    "rework_90d": "90-day rework",
}
display = display.rename(columns=rename)
if "Divergence" in display:
    display["Divergence"] = display["Divergence"].map(lambda x: f"{float(x):.3f}" if x == x else "—")
if "Similarity" in display:
    display["Similarity"] = display["Similarity"].map(lambda x: f"{float(x):.3f}" if x == x else "—")

st.dataframe(display, use_container_width=True, hide_index=True, height=560)

st.caption("Select an observation by using the Pull Request Detail page. The Explorer itself never recomputes research metrics.")
