"""Evidence and validation: the empirical results in research-question order."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from intentinsight.presentation.dashboard.components import callout, header, metric_row, section
from intentinsight.presentation.dashboard.data.repository import (
    load_predictive_results,
    load_random_control_results,
    load_rework_analysis,
)

header(
    "EVIDENCE · VALIDATION",
    "Evidence & Validation",
    "A traceable account of what was tested, what the evidence supports, and where the conclusions stop.",
)

section(
    "RQ2 · Does divergence capture meaningful semantic–structural characteristics?",
    "The first empirical test compares the observed semantic–structural pairing against random pairings of the same representations. The validated null model used 10,000 permutations over the complete 703-PR matched population.",
    "REPRESENTATION ALIGNMENT",
)
metric_row([
    ("Observed similarity", "0.307207", "mean cosine similarity"),
    ("Random mean", "0.241821", "random-pairing null"),
    ("Difference", "+0.065386", "observed − random"),
    ("Permutation p", "0.0001", "10,000 permutations"),
])

callout(
    "Finding",
    "Observed intent–structure pairings were substantially more similar than arbitrary pairings. This supports a non-random relationship in representation space. It does not establish predictive success.",
    "positive",
)

random_control = load_random_control_results()
if not random_control.empty:
    numeric = random_control.select_dtypes(include="number")
    candidate = next((c for c in numeric.columns if "similar" in c.lower() or "score" in c.lower()), None)
    if candidate:
        section("Null-model distribution", "The persisted permutation/control values are shown without recomputing the experiment.", "10,000 PERMUTATIONS")
        st.line_chart(numeric[candidate].reset_index(drop=True), height=260, use_container_width=True)
        with st.expander("Inspect persisted null-model artifact"):
            st.dataframe(random_control, use_container_width=True, hide_index=True)

section(
    "RQ3 · Is the divergence measure robust to historical reconstruction?",
    "Historical reconstruction tests whether the structural representation remains coherent when the repository is reconstructed at the relevant historical state rather than inferred only from the current repository state.",
    "HISTORICAL RECONSTRUCTION",
)
metric_row([
    ("Exact reconstruction", "703 / 703", "exact module-profile equivalence"),
    ("Historical/current r", "0.944004", "divergence correlation"),
    ("Identical divergence", "47.65%", "335 of 703 observations"),
])
callout(
    "Finding",
    "Historical structural reconstruction achieved exact module-profile equivalence for all 703 analysed Pull Requests. Current and historical divergence were strongly correlated. Together, these results support the robustness of the structural representation under the tested reconstruction procedure.",
    "positive",
)

section(
    "RQ4 · Does divergence provide incremental predictive value?",
    "The downstream experiment used a chronological train/test split to avoid temporal leakage. The outcome was structural rework observed within 90 days; one right-censored observation was excluded from the primary outcome analysis, leaving 702 observable cases.",
    "DOWNSTREAM EVALUATION",
)
predictive = load_predictive_results()
base = 0.564427
with_div = 0.560606
if not predictive.empty and {"model", "roc_auc"}.issubset(predictive.columns):
    rows = predictive.set_index("model")
    if "baseline" in rows.index:
        base = float(rows.loc["baseline", "roc_auc"])
    if "baseline_plus_divergence" in rows.index:
        with_div = float(rows.loc["baseline_plus_divergence", "roc_auc"])
metric_row([
    ("Baseline ROC-AUC", f"{base:.4f}", "baseline model"),
    ("Baseline + divergence", f"{with_div:.4f}", "same evaluation design"),
    ("Observed difference", f"{with_div-base:+.4f}", "incremental change"),
    ("Paired permutation p", "0.729627", "downstream comparison"),
])

comparison = pd.DataFrame(
    {"ROC-AUC": [base, with_div]},
    index=["Baseline", "Baseline + divergence"],
)
st.bar_chart(comparison, height=250, use_container_width=True)

callout(
    "Finding",
    "The selected 90-day structural-rework experiment did not detect statistically significant incremental predictive value from divergence. The observed difference was −0.003821, with a 10,000-sample bootstrap 95% CI of [−0.024571, +0.018007]. This negative result is part of the empirical contribution and is not treated as a failure to be hidden or tuned away.",
    "negative",
)

section("What the evidence establishes", None, "SYNTHESIS")
for title, text in [
    ("Established", "The semantic and structural representations exhibit non-random alignment across the complete 703-PR study population."),
    ("Validated", "Historical structural reconstruction achieved exact module-profile equivalence for 703/703 Pull Requests."),
    ("Not established", "The tested divergence measure did not demonstrate incremental predictive usefulness for the selected 90-day structural-rework outcome."),
]:
    st.markdown(
        f'<div class="ii-card" style="margin-bottom:.7rem;"><div class="ii-card-label">{title}</div>'
        f'<div style="color:#c0c9d3;line-height:1.65;">{text}</div></div>',
        unsafe_allow_html=True,
    )
