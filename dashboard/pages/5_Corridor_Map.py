"""Page 5 — Corridor Map.

Maps to brief output #5: an interactive map of Patna with all 28 corridors
colour-coded by Peak-Hour Congestion Index. Designed for state govt and
press sharing.

Each corridor is drawn along its actual road geometry, sourced from
`corridor_polylines.json` (built one-time via `tools/fetch_corridor_polylines.py`
using the free OpenStreetMap Routing Machine demo server). The polylines
are for DISPLAY ONLY — Congestion Ratio metrics are calculated on Google's
own route choice for each measurement, which is route-invariant (both
numerator and denominator come from the same Google route per call).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from data import load_observations
from metrics import ranking_table

st.set_page_config(page_title="Corridor Map", page_icon="🗺️", layout="wide")


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
POLYLINES_FILE = PROJECT_DIR / "corridor_polylines.json"


@st.cache_data(ttl=600)
def _load():
    return load_observations()


@st.cache_data
def _load_polylines() -> dict:
    """Load the OSRM-fetched road polylines, or return empty dict if missing."""
    if not POLYLINES_FILE.exists():
        return {}
    try:
        return json.loads(POLYLINES_FILE.read_text())
    except json.JSONDecodeError:
        return {}


df = _load()
polylines = _load_polylines()

st.title("Patna — Corridor Congestion Map")
st.caption(
    "Brief output #5 — all 28 corridors of Patna, drawn along their actual "
    "road geometry and colour-coded by Peak-Hour Congestion Index (PHCI). "
    "Hover any corridor for its full statistics. Suitable for sharing with "
    "the State Government and the press."
)

if df.empty:
    st.warning("No observations yet.")
    st.stop()

if not polylines:
    st.warning(
        "`corridor_polylines.json` not found. The map is falling back to "
        "straight lines between corridor endpoints. To get road-following "
        "geometry, run `python tools/fetch_corridor_polylines.py` once and "
        "commit the resulting JSON."
    )

ranking = ranking_table(df)

# Build per-corridor geometry (one row per corridor; both directions follow
# the same physical road in essentially all of Patna).
geom = (
    df[["corridor_id", "corridor_name", "origin_lat", "origin_lng",
        "dest_lat", "dest_lng", "est_distance_km"]]
    .drop_duplicates(subset=["corridor_id"])
    .reset_index(drop=True)
)
display = geom.merge(ranking[["corridor_id", "phci", "adci", "bti", "phci_hour"]],
                     on="corridor_id", how="left")
display["phci"] = display["phci"].fillna(1.0)


def phci_to_rgb(v: float) -> list[int]:
    """Map a PHCI value to an RGB triplet on the same scale as the heatmap."""
    if pd.isna(v):
        return [156, 163, 175]  # grey
    if v < 1.0:
        return [59, 130, 246]   # blue
    if v < 1.25:
        return [252, 211, 77]   # pale orange
    if v < 1.5:
        return [249, 115, 22]   # orange
    if v < 2.0:
        return [220, 38, 38]    # red
    return [127, 29, 29]        # dark red


def coords_for(corridor_id: str, origin_lng: float, origin_lat: float,
               dest_lng: float, dest_lat: float) -> list[list[float]]:
    """Return the polyline for this corridor — OSRM road path if available,
    otherwise a two-point straight-line fallback."""
    key = f"{corridor_id}__A_to_B"
    entry = polylines.get(key)
    if entry and entry.get("coords"):
        return entry["coords"]
    return [[origin_lng, origin_lat], [dest_lng, dest_lat]]


display["color_rgb"] = display["phci"].apply(phci_to_rgb)
display["color_r"] = display["color_rgb"].apply(lambda c: c[0])
display["color_g"] = display["color_rgb"].apply(lambda c: c[1])
display["color_b"] = display["color_rgb"].apply(lambda c: c[2])
display["phci_label"] = display["phci"].round(3).astype(str)
display["coords"] = display.apply(
    lambda r: coords_for(r["corridor_id"], r["origin_lng"], r["origin_lat"],
                         r["dest_lng"], r["dest_lat"]),
    axis=1,
)
display["n_path_points"] = display["coords"].apply(len)

# ---------------------------------------------------------------------------
# pydeck layers
# ---------------------------------------------------------------------------
path_layer = pdk.Layer(
    "PathLayer",
    data=display,
    get_path="coords",
    get_color=["color_r", "color_g", "color_b", 220],
    get_width=5,
    width_min_pixels=3,
    width_max_pixels=10,
    pickable=True,
    auto_highlight=True,
    cap_rounded=True,
    joint_rounded=True,
)

origin_layer = pdk.Layer(
    "ScatterplotLayer",
    data=display,
    get_position=["origin_lng", "origin_lat"],
    get_fill_color=[31, 41, 55, 200],
    get_radius=70,
    pickable=False,
)
dest_layer = pdk.Layer(
    "ScatterplotLayer",
    data=display,
    get_position=["dest_lng", "dest_lat"],
    get_fill_color=[31, 41, 55, 200],
    get_radius=70,
    pickable=False,
)

view_state = pdk.ViewState(
    longitude=85.13,
    latitude=25.605,
    zoom=11.6,
    pitch=0,
    bearing=0,
)

tooltip = {
    "html": "<b>{corridor_id}. {corridor_name}</b><br/>"
            "PHCI: {phci_label}<br/>"
            "Worst hour: {phci_hour}:00<br/>"
            "Est. distance: {est_distance_km} km",
    "style": {"backgroundColor": "white", "color": "black",
              "fontSize": "12px", "padding": "8px",
              "border": "1px solid #d1d5db"},
}

deck = pdk.Deck(
    layers=[path_layer, origin_layer, dest_layer],
    initial_view_state=view_state,
    map_style="light",
    tooltip=tooltip,
)

st.pydeck_chart(deck, use_container_width=True)

# Legend
st.markdown(
    "**Colour scale — Peak-Hour Congestion Index (PHCI):** "
    "<span style='background:#3b82f6;color:white;padding:2px 6px'>&lt; 1.0</span> "
    "<span style='background:#fcd34d;color:black;padding:2px 6px'>1.0–1.25</span> "
    "<span style='background:#f97316;color:white;padding:2px 6px'>1.25–1.5</span> "
    "<span style='background:#dc2626;color:white;padding:2px 6px'>1.5–2.0</span> "
    "<span style='background:#7f1d1d;color:white;padding:2px 6px'>≥ 2.0</span>  &nbsp;"
    "<span style='background:#9ca3af;color:white;padding:2px 6px'>no data</span>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Methodology note — what the lines actually represent
# ---------------------------------------------------------------------------
with st.expander("ℹ️ What the lines on this map actually represent"):
    st.markdown(
        """
        Each corridor is drawn as a path following the **actual road geometry**
        between its two endpoints, sourced from the **OpenStreetMap Routing
        Machine (OSRM)**. The geometry is fetched once via
        `tools/fetch_corridor_polylines.py` and cached in
        `corridor_polylines.json` (committed to the repo for reproducibility).

        **Important nuance for audit-defensibility:** the OSRM path is for
        **display only**. The Congestion Ratio numbers themselves come from
        Google's live route choice for each 30-minute measurement, which can
        differ slightly between calls (see the *Distance Drift* table on the
        Methodology & Data Quality page). All metrics on this dashboard are
        **ratios** of Google's live-traffic time to Google's free-flow time
        on the *same call*, so they are route-invariant — Google can re-route
        without affecting the ratio's validity.

        In short: the map shows the canonical road being measured; the numbers
        on the dashboard reflect the actual traffic on whatever path Google
        chose at each measurement instant.
        """
    )

st.subheader("Corridor summary")
table = display[[
    "corridor_id", "corridor_name", "est_distance_km",
    "phci", "phci_hour", "adci", "bti", "n_path_points",
]].copy()
table = table.sort_values("phci", ascending=False).reset_index(drop=True)
table.insert(0, "rank", table.index + 1)
table["phci"] = table["phci"].round(3)
table["adci"] = table["adci"].round(3)
table["bti"] = table["bti"].round(3)
table = table.rename(columns={"n_path_points": "Road-path vertices"})
st.dataframe(table, use_container_width=True, hide_index=True)

st.caption(
    "Map tiles: CARTO Light (pydeck default). "
    "Road geometry: OpenStreetMap Routing Machine (OSRM) public demo server, "
    "fetched once on dashboard build. "
    "Origin/destination endpoints: `corridors.csv` (28 corridors × 2 directions). "
    "Press-quality PNG export available on the Downloads page."
)
