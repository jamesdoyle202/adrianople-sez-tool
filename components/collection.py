import streamlit as st

from components.navigation import go_to, render_back_link


def render() -> None:
    render_back_link()
    st.markdown("# Data Collection")
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Import Polygon Data", use_container_width=True):
            go_to("import")

    with col2:
        if st.button("Manual Polygon Extraction", use_container_width=True):
            go_to("manual_extraction")
