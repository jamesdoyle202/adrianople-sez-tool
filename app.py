import streamlit as st

from components.manual_tool import render as render_manual
from config import GLOBAL_CSS, PAGE_LAYOUT, PAGE_TITLE

st.set_page_config(
    page_title=PAGE_TITLE,
    layout=PAGE_LAYOUT,
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

render_manual()
