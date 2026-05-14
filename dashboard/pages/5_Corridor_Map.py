"""Page 5 — Corridor Map.

Maps to brief output #5: an interactive map of Patna with all 28 corridors
colour-coded by Peak-Hour Congestion Index. Designed for state govt and
press sharing. The static PNG of this view is part of the downloads bundle.
"""

from __future__ import annotations

import pandas as pd
import pydeck as pdk
import streamlit as st

from data import load_observations
from metrics import ranking_table

st.set_page_config(page_title="Corridor Map", page_icon="🗺️", layout="wide")


@st.cache_data(ttl=600)
def _load():
    return load_observations()


df = _load()

st.title("Patna — Corridor Congestion Map")
st.caption(
    "Brief output #5 — all 28 corridors of Patna, colour-coded by Peak-Hour "
    "Congestion Index. Hover any corridor for its full statistics. Suitable "
    "for sharing with the State Government and the press."
)

if df.empty:
    st.warning("No observations yet.")
    st.stop()

ranking = ranking_table(df)

# Build per-corridor geometry (use any one direction's coords; both directions
# share the same endpoints in corridors.csv).
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


display["color_rgb"] = display["phci"].apply(phci_to_rgb)
display["color_r"] = display["color_rgb"].apply(lambda c: c[0])
display["color_g"] = display["color_rgb"].apply(lambda c: c[1])
display["color_b"] = display["color_rgb"].apply(lambda c: c[2])
display["phci_label"] = display["phci"].round(3).astype(str)

line_layer = pdk.Layer(
    "LineLayer",
    data=display,
    get_source_position=["origin_lng", "origin_lat"],
    get_target_position=["dest_lng", "dest_lat"],
    get_color=["color_r", "color_g", "color_b", 220],
    get_width=6,
    pickable=True,
    auto_highlight=True,
)

origin_layer = pdk.Layer(
    "ScatterplotLayer",
    data=display,
    get_position=["origin_lng", "origin_lat"],
    get_fill_color=[31, 41, 55, 200],
    get_radius=80,
    pickable=False,
)
dest_layer = pdk.Layer(
    "ScatterplotLayer",
    data=display,
    get_position=["dest_lng", "dest_lat"],
    get_fill_color=[31, 41, 55, 200],
    get_radius=80,
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
    layers=[line_layer, origin_layer, dest_layer],
    initial_view_state=view_state,
    map_style="light",
    tooltip=tooltip,
)

st.pydeck_chart(deck, use_container_width=True)

# Legend
st.markdown(
    "**Colour scale (PHCI):** "
    "<span style='background:#3b82f6;color:white;padding:2px 6px'>&lt; 1.0</span> "
    "<span style='background:#fcd34d;color:black;padding:2px 6px'>1.0–1.25</span> "
    "<span style='background:#f97316;color:white;padding:2px 6px'>1.25–1.5</span> "
    "<span style='background:#dc2626;color:white;padding:2px 6px'>1.5–2.0</span> "
    "<span style='background:#7f1d1d;color:white;padding:2px 6px'>≥ 2.0</span>  &nbsp;"
    "<span style='background:#9ca3af;color:white;padding:2px 6px'>no data</span>",
    unsafe_allow_html=True,
)

st.subheader("Corridor summary")
table = display[[
    "corridor_id", "corridor_name", "est_distance_km",
    "phci", "phci_hour", "adci", "bti",
]].copy()
table = table.sort_values("phci", ascending=False).reset_index(drop=True)
table.insert(0, "rank", table.index + 1)
table["phci"] = table["phci"].round(3)
table["adci"] = table["adci"].round(3)
table["bti"] = table["bti"].round(3)
st.dataframe(table, use_container_width=True, hide_index=True)

st.caption(
    "Map tiles from CARTO via Mapbox Light style (pydeck default). "
    "Origin/destination endpoints from `corridors.csv` (28 corridors × 2 directions). "
    "PNG export of this view is available on the **Downloads** page."
)
