import streamlit as st

from components.manual_tool import render as render_manual
from components.matcher import render as render_matcher
from config import APP_NAME, GLOBAL_CSS, PAGE_LAYOUT, PAGE_TITLE

st.set_page_config(
    page_title=PAGE_TITLE,
    layout=PAGE_LAYOUT,
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "home"


def render_home() -> None:
    st.markdown(f"# {APP_NAME}")
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Manual Data Collection", use_container_width=True):
            st.session_state.page = "manual"
            st.rerun()

    with col2:
        if st.button("SEZ Polygon Matcher", use_container_width=True):
            st.session_state.page = "matcher"
            st.rerun()


PAGES = {
    "home": render_home,
    "manual": render_manual,
    "matcher": render_matcher,
}

page = st.session_state.page
if page not in PAGES:
    st.session_state.page = "home"
    st.rerun()

PAGES[page]()
