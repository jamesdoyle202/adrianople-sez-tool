import streamlit as st

from components.navigation import render_back_link


def render() -> None:
    render_back_link()
    st.markdown("# Polygon Database — coming soon")
