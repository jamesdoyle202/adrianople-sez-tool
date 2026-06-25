import json
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import folium
import requests
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

from components.import_tool import save_polygon
from components.navigation import render_back_link
from utils.github_api import GitHubAPIError

DEFAULT_CENTER = (20.0, 0.0)
DEFAULT_ZOOM = 2
COUNTRY_ZOOM = 5
ESRI_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "AdrianopleGroupSEZTool/1.0"


@st.cache_data(ttl=3600, show_spinner=False)
def geocode_country(country: str) -> Optional[Tuple[float, float]]:
    response = requests.get(
        NOMINATIM_URL,
        params={"country": country, "format": "json", "limit": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    if not response.ok:
        return None

    results = response.json()
    if not results:
        return None

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    return (lat, lon)


def init_map_state() -> None:
    if "manual_map_center" not in st.session_state:
        st.session_state.manual_map_center = DEFAULT_CENTER
    if "manual_map_zoom" not in st.session_state:
        st.session_state.manual_map_zoom = DEFAULT_ZOOM
    if "manual_geocoded_country" not in st.session_state:
        st.session_state.manual_geocoded_country = ""
    if "manual_saved_fingerprint" not in st.session_state:
        st.session_state.manual_saved_fingerprint = ""


def init_session_state() -> None:
    if "manual_session_active" not in st.session_state:
        st.session_state.manual_session_active = False


def update_map_center(country: str) -> None:
    country = country.strip()
    if not country:
        st.session_state.manual_map_center = DEFAULT_CENTER
        st.session_state.manual_map_zoom = DEFAULT_ZOOM
        st.session_state.manual_geocoded_country = ""
        return

    if country == st.session_state.manual_geocoded_country:
        return

    location = geocode_country(country)
    if location:
        st.session_state.manual_map_center = location
        st.session_state.manual_map_zoom = COUNTRY_ZOOM
        st.session_state.manual_geocoded_country = country


def start_session(country: str, collector: str, source: str, session_date: str) -> None:
    st.session_state.manual_session_active = True
    st.session_state.manual_session_country = country.strip()
    st.session_state.manual_session_collector = collector.strip()
    st.session_state.manual_session_source = source.strip()
    st.session_state.manual_session_date = session_date
    st.session_state.manual_saved_fingerprint = ""
    update_map_center(country)


def end_session() -> None:
    st.session_state.manual_session_active = False
    for key in (
        "manual_session_country",
        "manual_session_collector",
        "manual_session_source",
        "manual_session_date",
        "manual_map_center",
        "manual_map_zoom",
        "manual_geocoded_country",
        "manual_saved_fingerprint",
    ):
        st.session_state.pop(key, None)


def build_map(center: Tuple[float, float], zoom: int) -> folium.Map:
    map_obj = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles=ESRI_TILES,
        attr="Esri World Imagery",
        name="Esri World Imagery",
        overlay=False,
        control=False,
    ).add_to(map_obj)

    Draw(
        export=True,
        draw_options={
            "polyline": False,
            "rectangle": False,
            "polygon": True,
            "circle": False,
            "marker": False,
            "circlemarker": False,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(map_obj)

    return map_obj


def drawings_fingerprint(drawings: Any) -> str:
    if not drawings:
        return ""
    return json.dumps(drawings, sort_keys=True)


def polygon_features(drawings: Any) -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []
    if not isinstance(drawings, list):
        return features

    for drawing in drawings:
        if not isinstance(drawing, dict):
            continue

        if drawing.get("type") == "Feature":
            geometry = drawing.get("geometry", {})
            if geometry.get("type") == "Polygon":
                features.append(drawing)
            continue

        if drawing.get("type") == "Polygon":
            features.append(
                {
                    "type": "Feature",
                    "properties": drawing.get("properties", {}),
                    "geometry": drawing,
                }
            )
            continue

        geometry = drawing.get("geometry")
        if isinstance(geometry, dict) and geometry.get("type") == "Polygon":
            features.append(
                {
                    "type": "Feature",
                    "properties": drawing.get("properties", {}),
                    "geometry": geometry,
                }
            )

    return features


def to_feature_collection(drawings: Any) -> Dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": polygon_features(drawings),
    }


def clear_database_cache() -> None:
    try:
        from components.database import load_geojson, load_index

        load_index.clear()
        load_geojson.clear()
    except Exception:
        pass


def save_drawn_polygon(
    drawings: Any,
    sez_name: str,
    notes: str,
) -> None:
    features = polygon_features(drawings)
    if not features:
        st.error("Draw a polygon on the map before saving.")
        return

    if not sez_name.strip():
        st.error("SEZ Name is required.")
        return

    geojson_data = to_feature_collection(drawings)
    fingerprint = drawings_fingerprint(drawings)

    try:
        saved_sez_name = save_polygon(
            country=st.session_state.manual_session_country,
            sez_name=sez_name,
            source=st.session_state.manual_session_source,
            contributor=st.session_state.manual_session_collector,
            notes=notes,
            geojson_data=geojson_data,
            saved_date=st.session_state.manual_session_date,
        )
    except (GitHubAPIError, requests.RequestException, json.JSONDecodeError):
        st.error("Something went wrong — please try again.")
        return

    st.session_state.manual_saved_fingerprint = fingerprint
    clear_database_cache()
    st.success(f"{saved_sez_name} saved to database.")


def render_setup_form() -> None:
    today = date.today().isoformat()

    with st.form("manual_session_setup"):
        country = st.text_input("Country")
        collector = st.text_input("Collector name")
        source = st.text_input("Source")
        st.text_input("Date", value=today, disabled=True)
        submitted = st.form_submit_button("Start Session")

    if not submitted:
        return

    if not country.strip() or not collector.strip() or not source.strip():
        st.error("Country, Collector name, and Source are required.")
        return

    start_session(country, collector, source, today)
    st.rerun()


def render_active_session() -> None:
    country = st.session_state.manual_session_country
    collector = st.session_state.manual_session_collector
    source = st.session_state.manual_session_source
    session_date = st.session_state.manual_session_date

    info_col, action_col = st.columns([5, 1])
    with info_col:
        st.caption(f"Session: {country} | {collector} | {source} | {session_date}")
    with action_col:
        if st.button("End Session", key="manual_end_session", use_container_width=True):
            end_session()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    map_obj = build_map(
        st.session_state.manual_map_center,
        st.session_state.manual_map_zoom,
    )

    map_output = st_folium(
        map_obj,
        key="manual_extraction_map",
        height=500,
        use_container_width=True,
        returned_objects=["all_drawings"],
        center=st.session_state.manual_map_center,
        zoom=st.session_state.manual_map_zoom,
    )

    drawings = map_output.get("all_drawings") if map_output else None
    features = polygon_features(drawings)
    fingerprint = drawings_fingerprint(drawings)
    has_unsaved_polygons = bool(
        features and fingerprint != st.session_state.manual_saved_fingerprint
    )

    if not has_unsaved_polygons:
        st.caption("Draw a polygon on the map to save it.")
        return

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("manual_polygon_save", clear_on_submit=True):
        sez_name = st.text_input("SEZ Name")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save")

    if submitted:
        save_drawn_polygon(drawings, sez_name, notes)


def render() -> None:
    render_back_link(target="collection")
    st.markdown("# Manual Polygon Extraction")
    st.markdown("<br>", unsafe_allow_html=True)

    init_session_state()
    init_map_state()

    if st.session_state.manual_session_active:
        render_active_session()
    else:
        render_setup_form()
