import streamlit as st


def go_home() -> None:
    st.session_state.page = "home"
    st.rerun()


def render_back_link(label: str = "Back") -> None:
    if st.button(label, key=f"back_{st.session_state.page}", type="tertiary"):
        go_home()
