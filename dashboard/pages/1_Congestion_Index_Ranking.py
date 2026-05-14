"""Page 1 — Congestion Index Ranking.

Maps to brief output #1: a worst→best ranked list of 28 corridors with
peak-hour ratios, plus the secondary "absolute minutes lost" ranking
that contextualises short-corridor ratios.
"""

from __future__ import annotations

import streamlit as st

from dashboard.data import load_observations
from dashboard.metrics import (
    GATING, gating_state, ranking_table, minutes_lost_table, SHORT_CORRIDOR_IDS,
)
from dashboard.viz import ranking_bar

st.set_page_config(page_title="Congestion Index Ranking", page_icon="📊", layout="wide")


@st.cache_data(ttl=600)
def _load():
    return load_observations()


df = _load()
ranking = ranking_table(df)

st.title("Congestion Index Ranking")
st.caption("Brief output #1 — 28 corridors of Patna, worst congested to least.")

if ranking.empty:
    st.warning("No observations yet. The dashboard will populate as the cron collector runs.")
    st.stop()

min_n = int(ranking["n_peak"].min())
state = gating_state(min_n, "phci_weekday")
threshold = GATING["phci_weekday"]
if state == "Preliminary":
    st.warning(
        f"**Preliminary — n={min_n}** weekday peak-hour observations per corridor. "
        f"Numbers stabilise at n ≥ {threshold.stable_n}. Quote results with the n attached."
    )
elif state == "Locked":
    st.error(
        f"**Locked** — need at least n={threshold.min_n} weekday peak observations per "
        f"corridor; current min is {min_n}. Awaiting more cron batches."
    )
else:
    st.success(f"**Stable** — min n={min_n} per corridor (threshold: {threshold.stable_n}).")

# ---------------------------------------------------------------------------
# Primary chart: PHCI ranking
# ---------------------------------------------------------------------------
st.subheader("Peak-Hour Congestion Index (PHCI)")
st.markdown(
    "For each corridor, the maximum of the **weekday peak-hour median** congestion "
    "ratios across both directions, taken over peak hours 08–10 and 17–19 IST. "
    "A value of 1.50 means the worst peak-hour median trip took 50% longer than free-flow."
)
st.plotly_chart(ranking_bar(ranking), use_container_width=True)

# ---------------------------------------------------------------------------
# Ranking table — sortable, with all metrics
# ---------------------------------------------------------------------------
st.subheader("Full ranking table")

display = ranking[[
    "rank", "corridor_id", "corridor_name", "phci", "phci_hour", "phci_direction",
    "adci", "bti", "cv", "n_peak", "is_short_corridor",
]].copy()
display["phci"] = display["phci"].round(3)
display["adci"] = display["adci"].round(3)
display["bti"] = display["bti"].round(3)
display["cv"] = display["cv"].round(3)
display = display.rename(columns={
    "phci": "PHCI", "phci_hour": "Worst hour", "phci_direction": "Worst dir",
    "adci": "ADCI (06-21)", "bti": "BTI (peak)", "cv": "CV (peak)",
    "n_peak": "n peak obs", "is_short_corridor": "Short corridor *",
})
st.dataframe(display, use_container_width=True, hide_index=True)

if any(ranking["is_short_corridor"]):
    short = ", ".join(sorted(SHORT_CORRIDOR_IDS))
    st.caption(
        f"\\* Short corridors ({short}) are < 1.5 km. Congestion ratio there is "
        "sensitive to one signal cycle and should be read alongside the absolute "
        "minutes-lost table below."
    )

# ---------------------------------------------------------------------------
# Secondary ranking by absolute minutes lost
# ---------------------------------------------------------------------------
st.subheader("Cross-check — peak minutes lost per trip")
st.caption(
    "Same data, different lens: how many real minutes a peak-hour driver loses "
    "vs. free-flow on each corridor. Long corridors can have a modest ratio but "
    "lose many absolute minutes; short corridors can show a dramatic ratio but "
    "only seconds of real delay."
)
ml = minutes_lost_table(df).copy()
ml.insert(0, "rank", ml.index + 1)
st.dataframe(ml, use_container_width=True, hide_index=True)
