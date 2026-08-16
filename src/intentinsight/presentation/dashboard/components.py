"""Small presentation primitives shared by Workbench pages."""
from __future__ import annotations

from typing import Any

import streamlit as st


def header(eyebrow: str, title: str, lead: str) -> None:
    st.markdown(f'<div class="ii-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="ii-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="ii-lead">{lead}</div>', unsafe_allow_html=True)
    st.markdown('<div class="ii-rule"></div>', unsafe_allow_html=True)


def section(title: str, copy: str | None = None, kicker: str | None = None) -> None:
    if kicker:
        st.markdown(f'<div class="ii-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ii-section-title">{title}</div>', unsafe_allow_html=True)
    if copy:
        st.markdown(f'<div class="ii-section-copy">{copy}</div>', unsafe_allow_html=True)


def card(label: str, value: Any, note: str | None = None) -> str:
    note_html = f'<div class="ii-card-note">{note}</div>' if note else ''
    return (
        '<div class="ii-card">'
        f'<div class="ii-card-label">{label}</div>'
        f'<div class="ii-card-value">{value}</div>'
        f'{note_html}</div>'
    )


def callout(title: str, text: str, tone: str = "") -> None:
    st.markdown(
        f'<div class="ii-callout {tone}">'
        f'<div class="ii-callout-title">{title}</div>'
        f'<div class="ii-callout-text">{text}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def metric_row(items: list[tuple[str, Any, str | None]]) -> None:
    cols = st.columns(len(items), gap="small")
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(card(label, value, note), unsafe_allow_html=True)
