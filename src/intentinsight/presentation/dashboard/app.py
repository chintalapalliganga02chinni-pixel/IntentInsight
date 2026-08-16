"""IntentInsight Research Workbench application shell."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from intentinsight.presentation.dashboard.theme import apply_theme


def main() -> None:
    """Configure and run the IntentInsight Research Workbench."""

    st.set_page_config(
        page_title="IntentInsight · Research Workbench",
        page_icon="II",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_theme()

    # -------------------------------------------------------------------------
    # Page definitions
    # -------------------------------------------------------------------------

    page_dir = Path(__file__).resolve().parent / "pages"

    overview = st.Page(
        str(page_dir / "overview.py"),
        title="Research Overview",
        icon=":material/menu_book:",
        default=True,
    )

    explorer = st.Page(
        str(page_dir / "pr_explorer.py"),
        title="Pull Request Explorer",
        url_path="explorer",
        icon=":material/search:",
    )

    detail = st.Page(
        str(page_dir / "pr_detail.py"),
        title="Pull Request Detail",
        url_path="pr-detail",
        icon=":material/article:",
    )

    divergence = st.Page(
        str(page_dir / "divergence.py"),
        title="Divergence Analysis",
        url_path="divergence",
        icon=":material/analytics:",
    )

    evidence = st.Page(
        str(page_dir / "evidence.py"),
        title="Evidence & Validation",
        url_path="evidence",
        icon=":material/fact_check:",
    )

    methodology = st.Page(
        str(page_dir / "methodology.py"),
        title="Methodology",
        url_path="methodology",
        icon=":material/account_tree:",
    )

    reproducibility = st.Page(
        str(page_dir / "reproducibility.py"),
        title="Reproducibility",
        url_path="reproducibility",
        icon=":material/verified:",
    )

    # -------------------------------------------------------------------------
    # Application navigation
    #
    # IMPORTANT:
    # The page objects above are the authoritative Streamlit navigation
    # targets. Other pages must use these objects rather than URL strings
    # with st.page_link().
    # -------------------------------------------------------------------------

    pages = st.navigation(
        {
            "Study": [
                overview,
                explorer,
                detail,
            ],
            "Evidence": [
                divergence,
                evidence,
            ],
            "Method": [
                methodology,
                reproducibility,
            ],
        },
        position="hidden",
    )

    # -------------------------------------------------------------------------
    # Custom sidebar
    # -------------------------------------------------------------------------

    with st.sidebar:

        st.markdown(
            '<div class="ii-brand-name">IntentInsight</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="ii-brand-subtitle">Research Workbench</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="ii-sidebar-rule"></div>',
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------------------
        # Study
        # ---------------------------------------------------------------------

        st.markdown(
            '<div class="ii-nav-heading">Study</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            overview,
            label="Research Overview",
            icon=":material/menu_book:",
            width="stretch",
        )

        st.page_link(
            explorer,
            label="Pull Request Explorer",
            icon=":material/search:",
            width="stretch",
        )

        st.page_link(
            detail,
            label="Pull Request Detail",
            icon=":material/article:",
            width="stretch",
        )

        st.markdown(
            '<div class="ii-sidebar-rule"></div>',
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------------------
        # Evidence
        # ---------------------------------------------------------------------

        st.markdown(
            '<div class="ii-nav-heading">Evidence</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            divergence,
            label="Divergence Analysis",
            icon=":material/analytics:",
            width="stretch",
        )

        st.page_link(
            evidence,
            label="Evidence & Validation",
            icon=":material/fact_check:",
            width="stretch",
        )

        st.markdown(
            '<div class="ii-sidebar-rule"></div>',
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------------------
        # Method
        # ---------------------------------------------------------------------

        st.markdown(
            '<div class="ii-nav-heading">Method</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            methodology,
            label="Methodology",
            icon=":material/account_tree:",
            width="stretch",
        )

        st.page_link(
            reproducibility,
            label="Reproducibility",
            icon=":material/verified:",
            width="stretch",
        )

        st.markdown(
            '<div class="ii-sidebar-rule"></div>',
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------------------
        # Study status
        # ---------------------------------------------------------------------

        st.markdown(
            '<div class="ii-sidebar-count">'
            "703 eligible Pull Requests"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="ii-sidebar-meta">'
            "Validated empirical study · read-only research artifacts"
            "</div>",
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # Run selected page
    # -------------------------------------------------------------------------

    pages.run()


if __name__ == "__main__":
    main()