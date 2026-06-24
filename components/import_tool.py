import json
import re
from datetime import date
from typing import Any, Dict, List

import requests
import streamlit as st

from components.navigation import render_back_link
from utils.github_api import (
    GitHubAPIError,
    check_duplicate,
    read_index,
    write_geojson,
    write_index,
)


def normalize(value: str) -> str:
    cleaned = value.lower().strip()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def filename_for(country: str, sez_name: str) -> str:
    country_slug = normalize(country).replace(" ", "_")
    sez_slug = normalize(sez_name).replace(" ", "_")
    return f"{country_slug}_{sez_slug}.geojson"


def build_entry(
    country: str,
    sez_name: str,
    source: str,
    contributor: str,
    notes: str,
    saved_date: str,
    filename: str,
) -> Dict[str, Any]:
    return {
        "country": country.strip(),
        "sez_name": sez_name.strip(),
        "country_normalized": normalize(country),
        "sez_name_normalized": normalize(sez_name),
        "source": source.strip(),
        "contributor": contributor.strip(),
        "notes": notes.strip(),
        "date": saved_date,
        "file": filename,
    }


def save_polygon(
    country: str,
    sez_name: str,
    source: str,
    contributor: str,
    notes: str,
    geojson_data: Dict[str, Any],
) -> str:
    entries = read_index()
    filename = filename_for(country, sez_name)
    saved_date = date.today().isoformat()
    country_normalized = normalize(country)
    sez_name_normalized = normalize(sez_name)
    entry = build_entry(
        country=country,
        sez_name=sez_name,
        source=source,
        contributor=contributor,
        notes=notes,
        saved_date=saved_date,
        filename=filename,
    )

    existing_entry = check_duplicate(entries, country_normalized, sez_name_normalized)
    if existing_entry is not None:
        for index, current_entry in enumerate(entries):
            if (
                current_entry.get("country_normalized") == country_normalized
                and current_entry.get("sez_name_normalized") == sez_name_normalized
            ):
                entries[index] = entry
                break
        action = "Update"
    else:
        entries.append(entry)
        action = "Add"

    display_name = sez_name.strip()
    commit_message = f"{action} {display_name} polygon"

    write_geojson(filename, geojson_data, commit_message)
    write_index(entries, commit_message)

    return display_name


def render() -> None:
    render_back_link(target="collection")
    st.markdown("# Import Polygon Data")
    st.markdown("<br>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop a GeoJSON or JSON file here",
        type=["geojson", "json"],
    )

    if uploaded_file is None:
        return

    try:
        geojson_data = json.loads(uploaded_file.getvalue())
    except json.JSONDecodeError:
        st.error("This file is not valid JSON.")
        return

    if not isinstance(geojson_data, dict):
        st.error("This file does not contain a valid GeoJSON object.")
        return

    st.markdown("<br>", unsafe_allow_html=True)
    today = date.today().isoformat()

    with st.form("import_metadata"):
        country = st.text_input("Country")
        sez_name = st.text_input("SEZ Name")
        source = st.text_input("Source")
        contributor = st.text_input("Contributor")
        notes = st.text_area("Notes")
        st.text_input("Date", value=today, disabled=True)

        submitted = st.form_submit_button("Save")

    if not submitted:
        return

    if not country.strip() or not sez_name.strip():
        st.error("Country and SEZ Name are required.")
        return

    if not source.strip() or not contributor.strip():
        st.error("Source and Contributor are required.")
        return

    try:
        saved_sez_name = save_polygon(
            country=country,
            sez_name=sez_name,
            source=source,
            contributor=contributor,
            notes=notes,
            geojson_data=geojson_data,
        )
    except (GitHubAPIError, requests.RequestException, json.JSONDecodeError):
        st.error("Something went wrong — please try again.")
        return

    st.success(f"{saved_sez_name} saved to database.")
