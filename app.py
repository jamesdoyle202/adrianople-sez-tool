import streamlit as st

from components import collection, database
from config import APP_NAME, GLOBAL_CSS, PAGE_LAYOUT, PAGE_TITLE

st.set_page_config(
    page_title=PAGE_TITLE,
    layout=PAGE_LAYOUT,
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    st.markdown(f"# {APP_NAME}")
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Polygon Database", use_container_width=True):
            st.session_state.page = "database"
            st.rerun()

    with col2:
        if st.button("Data Collection", use_container_width=True):
            st.session_state.page = "collection"
            st.rerun()

elif st.session_state.page == "database":
    database.render()

elif st.session_state.page == "collection":
    collection.render()
