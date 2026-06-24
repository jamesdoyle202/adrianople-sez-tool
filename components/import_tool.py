import json
import re
from datetime import date
from typing import Any, Optional

import streamlit as st

from components.navigation import render_back_link
from config import INDEX_FILE, POLYGONS_DIR


def normalize(value: str) -> str:
    cleaned = value.lower().strip()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def filename_for(country: str, sez_name: str) -> str:
    country_slug = normalize(country).replace(" ", "_")
    sez_slug = normalize(sez_name).replace(" ", "_")
    return f"{country_slug}_{sez_slug}.geojson"


def load_index() -> list[dict[str, Any]]:
    if not INDEX_FILE.exists():
        return []

    with INDEX_FILE.open(encoding="utf-8") as index_file:
        data = json.load(index_file)

    return data if isinstance(data, list) else []


def save_index(entries: list[dict[str, Any]]) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_FILE.open("w", encoding="utf-8") as index_file:
        json.dump(entries, index_file, indent=2)
        index_file.write("\n")


def find_existing_index(entries: list[dict[str, Any]], country: str, sez_name: str) -> Optional[int]:
    country_normalized = normalize(country)
    sez_name_normalized = normalize(sez_name)

    for index, entry in enumerate(entries):
        if (
            entry.get("country_normalized") == country_normalized
            and entry.get("sez_name_normalized") == sez_name_normalized
        ):
            return index

    return None


def build_entry(
    country: str,
    sez_name: str,
    source: str,
    contributor: str,
    notes: str,
    saved_date: str,
    filename: str,
) -> dict[str, Any]:
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
    geojson_data: dict[str, Any],
) -> str:
    entries = load_index()
    filename = filename_for(country, sez_name)
    saved_date = date.today().isoformat()
    entry = build_entry(
        country=country,
        sez_name=sez_name,
        source=source,
        contributor=contributor,
        notes=notes,
        saved_date=saved_date,
        filename=filename,
    )

    existing_index = find_existing_index(entries, country, sez_name)
    if existing_index is not None:
        entries[existing_index] = entry
    else:
        entries.append(entry)

    POLYGONS_DIR.mkdir(parents=True, exist_ok=True)
    polygon_path = POLYGONS_DIR / filename
    with polygon_path.open("w", encoding="utf-8") as polygon_file:
        json.dump(geojson_data, polygon_file, indent=2)
        polygon_file.write("\n")

    save_index(entries)
    return sez_name.strip()


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

    saved_sez_name = save_polygon(
        country=country,
        sez_name=sez_name,
        source=source,
        contributor=contributor,
        notes=notes,
        geojson_data=geojson_data,
    )
    st.success(f"{saved_sez_name} saved.")
