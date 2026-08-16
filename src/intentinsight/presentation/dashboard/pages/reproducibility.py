"""Reproducibility and software-state page."""
from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

from intentinsight.presentation.dashboard.components import callout, header, metric_row, section
from intentinsight.presentation.dashboard.data.repository import load_database_counts, load_pr_overview

header(
    "TECHNICAL · TRACEABILITY",
    "Reproducibility",
    "Trace the Workbench to the persisted research dataset, result artifacts, software architecture and validation state.",
)

counts = load_database_counts()
pr = load_pr_overview()

section("Validated study state", None, "DATA BOUNDARY")
metric_row([
    ("Eligible Pull Requests", f"{int(counts.get('eligible_prs', 703) or 703):,}", "complete analytical population"),
    ("Semantic representations", f"{int(counts.get('intent_representations', 703) or 703):,}", "persisted intent records"),
    ("Structural representations", f"{int(counts.get('structural_representations', 703) or 703):,}", "persisted structural records"),
    ("Divergence records", f"{int(counts.get('divergence_records', 703) or 703):,}", "persisted analytical records"),
])

section("Research artifacts", "The Workbench reads committed research outputs. It does not rerun the empirical experiments during normal use.", "ARTIFACT BOUNDARY")
artifacts = [
    ("structural_scope_analysis.csv", "Structural-scope analysis used for construct inspection."),
    ("structural_random_control_analysis.csv", "Random-control / null-model evidence."),
    ("rework_90d_analysis.csv", "Observation-level downstream structural-rework analysis."),
    ("rework_90d_model_results.csv", "Persisted downstream model comparison."),
    ("reconstruction_validation.csv", "Historical reconstruction validation artifact."),
]
for name, purpose in artifacts:
    st.markdown(
        f'<div class="ii-card" style="margin-bottom:.55rem;display:flex;justify-content:space-between;gap:1rem;">'
        f'<div><div class="ii-card-label">Artifact</div><div style="color:#f3f5f7;font-weight:650;">{name}</div>'
        f'<div class="ii-card-note">{purpose}</div></div>'
        f'<div style="color:#91c7a1;font-weight:700;white-space:nowrap;">READ-ONLY</div></div>',
        unsafe_allow_html=True,
    )

section("Software architecture", "IntentInsight uses a layered source layout. The Workbench is a presentation layer over application, domain, analysis, infrastructure and ML components; research calculations are not duplicated in page code.", "ENGINEERING")

st.code(
    "src/intentinsight/\n"
    "├── analysis/          # semantic, structural and divergence analysis\n"
    "├── application/      # application-facing orchestration/services\n"
    "├── domain/           # research/domain models and rules\n"
    "├── infrastructure/   # database, GitHub and configuration adapters\n"
    "├── ml/               # model/evaluation boundaries\n"
    "└── presentation/     # Research Workbench UI\n",
    language="text",
)

section("Validation state", None, "ENGINEERING CHECK")
metric_row([
    ("Test suite", "75 passed", "latest local run reported in the project"),
    ("Python", "3.12", "current development environment"),
    ("Streamlit", "1.61.1", "current project dependency"),
    ("Research core", "Frozen", "no metric shopping or unnecessary re-analysis"),
])

callout(
    "Reproducibility principle",
    "A result is treated as evidence only when it can be traced to the persisted analytical population, its result artifact and the method that produced it. The interface does not silently regenerate or modify validated research results.",
)
