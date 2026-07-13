import json
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import folium
import requests
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

from config import APP_NAME

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


def init_state() -> None:
    if "manual_session_active" not in st.session_state:
        st.session_state.manual_session_active = False
    if "manual_session_polygons" not in st.session_state:
        st.session_state.manual_session_polygons = []
    if "manual_map_center" not in st.session_state:
        st.session_state.manual_map_center = DEFAULT_CENTER
    if "manual_map_zoom" not in st.session_state:
        st.session_state.manual_map_zoom = DEFAULT_ZOOM
    if "manual_geocoded_country" not in st.session_state:
        st.session_state.manual_geocoded_country = ""
    if "manual_last_saved_fingerprint" not in st.session_state:
        st.session_state.manual_last_saved_fingerprint = ""


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
    st.session_state.manual_session_polygons = []
    st.session_state.manual_last_saved_fingerprint = ""
    update_map_center(country)


def end_session() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("manual_"):
            st.session_state.pop(key, None)
    st.session_state.manual_session_active = False
    st.session_state.manual_session_polygons = []


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
        export=False,
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


def feature_fingerprint(feature: Dict[str, Any]) -> str:
    return json.dumps(feature.get("geometry"), sort_keys=True)


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


def saved_geometry_fingerprints() -> set:
    return {
        feature_fingerprint(item["feature"])
        for item in st.session_state.manual_session_polygons
    }


def session_feature_collection() -> Dict[str, Any]:
    features = []
    for item in st.session_state.manual_session_polygons:
        feature = dict(item["feature"])
        properties = dict(feature.get("properties") or {})
        properties.update(
            {
                "sez_name": item["sez_name"],
                "notes": item.get("notes", ""),
                "country": st.session_state.manual_session_country,
                "collector": st.session_state.manual_session_collector,
                "source": st.session_state.manual_session_source,
                "date": st.session_state.manual_session_date,
            }
        )
        feature["properties"] = properties
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def save_drawn_polygon(drawings: Any, sez_name: str, notes: str) -> None:
    features = polygon_features(drawings)
    if not features:
        st.error("Draw a polygon on the map before saving.")
        return

    if not sez_name.strip():
        st.error("SEZ Name is required.")
        return

    already_saved = saved_geometry_fingerprints()
    new_features = [
        feature
        for feature in features
        if feature_fingerprint(feature) not in already_saved
    ]

    if not new_features:
        st.caption("These polygons are already saved in this session.")
        return

    base_name = sez_name.strip()
    for index, feature in enumerate(new_features, start=1):
        name = base_name if len(new_features) == 1 else f"{base_name} ({index})"
        st.session_state.manual_session_polygons.append(
            {
                "sez_name": name,
                "notes": notes.strip(),
                "feature": feature,
            }
        )

    st.session_state.manual_last_saved_fingerprint = drawings_fingerprint(drawings)
    if len(new_features) == 1:
        st.success(f"{base_name} saved.")
    else:
        st.success(f"Saved {len(new_features)} polygons.")


def render_setup_form() -> None:
    st.markdown(f"# {APP_NAME}")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Manual data collection")
    st.caption("Draw polygons on the map, then download them as GeoJSON when you are finished.")
    st.markdown("<br>", unsafe_allow_html=True)

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


def render_export_section() -> None:
    polygons = st.session_state.manual_session_polygons
    st.markdown("### Export")

    if not polygons:
        st.caption("Save at least one polygon to enable download.")
        return

    collection = session_feature_collection()
    country_slug = st.session_state.manual_session_country.lower().replace(" ", "_")
    filename = f"{country_slug}_session.geojson"

    st.download_button(
        label=f"Download {len(polygons)} polygon(s) as GeoJSON",
        data=json.dumps(collection, indent=2),
        file_name=filename,
        mime="application/geo+json",
        key="export_session_geojson",
        use_container_width=True,
    )
    st.caption("This file can be opened in geojson.io.")


def render_saved_list() -> None:
    polygons = st.session_state.manual_session_polygons
    if not polygons:
        return

    st.markdown("### Saved in this session")
    for index, item in enumerate(polygons, start=1):
        notes = item.get("notes", "").strip()
        line = f"{index}. {item['sez_name']}"
        if notes:
            line = f"{line} — {notes}"
        st.markdown(line)


def render_active_session() -> None:
    country = st.session_state.manual_session_country
    collector = st.session_state.manual_session_collector
    source = st.session_state.manual_session_source
    session_date = st.session_state.manual_session_date

    st.markdown(f"# {APP_NAME}")
    st.markdown("<br>", unsafe_allow_html=True)

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
    already_saved = saved_geometry_fingerprints()
    new_features = [
        feature
        for feature in features
        if feature_fingerprint(feature) not in already_saved
    ]

    if new_features:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("manual_polygon_save", clear_on_submit=True):
            sez_name = st.text_input("SEZ Name")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save")
        if submitted:
            save_drawn_polygon(drawings, sez_name, notes)
            st.rerun()
    else:
        st.caption("Draw a polygon on the map to save it.")

    st.markdown("<br>", unsafe_allow_html=True)
    render_saved_list()
    st.markdown("<br>", unsafe_allow_html=True)
    render_export_section()


def render() -> None:
    init_state()

    if st.session_state.manual_session_active:
        render_active_session()
    else:
        render_setup_form()
