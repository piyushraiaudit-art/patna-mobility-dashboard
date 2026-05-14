"""Page 4 — Reliability Index.

Maps to brief output #4: how unpredictable a commute is. Buffer Time Index
(FHWA standard) is the headline; Coefficient of Variation is the cross-check.
Showing both protects against "you cherry-picked the metric" objections.
"""

from __future__ import annotations

import streamlit as st

from dashboard.data import load_observations
from dashboard.metrics import (
    GATING, gating_state, bti as compute_bti, cv as compute_cv, peak_observations,
    weekday_observations,
)
from dashboard.viz import reliability_chart

st.set_page_config(page_title="Reliability Index", page_icon="⏱️", layout="wide")


@st.cache_data(ttl=600)
def _load():
    return load_observations()


df = _load()

st.title("Reliability Index")
st.caption(
    "Brief output #4 — \"how much extra time must a commuter budget to arrive "
    "on time?\". Two metrics shown side-by-side: the **Buffer Time Index** "
    "(FHWA standard, US-DOT Mobility Monitoring Program) and the **Coefficient "
    "of Variation** as a cross-check."
)

if df.empty:
    st.warning("No observations yet.")
    st.stop()

wk_peak = peak_observations(weekday_observations(df))
min_n = int(wk_peak.groupby("corridor_id").size().min()) if not wk_peak.empty else 0

threshold_b = GATING["bti"]
threshold_c = GATING["cv"]
state_b = gating_state(min_n, "bti")
state_c = gating_state(min_n, "cv")

col1, col2 = st.columns(2)
col1.metric("Min peak-window n per corridor", min_n)
col2.metric("BTI / CV stable thresholds",
            f"{threshold_b.stable_n} / {threshold_c.stable_n}")

if state_b == "Locked":
    st.error("🔒 BTI locked — awaiting more peak-window observations.")
    st.stop()
elif state_b == "Preliminary":
    st.warning(
        f"**Preliminary** — peak-window samples per corridor are still small "
        f"(min n={min_n}). p95 is sensitive to small samples; treat BTI values "
        f"as directional until n ≥ {threshold_b.stable_n}."
    )

# ---------------------------------------------------------------------------
# BTI
# ---------------------------------------------------------------------------
st.subheader("Buffer Time Index (BTI) — FHWA standard")
st.markdown(
    "**BTI = (p95 peak duration − median peak duration) / median peak duration.**  "
    "Interpretation: a BTI of 0.30 means a commuter must budget 30% extra time "
    "to arrive on time 95 days out of 100. Cited from the US Federal Highway "
    "Administration's Mobility Monitoring Program."
)
bti_df = compute_bti(df)
st.plotly_chart(reliability_chart(bti_df, metric="bti"), use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# CV
# ---------------------------------------------------------------------------
st.subheader("Coefficient of Variation (CV) — cross-check")
st.markdown(
    "**CV = σ(peak duration) / μ(peak duration).** A simpler, distribution-shape-"
    "agnostic measure of trip-time variability. We report it alongside BTI so two "
    "different statistical lenses converge on the same conclusion about a corridor's "
    "predictability."
)
cv_df = compute_cv(df)
st.plotly_chart(reliability_chart(cv_df, metric="cv"), use_container_width=True)

st.divider()
st.subheader("Reliability table")
table = bti_df.merge(
    cv_df[["corridor_id", "direction", "cv", "mu_peak_s", "sigma_peak_s"]],
    on=["corridor_id", "direction"], how="left",
)
table["bti"] = table["bti"].round(3)
table["cv"] = table["cv"].round(3)
table["median_peak_min"] = (table["median_peak_s"] / 60.0).round(2)
table["p95_peak_min"] = (table["p95_peak_s"] / 60.0).round(2)
display = table[[
    "corridor_id", "corridor_name", "direction",
    "median_peak_min", "p95_peak_min", "bti", "cv", "n",
]]
st.dataframe(display, use_container_width=True, hide_index=True)
