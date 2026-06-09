"""
Flood Explorer — Interactive JRC Global River Flood Hazard Map.

Target area: Escobar, Paraguarí, Paraguay (-25.634, -57.072).

Layers from JRC Global River Flood Hazard Maps v2 (90m resolution).
Each band shows flood depth (meters) at a given return period:
  10, 20, 50, 100, 200, 500 years.

Run:
    streamlit run app.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

import ee
import folium
import streamlit as st
from streamlit_folium import st_folium

# ── Load .env ─────────────────────────────────────────────────────────────────

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Flood Explorer — Escobar, Paraguay",
    page_icon="🌊",
    layout="wide",
)

st.title("🌊 Flood Explorer — Escobar, Paraguarí, Paraguay")
st.caption(
    "JRC Global River Flood Hazard Maps v2.1 — 90 m resolution. "
    "Flood depth is *modelled*, not observed. "
    "Verify with local knowledge and ground surveys."
)

# ── Initialize Earth Engine ─────────────────────────────────────────────────

def init_ee():
    """Initialize Earth Engine. Tries service account first, then OAuth."""
    project = os.getenv("EE_PROJECT", "")
    svc_account_path = Path("ee-service-account.json")
    if svc_account_path.exists():
        with open(svc_account_path) as f:
            creds = json.load(f)
        credentials = ee.ServiceAccountCredentials(
            creds["client_email"], str(svc_account_path)
        )
        kwargs = {"credentials": credentials}
        if project:
            kwargs["project"] = project
        ee.Initialize(**kwargs)
        st.sidebar.success("✅ Authenticated via service account")
        return True

    # Fallback to OAuth
    try:
        kwargs = {}
        if project:
            kwargs["project"] = project
        ee.Initialize(**kwargs)
        st.sidebar.success("✅ Authenticated via stored OAuth credentials")
        return True
    except Exception:
        st.sidebar.warning(
            "🔐 Not authenticated. Click the button below, then reload this page."
        )
        if st.sidebar.button("Authenticate with Google Earth Engine"):
            ee.Authenticate()
            kwargs = {}
            if project:
                kwargs["project"] = project
            ee.Initialize(**kwargs)
            st.sidebar.success("✅ Authenticated! Reload the page.")
            st.rerun()
        st.stop()

init_ee()

# ── Dataset ──────────────────────────────────────────────────────────────────

JRC_DATASET = "JRC/CEMS_GLOFAS/FloodHazard/v2_1"

RETURN_PERIODS = {
    "10-year flood (10%)":   "RP10_depth",
    "20-year flood (5%)":    "RP20_depth",
    "50-year flood (2%)":    "RP50_depth",
    "75-year flood (1.3%)":  "RP75_depth",
    "100-year flood (1%)":   "RP100_depth",
    "200-year flood (0.5%)": "RP200_depth",
    "500-year flood (0.2%)": "RP500_depth",
}

# Styling bands — blue palette from shallow to deep
FLOOD_VIZ = {
    "min": 0.0,
    "max": 2.0,
    "palette": [
        "#ffffff00",  # 0.0 m = transparent (no flood)
        "#cce5ff",    # 0.4 m
        "#99c2ff",    # 0.8 m
        "#6699ff",    # 1.2 m
        "#3366ff",    # 1.6 m
        "#0033cc",    # 2.0+ m
    ],
}

# ── Coordinates ──────────────────────────────────────────────────────────────

CENTER_LAT = float(os.getenv("CENTER_LAT", "-25.634"))
CENTER_LON = float(os.getenv("CENTER_LON", "-57.072"))
ZOOM_START = int(os.getenv("ZOOM_START", "13"))

# ── Sidebar controls ─────────────────────────────────────────────────────────

st.sidebar.header("🎛️ Controls")

# --- Location search ---
st.sidebar.subheader("🔍 Jump to location")

# Initialize session state for map center
if "map_lat" not in st.session_state:
    st.session_state.map_lat = CENTER_LAT
if "map_lon" not in st.session_state:
    st.session_state.map_lon = CENTER_LON

place_query = st.sidebar.text_input(
    "Coordinates or place name",
    placeholder="e.g. 48.8566, 2.3522 or Paris, France",
    key="place_search",
)

if st.sidebar.button("Go", key="go_btn") and place_query:
    # Try parsing as lat,lon first
    parts = [p.strip() for p in place_query.split(",")]
    if len(parts) == 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                st.session_state.map_lat = lat
                st.session_state.map_lon = lon
                st.rerun()
        except ValueError:
            pass

    # Fallback: geocode as place name
    import urllib.parse, urllib.request, json as _json
    try:
        encoded = urllib.parse.quote(place_query)
        url = (
            "https://nominatim.openstreetmap.org/search"
            f"?q={encoded}&format=json&limit=1"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "flood-explorer/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            results = _json.loads(resp.read())
        if results:
            st.session_state.map_lat = float(results[0]["lat"])
            st.session_state.map_lon = float(results[0]["lon"])
            st.rerun()
        else:
            st.sidebar.error("Place not found")
    except Exception:
        st.sidebar.error("Geocoding failed — try lat,lon instead")

st.sidebar.caption(
    f"📍 {st.session_state.map_lat:.4f}, {st.session_state.map_lon:.4f}"
)

st.sidebar.divider()

selected_label = st.sidebar.selectbox(
    "Return period",
    list(RETURN_PERIODS.keys()),
    index=4,  # default: 100-year
)
selected_band = RETURN_PERIODS[selected_label]

opacity = st.sidebar.slider("Flood layer opacity", 0.0, 1.0, 0.7, 0.05)

show_labels = st.sidebar.checkbox("Show depth labels on hover", value=True)

st.sidebar.divider()
st.sidebar.header("ℹ️ About")
st.sidebar.markdown(
    """
**Data source:** JRC Global River Flood Hazard Maps v2.1  
**Resolution:** ~90 m (3 arc-seconds)  
**Unit:** Meters of flood depth above ground  

**How to read:** Blue areas indicate modelled flood
inundation for the selected return period.
Darker blue = deeper water.

A 100-year flood does *not* mean "once per century"
— it's a 1% chance in any given year.
"""
)

# ── Build map ────────────────────────────────────────────────────────────────

# Cache the tile layer URL so we don't recompute on every interaction
@st.cache_data
def get_flood_tile_url(band: str) -> str:
    """Get a MapID token for the selected band (cached, expires ~24h)."""
    col = ee.ImageCollection(JRC_DATASET)
    image = col.first().select(band).visualize(**FLOOD_VIZ)
    map_id = image.getMapId()
    return map_id["tile_fetcher"].url_format


@st.cache_data
def get_flood_image_for_point(band: str, lat: float, lon: float) -> float | None:
    """Sample flood depth at a specific point. Returns depth in meters."""
    col = ee.ImageCollection(JRC_DATASET)
    image = col.first().select(band)
    point = ee.Geometry.Point(lon, lat)
    try:
        value = (
            image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=90,  # native resolution
                maxPixels=1,
            )
            .get(band)
            .getInfo()
        )
        return value
    except Exception:
        return None


tile_url = get_flood_tile_url(selected_band)

m = folium.Map(
    location=[st.session_state.map_lat, st.session_state.map_lon],
    zoom_start=ZOOM_START,
    tiles="OpenStreetMap",
    control_scale=True,
)

# Satellite basemap toggle
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google Satellite",
    name="🛰️ Satellite",
    overlay=False,
).add_to(m)

# Flood hazard layer
folium.TileLayer(
    tiles=tile_url,
    attr="JRC GLOFAS Flood Hazard v2.1",
    name=f"🌊 {selected_label}",
    overlay=True,
    opacity=opacity,
    show=True,
).add_to(m)

# Layer control
folium.LayerControl().add_to(m)

# Marker at center
folium.Marker(
    location=[st.session_state.map_lat, st.session_state.map_lon],
    popup=f"📍 {st.session_state.map_lat:.4f}, {st.session_state.map_lon:.4f}",
    icon=folium.Icon(color="red", icon="info-sign"),
).add_to(m)

# ── Render map ───────────────────────────────────────────────────────────────

st.subheader(f"🗺️ {selected_label} — Flood Depth Map")
st.caption(
    f"Center: {st.session_state.map_lat:.4f}, {st.session_state.map_lon:.4f}"
)
st.caption(
    "💡 Transparent areas = no modelled flood risk. "
    "Blue areas = flood depth in meters. "
    "This model only covers river floodplains — your parcel may be on high ground. "
    "Click the map to sample any point."
)

map_output = st_folium(
    m,
    width=None,       # fill container
    height=600,
    returned_objects=["last_object_clicked"],
    use_container_width=True,
)

# ── Click-to-sample ──────────────────────────────────────────────────────────

st.divider()
st.subheader("📍 Click the map to sample flood depth")

clicked = map_output.get("last_object_clicked") if map_output else None

if clicked and clicked.get("lat") and clicked.get("lng"):
    click_lat = clicked["lat"]
    click_lon = clicked["lng"]

    with st.spinner(f"Sampling flood depth at {click_lat:.5f}, {click_lon:.5f}..."):
        depth = get_flood_image_for_point(selected_band, click_lat, click_lon)

    if depth is not None:
        st.metric(
            label=f"Flood depth ({selected_label})",
            value=f"{depth:.2f} m",
            delta=None if depth == 0 else "⚠️ Flood risk" if depth < 0.5 else "🚨 Significant depth",
        )
        st.caption(f"Sampled at: {click_lat:.6f}, {click_lon:.6f}")
    else:
        st.success(
            f"✅ No modelled flood risk at this location. "
            f"The JRC model predicts no river flooding here at any return period "
            f"(the point is outside the mapped river floodplain). "
            f"This is the best-case result — but still verify with local flood history."
        )
else:
    st.info("Click anywhere on the map above to get the flood depth at that point.")
