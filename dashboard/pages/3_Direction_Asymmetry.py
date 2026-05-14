"""Page 3 — Direction Asymmetry.

Maps to brief output #3: inbound vs outbound congestion at AM and PM
peak windows. Useful for one-way regulation or signal-timing recommendations.
"""

from __future__ import annotations

import streamlit as st

from data import load_observations
from metrics import (
    GATING, gating_state, direction_asymmetry, am_peak_observations,
    pm_peak_observations, weekday_observations,
)
from viz import direction_asymmetry_chart

st.set_page_config(page_title="Direction Asymmetry", page_icon="↔️", layout="wide")


@st.cache_data(ttl=600)
def _load():
    return load_observations()


df = _load()

st.title("Direction Asymmetry")
st.caption(
    "Brief output #3 — for each corridor, inbound (A→B) vs outbound (B→A) median "
    "congestion ratio. Large gaps suggest one-way regulation, signal retiming, "
    "or directional parking enforcement as candidate interventions."
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

col1, col2 = st.columns(2)
col1.metric("AM-peak min n/direction", am_min, help=f"Stable at n ≥ {threshold.stable_n}")
col2.metric("PM-peak min n/direction", pm_min, help=f"Stable at n ≥ {threshold.stable_n}")

asym = direction_asymmetry(df)

if state_am != "Locked":
    if state_am == "Preliminary":
        st.info(f"AM-peak **Preliminary** (n={am_min}).")
    st.plotly_chart(direction_asymmetry_chart(asym, "AM Peak"), use_container_width=True)
else:
    st.warning("🔒 AM-peak asymmetry locked — awaiting more morning observations.")

st.divider()

if state_pm != "Locked":
    if state_pm == "Preliminary":
        st.info(f"PM-peak **Preliminary** (n={pm_min}).")
    st.plotly_chart(direction_asymmetry_chart(asym, "PM Peak"), use_container_width=True)
else:
    st.warning("🔒 PM-peak asymmetry locked — awaiting more evening observations.")

st.divider()

st.subheader("Asymmetry table")
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
