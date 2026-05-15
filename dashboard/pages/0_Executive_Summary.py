"""Executive Summary — the new landing page.

A one-screen story for busy CAG seniors and govt officials: top 3 findings
in plain English, headline KPIs, a mini-map of the worst corridors, and
jump-links into the detail pages.
"""

from __future__ import annotations

import pydeck as pdk
import streamlit as st

from data import load_observations, data_quality_report, AUDIT_WINDOW_END, AUDIT_WINDOW_START
from metrics import (
    bti as compute_bti,
    direction_asymmetry,
    minutes_lost_table,
    ranking_table,
)
from viz import (
    build_corridor_geometry,
    compact_ranking_bar,
    mini_map,
    network_hourly_line,
)
from insights import top_findings_html
from ui import (
    KPI, apply_page_chrome, audit_context_caption, callout, kpi_row, page_header,
)
try:
    from ui import top_rank_list
except ImportError:
    # Defensive: if the deployed ui.py is from a partial cache, fall back to a
    # plain dataframe so the page still renders the rank info.
    def top_rank_list(ranking, top_n=5, title="Top corridors", footer=""):
        st.markdown(f"**{title}**")
        if ranking is not None and len(ranking) > 0:
            st.dataframe(
                ranking.head(top_n)[["rank", "corridor_name", "phci"]],
                use_container_width=True, hide_index=True,
            )
        if footer:
            st.caption(footer)


st.set_page_config(
    page_title="Executive Summary — Patna Mobility Audit",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=600, show_spinner="Loading observations…")
def _load():
    return load_observations()


@st.cache_data(ttl=600)
def _quality(_n: int):
    return data_quality_report()


df = _load()
ranking = ranking_table(df)
quality = _quality(len(df))
stats = quality["stats"]

apply_page_chrome(df, ranking, stats)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
page_header(
    title="Patna Mobility Congestion Index",
    subtitle=(
        f"Live evidence base for the CAG Urban Mobility Audit · "
        f"{AUDIT_WINDOW_START.date()} → {AUDIT_WINDOW_END.date()} · "
        "28 critical corridors · 30-minute polling via Google Routes API v2."
    ),
    eyebrow="Executive Summary",
)

if df.empty:
    st.warning("No observations yet. The dashboard will populate as the cron collector runs.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI strip — six cards
# ---------------------------------------------------------------------------
ml = minutes_lost_table(df)
bti_df = compute_bti(df)

worst = ranking.iloc[0] if not ranking.empty else None
longest_delay = ml.iloc[0] if not ml.empty else None
most_unreliable = (
    bti_df.dropna(subset=["bti"]).iloc[0]
    if (not bti_df.empty and bti_df["bti"].notna().any()) else None
)

kpi_row([
    KPI(
        label="Worst corridor",
        value=str(worst["corridor_name"])[:24] if worst is not None else "—",
        sublabel=(f"PHCI {float(worst['phci']):.2f} · "
                  f"{int(worst['phci_hour']):02d}:00 IST" if worst is not None else "Locked"),
        accent="rose",
    ),
    KPI(
        label="Longest peak delay",
        value=(f"{float(longest_delay['minutes_lost']):.1f} min/trip"
               if longest_delay is not None else "—"),
        sublabel=(str(longest_delay["corridor_name"])[:30]
                  if longest_delay is not None else "Awaiting data"),
        accent="amber",
    ),
    KPI(
        label="Most unreliable",
        value=(f"BTI {float(most_unreliable['bti']):.2f}"
               if most_unreliable is not None else "—"),
        sublabel=(str(most_unreliable["corridor_name"])[:30]
                  if most_unreliable is not None else "Locked"),
        accent="violet",
    ),
    KPI(
        label="Days observed",
        value=f"{stats.days_covered} / 8",
        sublabel="of the 8-day audit window",
        accent="indigo",
    ),
    KPI(
        label="Corridor coverage",
        value=f"{stats.corridors_covered} / 28",
        sublabel="critical corridors active",
        accent="emerald",
    ),
    KPI(
        label="Observations",
        value=f"{stats.total_observations:,}",
        sublabel=f"FAIL rate {stats.fail_pct:.2f}%",
        accent="cyan",
    ),
])

# ---------------------------------------------------------------------------
# Top 3 findings
# ---------------------------------------------------------------------------
asym = direction_asymmetry(df)
findings_html = top_findings_html(df, ranking, asym, bti_df, ml)
callout(findings_html, kind="insight",
        title="Top 3 findings — what the data says today")

# ---------------------------------------------------------------------------
# Mini-map of top 5 worst corridors — paired with a colour-matched rank list
# ---------------------------------------------------------------------------
st.markdown("### Where the worst congestion is happening")
st.caption(
    "On the map, the boldest, most-saturated lines are the worst — line thickness "
    "decreases from rank 1 to 5. The 23 remaining corridors are faded for "
    "geographic context. Hover any line for the corridor name and PHCI."
)
geom = build_corridor_geometry(df, ranking)
map_col, list_col = st.columns([2, 1], gap="medium")
with map_col:
    st.pydeck_chart(mini_map(geom, top_n=5), use_container_width=True, height=420)
with list_col:
    top_rank_list(
        ranking, top_n=5, title="Top 5 worst corridors",
        footer="Badge colour matches the line colour on the map. "
               "Hover any line for full statistics.",
    )

# ---------------------------------------------------------------------------
# Two compact charts
# ---------------------------------------------------------------------------
col_a, col_b = st.columns([1, 1], gap="large")
with col_a:
    st.markdown("#### Top corridors by PHCI")
    st.plotly_chart(compact_ranking_bar(ranking, top_n=6), use_container_width=True)
with col_b:
    st.markdown("#### When is congestion worst?")
    st.plotly_chart(network_hourly_line(df), use_container_width=True)

# ---------------------------------------------------------------------------
# Jump-to navigation
# ---------------------------------------------------------------------------
st.markdown("### Drill into the detail")
nav_cols = st.columns(3)
links = [
    ("pages/1_Congestion_Index_Ranking.py", "Full ranking", "📊"),
    ("pages/2_Hourly_Heatmap.py", "Hourly heatmap", "🌡️"),
    ("pages/3_Direction_Asymmetry.py", "Direction asymmetry", "↔️"),
    ("pages/4_Reliability_Index.py", "Reliability index", "⏱️"),
    ("pages/5_Corridor_Map.py", "Full interactive map", "🗺️"),
    ("pages/6_Methodology_and_Data_Quality.py", "Methodology & data quality", "📐"),
]
for i, (path, label, icon) in enumerate(links):
    with nav_cols[i % 3]:
        try:
            st.page_link(path, label=label, icon=icon)
        except KeyError:
            st.markdown(f"{icon} **{label}** &nbsp;`{path.split('/')[-1]}`",
                        unsafe_allow_html=True)

st.markdown("&nbsp;", unsafe_allow_html=True)
audit_context_caption(
    f"Last updated: {stats.last_timestamp} IST · "
    f"Reproducibility MD5: {stats.observations_md5[:12]}…"
)
