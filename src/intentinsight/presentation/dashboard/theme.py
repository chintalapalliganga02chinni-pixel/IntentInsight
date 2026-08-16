"""Visual system for the IntentInsight Research Workbench."""
from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    """Apply an explicit application theme; never inherit browser colours."""
    st.markdown(
        """
<style>
:root {
  --ii-bg: #0b0e12;
  --ii-surface: #11161c;
  --ii-surface-2: #151b22;
  --ii-border: #29323d;
  --ii-text: #f3f5f7;
  --ii-text-2: #c0c9d3;
  --ii-muted: #8995a3;
  --ii-accent: #9ab9dc;
  --ii-accent-strong: #c7dbf2;
  --ii-positive: #91c7a1;
  --ii-warning: #d8b56f;
  --ii-negative: #d58c8c;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
  background: var(--ii-bg) !important;
  color: var(--ii-text) !important;
}

[data-testid="stHeader"] { background: var(--ii-bg) !important; }
[data-testid="stToolbar"] { visibility: visible; }

.block-container {
  max-width: 1240px;
  padding: 2.5rem 3.25rem 5rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #0d1116 !important;
  border-right: 1px solid var(--ii-border) !important;
}
section[data-testid="stSidebar"] > div {
  background: #0d1116 !important;
}
section[data-testid="stSidebar"] * {
  color: var(--ii-text-2) !important;
}
section[data-testid="stSidebar"] .ii-brand-name,
section[data-testid="stSidebar"] .ii-sidebar-count {
  color: var(--ii-text) !important;
}
section[data-testid="stSidebar"] .ii-nav-heading {
  color: #8298b2 !important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
  color: var(--ii-text-2) !important;
  border-radius: 7px !important;
  margin: 2px 0 !important;
  padding: 0.38rem 0.55rem !important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
  background: #171d25 !important;
  color: var(--ii-text) !important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
  background: #1b222c !important;
  color: var(--ii-text) !important;
  box-shadow: inset 2px 0 0 var(--ii-accent);
}
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] svg {
  color: currentColor !important;
}

/* Native Streamlit text */
.stMarkdown, .stText, p, li, label, [data-testid="stCaptionContainer"] {
  color: var(--ii-text-2) !important;
}
h1, h2, h3, h4, h5, h6 { color: var(--ii-text) !important; }

.ii-eyebrow {
  color: #89a5c5 !important;
  font-size: .69rem;
  font-weight: 750;
  letter-spacing: .18em;
  text-transform: uppercase;
  margin: 0 0 .65rem;
}
.ii-title {
  color: var(--ii-text) !important;
  font-size: 2.7rem;
  line-height: 1.06;
  letter-spacing: -.045em;
  font-weight: 760;
  margin: 0;
}
.ii-lead {
  color: var(--ii-text-2) !important;
  font-size: 1.03rem;
  line-height: 1.7;
  max-width: 980px;
  margin-top: .9rem;
}
.ii-rule { height: 1px; background: var(--ii-border); margin: 2rem 0 2.25rem; }
.ii-kicker {
  color: #8298b2 !important;
  font-size: .68rem;
  font-weight: 750;
  letter-spacing: .15em;
  text-transform: uppercase;
  margin-bottom: .45rem;
}
.ii-section-title {
  color: var(--ii-text) !important;
  font-size: 1.55rem;
  line-height: 1.2;
  letter-spacing: -.025em;
  font-weight: 720;
  margin: 0 0 .45rem;
}
.ii-section-copy {
  color: var(--ii-text-2) !important;
  line-height: 1.68;
  max-width: 980px;
  margin-bottom: 1rem;
}

.ii-card {
  background: var(--ii-surface) !important;
  border: 1px solid var(--ii-border) !important;
  border-radius: 10px;
  padding: 1.05rem 1.15rem;
  height: 100%;
  box-sizing: border-box;
}
.ii-card-label {
  color: #8398b1 !important;
  font-size: .64rem;
  font-weight: 760;
  letter-spacing: .14em;
  text-transform: uppercase;
  margin-bottom: .45rem;
}
.ii-card-value {
  color: var(--ii-text) !important;
  font-size: 1.72rem;
  line-height: 1.05;
  font-weight: 760;
  letter-spacing: -.025em;
}
.ii-card-note {
  color: var(--ii-muted) !important;
  font-size: .78rem;
  line-height: 1.45;
  margin-top: .45rem;
}

.ii-callout {
  background: var(--ii-surface) !important;
  border: 1px solid var(--ii-border) !important;
  border-left: 3px solid var(--ii-accent) !important;
  border-radius: 8px;
  padding: 1rem 1.15rem;
}
.ii-callout.warning { border-left-color: var(--ii-warning) !important; }
.ii-callout.negative { border-left-color: var(--ii-negative) !important; }
.ii-callout.positive { border-left-color: var(--ii-positive) !important; }
.ii-callout-title { color: var(--ii-text) !important; font-weight: 720; margin-bottom: .35rem; }
.ii-callout-text { color: var(--ii-text-2) !important; line-height: 1.6; }

.ii-rq {
  background: #10151b !important;
  border: 1px solid var(--ii-border) !important;
  border-radius: 9px;
  padding: 1.05rem 1.15rem;
  margin-bottom: .7rem;
}
.ii-rq-head { color: #87a1bf !important; font-size: .65rem; font-weight: 760; letter-spacing: .13em; text-transform: uppercase; }
.ii-rq-question { color: var(--ii-text) !important; font-size: 1.02rem; line-height: 1.5; font-weight: 650; margin-top: .3rem; }
.ii-rq-meta { color: var(--ii-muted) !important; font-size: .78rem; margin-top: .5rem; }

.ii-result-row {
  display: grid;
  grid-template-columns: 1.2fr .9fr .9fr;
  gap: .75rem;
  margin: .8rem 0 1rem;
}
.ii-result {
  background: var(--ii-surface);
  border: 1px solid var(--ii-border);
  border-radius: 8px;
  padding: .9rem 1rem;
}
.ii-result-label { color: #8298b2 !important; font-size: .62rem; font-weight: 760; letter-spacing: .12em; text-transform: uppercase; }
.ii-result-value { color: var(--ii-text) !important; font-size: 1.45rem; font-weight: 750; margin-top: .3rem; }

.ii-nav-heading {
  font-size: .63rem !important;
  font-weight: 760 !important;
  letter-spacing: .16em;
  text-transform: uppercase;
  margin: .35rem 0 .45rem;
}
.ii-brand-name { font-size: 1.05rem; font-weight: 760; }
.ii-brand-subtitle { color: #8e9aa7 !important; font-size: .75rem; margin-top: .2rem; }
.ii-sidebar-rule { height: 1px; background: #252d36; margin: 1rem 0; }
.ii-sidebar-meta { color: #8d99a7 !important; font-size: .72rem; line-height: 1.7; }
.ii-sidebar-count { font-size: .78rem; font-weight: 720; }

/* Inputs / buttons / dataframes */
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
  background: #10151b !important;
  color: var(--ii-text) !important;
  border-color: var(--ii-border) !important;
}
.stTextInput input::placeholder { color: #667382 !important; }
button, [data-testid="stButton"] button {
  color: var(--ii-text) !important;
}
[data-testid="stDataFrame"] {
  border: 1px solid var(--ii-border) !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}

/* Reduce Streamlit's excessive vertical rhythm */
div[data-testid="stVerticalBlock"] > div:has(> div.stMarkdown) { margin-bottom: 0 !important; }
.stPlotlyChart, [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] { margin-top: .25rem; }

@media (max-width: 900px) {
  .block-container { padding: 1.5rem 1.1rem 3rem; }
  .ii-title { font-size: 2.05rem; }
  .ii-result-row { grid-template-columns: 1fr; }
}
</style>
        """,
        unsafe_allow_html=True,
    )
