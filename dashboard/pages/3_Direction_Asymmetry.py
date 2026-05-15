"""Page 3 — Direction Asymmetry.

Brief output #3: inbound vs outbound congestion at AM and PM peak windows.
Useful for one-way regulation or signal-timing recommendations.
"""

from __future__ import annotations

import streamlit as st

from data import data_quality_report, load_observations
from insights import asymmetry_implication
from metrics import (
    GATING, am_peak_observations, direction_asymmetry, gating_state,
    pm_peak_observations, ranking_table, weekday_observations,
)
from ui import apply_page_chrome, audit_context_caption, callout, page_header
from viz import direction_asymmetry_chart

st.set_page_config(page_title="Direction Asymmetry", page_icon="↔️", layout="wide")


@st.cache_data(ttl=600)
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

page_header(
    title="Direction Asymmetry",
    subtitle=("Brief output #3 — for each corridor, inbound (A→B) vs outbound (B→A) "
              "median congestion ratio at AM and PM peaks."),
    eyebrow="Page 3",
)

if df.empty:
    st.warning("No observations yet.")
    st.stop()

wk = weekday_observations(df)
am_obs = am_peak_observations(wk)
pm_obs = pm_peak_observations(wk)

threshold = GATING["direction_asymmetry"]
am_min = int(am_obs.groupby(["corridor_id", "direction"]).size().min()) if not am_obs.empty else 0
pm_min = int(pm_obs.groupby(["corridor_id", "direction"]).size().min()) if not pm_obs.empty else 0

state_am = gating_state(am_min, "direction_asymmetry")
state_pm = gating_state(pm_min, "direction_asymmetry")

asym = direction_asymmetry(df)

callout(asymmetry_implication(asym), kind="insight",
        title="What direction asymmetry says about intervention")

# ---------------------------------------------------------------------------
# AM peak
# ---------------------------------------------------------------------------
st.subheader("AM peak (08:00–11:00 IST)")
if state_am != "Locked":
    st.plotly_chart(direction_asymmetry_chart(asym, "AM Peak"), use_container_width=True)
else:
    st.info("AM-peak asymmetry unlocks once each direction has more morning observations.")

st.divider()

# ---------------------------------------------------------------------------
# PM peak
# ---------------------------------------------------------------------------
st.subheader("PM peak (17:00–20:00 IST)")
if state_pm != "Locked":
    st.plotly_chart(direction_asymmetry_chart(asym, "PM Peak"), use_container_width=True)
else:
    st.info("PM-peak asymmetry unlocks once each direction has more evening observations.")

st.divider()

# ---------------------------------------------------------------------------
# Full table — collapsed
# ---------------------------------------------------------------------------
with st.expander("Full asymmetry table"):
    display = asym.copy()
    for col in ("median_cr_A_to_B", "median_cr_B_to_A"):
        if col in display.columns:
            display[col] = display[col].round(3)
    display = display[[
        "peak", "corridor_id", "corridor_name",
        "median_cr_A_to_B", "median_cr_B_to_A", "asymmetry_pct",
        "n_A_to_B", "n_B_to_A",
    ]]
    st.dataframe(display, use_container_width=True, hide_index=True)

audit_context_caption()
