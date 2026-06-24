import streamlit as st


def go_to(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def go_home() -> None:
    go_to("home")


def render_back_link(label: str = "Back", target: str = "home") -> None:
    if st.button(
        label,
        key=f"back_{st.session_state.page}_{target}",
        type="tertiary",
    ):
        go_to(target)
