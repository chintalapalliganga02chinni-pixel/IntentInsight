"""Methodology page."""
from __future__ import annotations

import streamlit as st

from intentinsight.presentation.dashboard.components import callout, header, section

header(
    "METHOD · OPERATIONAL DESIGN",
    "Methodology",
    "The operational chain behind IntentInsight: what enters the study, how intent and impact are represented, how divergence is formed, and how each research question is evaluated.",
)

section("The study design", "The application presents the established research design rather than introducing new analyses. The empirical core is frozen; the Workbench is a read-only inspection layer over validated research artifacts.", "DESIGN")

steps = [
    ("01", "Pull Request", "Eligible merged Pull Requests form the analytical population."),
    ("02", "Developer intent", "Title and description are used to represent what the developer says the change is intended to accomplish."),
    ("03", "Semantic representation", "Intent is encoded using transformer-based sentence embeddings."),
    ("04", "Structural impact", "Changed Python files are mapped into module-level structural information."),
    ("05", "Divergence", "Semantic and structural representations are compared to obtain Intent–Impact Divergence."),
    ("06", "Empirical evaluation", "Null-model, reconstruction/robustness and downstream analyses test increasingly stronger claims."),
]
for code, title, text in steps:
    st.markdown(
        f'<div class="ii-rq"><div class="ii-rq-head">{code}</div>'
        f'<div class="ii-rq-question">{title}</div>'
        f'<div class="ii-rq-meta">{text}</div></div>', unsafe_allow_html=True
    )

section("Research questions and operational tests", None, "TRACEABILITY")
rows = [
    ("RQ1", "Can developer intent and implemented structural impact be represented consistently?", "Complete matched representation population: 703 intent rows, 703 structural rows and 703 matching PR keys."),
    ("RQ2", "Does Intent–Impact Divergence capture meaningful semantic–structural characteristics of Pull Requests?", "10,000-permutation random-pairing null model; observed similarity 0.307207 versus random mean 0.241821."),
    ("RQ3", "Is the divergence measure robust to historical reconstruction and structural-scope confounders?", "Historical reconstruction with exact module-profile equivalence and current/historical divergence comparison."),
    ("RQ4", "Does Intent–Impact Divergence provide incremental predictive value for subsequent structural rework?", "Chronological downstream evaluation for 90-day structural rework; paired permutation comparison."),
]
for code, question, test in rows:
    st.markdown(
        f'<div class="ii-card" style="margin-bottom:.7rem;">'
        f'<div class="ii-card-label">{code}</div>'
        f'<div style="color:#f3f5f7;font-weight:680;line-height:1.5;">{question}</div>'
        f'<div class="ii-card-note" style="font-size:.86rem;margin-top:.6rem;">Operational test: {test}</div>'
        '</div>', unsafe_allow_html=True
    )

section("Downstream outcome", None, "RQ4")
callout(
    "90-day structural rework",
    "A subsequent merged Pull Request, within 90 days of the original merge, modifying at least one Python module affected by the original Pull Request. The analysis contains 702 fully observable cases: 531 with subsequent same-module structural rework and 171 without observed same-module structural rework; one right-censored observation is excluded from the primary outcome analysis.",
)

section("Interpretive discipline", None, "WHY THE ORDER MATTERS")
for item in [
    "Representation coverage is established before interpreting divergence.",
    "The null model tests whether observed pairing differs from arbitrary pairing.",
    "Historical reconstruction tests robustness of the structural representation.",
    "The downstream experiment is deliberately separate: a meaningful construct need not improve prediction.",
]:
    st.markdown(f"- {item}")

section("Methodological boundaries", None, "LIMITATIONS")
callout(
    "What cannot be inferred from these tests",
    "The evidence does not establish causality, does not make divergence a general quality score, and does not imply that divergence must be predictive in other datasets or outcomes. The conclusions are bounded by the representations, dataset, outcome definition and experimental protocol used in this study.",
)
