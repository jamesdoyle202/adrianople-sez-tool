import json
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import folium
import requests
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

from components.navigation import render_back_link
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
    if "named_polygons" not in st.session_state:
        st.session_state.named_polygons = []
    if "manual_session_active" not in st.session_state:
        st.session_state.manual_session_active = False
    if "manual_map_center" not in st.session_state:
        st.session_state.manual_map_center = DEFAULT_CENTER
    if "manual_map_zoom" not in st.session_state:
        st.session_state.manual_map_zoom = DEFAULT_ZOOM
    if "manual_geocoded_country" not in st.session_state:
        st.session_state.manual_geocoded_country = ""
    if "manual_map_version" not in st.session_state:
        st.session_state.manual_map_version = 0


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
    st.session_state.named_polygons = []
    st.session_state.manual_map_version = 0
    update_map_center(country)


def end_session() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("manual_") or key in ("named_polygons", "zone_name_input"):
            st.session_state.pop(key, None)
    st.session_state.manual_session_active = False
    st.session_state.named_polygons = []


def reset_draw_state() -> None:
    """Remount the map so Leaflet.draw starts fresh for the next polygon."""
    st.session_state.manual_map_version += 1
    st.session_state.pop("zone_name_input", None)


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


def normalize_feature(drawing: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(drawing, dict):
        return None

    if drawing.get("type") == "Feature":
        geometry = drawing.get("geometry") or {}
        if geometry.get("type") == "Polygon":
            return {
                "type": "Feature",
                "properties": dict(drawing.get("properties") or {}),
                "geometry": geometry,
            }
        return None

    if drawing.get("type") == "Polygon":
        return {
            "type": "Feature",
            "properties": dict(drawing.get("properties") or {}),
            "geometry": drawing,
        }

    geometry = drawing.get("geometry")
    if isinstance(geometry, dict) and geometry.get("type") == "Polygon":
        return {
            "type": "Feature",
            "properties": dict(drawing.get("properties") or {}),
            "geometry": geometry,
        }

    return None


def most_recent_polygon(map_output: Any) -> Optional[Dict[str, Any]]:
    if not map_output:
        return None

    last_active = normalize_feature(map_output.get("last_active_drawing"))
    if last_active is not None:
        return last_active

    drawings = map_output.get("all_drawings") or []
    if not isinstance(drawings, list):
        return None

    for drawing in reversed(drawings):
        feature = normalize_feature(drawing)
        if feature is not None:
            return feature

    return None


def export_feature_collection() -> Dict[str, Any]:
    features: List[Dict[str, Any]] = []
    for feature in st.session_state.named_polygons:
        exported = {
            "type": "Feature",
            "properties": dict(feature.get("properties") or {}),
            "geometry": feature.get("geometry"),
        }
        exported["properties"].update(
            {
                "country": st.session_state.get("manual_session_country", ""),
                "collector": st.session_state.get("manual_session_collector", ""),
                "source": st.session_state.get("manual_session_source", ""),
                "date": st.session_state.get("manual_session_date", ""),
            }
        )
        features.append(exported)

    return {"type": "FeatureCollection", "features": features}


def save_named_polygon(feature: Dict[str, Any], zone_name: str) -> None:
    name = zone_name.strip()
    if not name:
        st.error("Zone Name is required.")
        return

    named_feature = {
        "type": "Feature",
        "properties": dict(feature.get("properties") or {}),
        "geometry": feature.get("geometry"),
    }
    named_feature["properties"]["name"] = name
    st.session_state.named_polygons.append(named_feature)
    reset_draw_state()
    st.success(f"{name} saved.")
    st.rerun()


def render_setup_form() -> None:
    render_back_link(target="home")
    st.markdown(f"# {APP_NAME}")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Manual data collection")
    st.caption("Draw polygons on the map, name each one, then download GeoJSON when finished.")
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


def render_saved_list() -> None:
    polygons = st.session_state.named_polygons
    if not polygons:
        return

    st.markdown("### Named polygons")
    for index, feature in enumerate(polygons, start=1):
        name = (feature.get("properties") or {}).get("name", f"Polygon {index}")
        st.markdown(f"{index}. {name}")


def render_export_section() -> None:
    polygons = st.session_state.named_polygons
    st.markdown("### Export")

    if not polygons:
        st.caption("Save at least one named polygon to enable download.")
        return

    collection = export_feature_collection()
    country_slug = st.session_state.manual_session_country.lower().replace(" ", "_")
    filename = f"{country_slug}_session.geojson"

    st.download_button(
        label=f"Download {len(polygons)} polygon(s) as GeoJSON",
        data=json.dumps(collection, indent=2),
        file_name=filename,
        mime="application/geo+json",
        key="export_named_polygons",
        use_container_width=True,
    )
    st.caption("This file can be opened in geojson.io. Each feature includes a name property.")


def render_active_session() -> None:
    country = st.session_state.manual_session_country
    collector = st.session_state.manual_session_collector
    source = st.session_state.manual_session_source
    session_date = st.session_state.manual_session_date

    render_back_link(target="home")
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
        key=f"manual_extraction_map_{st.session_state.manual_map_version}",
        height=500,
        use_container_width=True,
        returned_objects=["all_drawings", "last_active_drawing"],
        center=st.session_state.manual_map_center,
        zoom=st.session_state.manual_map_zoom,
    )

    latest_feature = most_recent_polygon(map_output)

    if latest_feature is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        zone_name = st.text_input("Zone Name", key="zone_name_input")
        if st.button("Save Polygon", key="save_named_polygon", use_container_width=True):
            save_named_polygon(latest_feature, zone_name)
    else:
        st.caption("Draw a polygon on the map, then give it a zone name.")

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
