import html
import json
from typing import Any, Dict, List

import requests
import streamlit as st
import streamlit.components.v1 as components

from components.navigation import render_back_link
from utils.github_api import GitHubAPIError, raw_geojson_url, read_geojson, read_index


@st.cache_data(ttl=60)
def load_index() -> List[Dict[str, Any]]:
    return read_index()


@st.cache_data(ttl=60)
def load_geojson(filename: str) -> str:
    return json.dumps(read_geojson(filename), indent=2)


def filter_by_country(
    entries: List[Dict[str, Any]],
    country: str,
) -> List[Dict[str, Any]]:
    if country == "All Countries":
        return entries
    return [entry for entry in entries if entry.get("country") == country]


def sort_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        entries,
        key=lambda entry: entry.get("date", ""),
        reverse=True,
    )


def render_entry(entry: Dict[str, Any], index: int) -> None:
    sez_name = html.escape(entry.get("sez_name", "Unknown SEZ"))
    country = html.escape(entry.get("country", "Unknown country"))
    contributor = html.escape(entry.get("contributor", "Unknown contributor"))
    saved_date = html.escape(entry.get("date", "Unknown date"))
    notes = html.escape(entry.get("notes", "").strip())
    filename = entry.get("file", "")

    st.markdown(
        f"""
        <div class="db-entry">
            <div class="db-entry-title">{sez_name}</div>
            <div class="db-entry-meta">Country: {country}</div>
            <div class="db-entry-meta">Contributor: {contributor}</div>
            <div class="db-entry-meta">Date: {saved_date}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if notes:
        st.markdown(
            f'<div class="db-entry-notes">Notes: {notes}</div>',
            unsafe_allow_html=True,
        )

    if not filename:
        st.caption("GeoJSON file not available for this entry.")
        return

    col1, col2 = st.columns(2)
    url = raw_geojson_url(filename)

    with col1:
        try:
            geojson_content = load_geojson(filename)
            st.download_button(
                label="Download GeoJSON",
                data=geojson_content,
                file_name=filename,
                mime="application/geo+json",
                key=f"download_{index}_{filename}",
                use_container_width=True,
            )
        except (GitHubAPIError, requests.RequestException, json.JSONDecodeError):
            st.caption("Download unavailable.")

    with col2:
        if st.button(
            "Copy GeoJSON URL",
            key=f"copy_{index}_{filename}",
            use_container_width=True,
        ):
            st.session_state["clipboard_url"] = url
            st.session_state["clipboard_notice"] = url

    st.markdown("<br>", unsafe_allow_html=True)


def render() -> None:
    render_back_link()
    st.markdown("# Polygon Database")
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        entries = sort_entries(load_index())
    except (GitHubAPIError, requests.RequestException, json.JSONDecodeError):
        st.error("Something went wrong — please try again.")
        return

    if not entries:
        st.markdown("No polygons yet — add your first one.")
        return

    countries = sorted({entry.get("country", "") for entry in entries if entry.get("country")})
    selected_country = st.selectbox(
        "Country",
        ["All Countries", *countries],
    )

    st.markdown("<br>", unsafe_allow_html=True)

    filtered_entries = filter_by_country(entries, selected_country)

    if not filtered_entries:
        st.markdown("No polygons match this country.")
        return

    if st.session_state.get("clipboard_notice"):
        components.html(
            f"""
            <script>
            navigator.clipboard.writeText({json.dumps(st.session_state["clipboard_url"])});
            </script>
            """,
            height=0,
        )
        st.caption("URL copied to clipboard.")
        st.session_state.pop("clipboard_notice", None)

    for index, entry in enumerate(filtered_entries):
        render_entry(entry, index)
