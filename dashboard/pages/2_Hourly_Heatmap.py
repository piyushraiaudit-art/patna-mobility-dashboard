"""Page 2 — Hourly Heatmap.

Maps to brief output #2: the corridor × hour heatmap that reveals peak
windows and their spreading. The weekday panel renders today; the weekend
panel is gated until weekend data arrives (first Sat: 2026-05-16).
"""

from __future__ import annotations

import streamlit as st

from dashboard.data import load_observations
from dashboard.metrics import (
    GATING, gating_state, hourly_median_cr, ranking_table, weekend_observations,
)
from dashboard.viz import hourly_heatmap

st.set_page_config(page_title="Hourly Heatmap", page_icon="🌡️", layout="wide")


@st.cache_data(ttl=600)
def _load():
    return load_observations()


df = _load()

st.title("Hourly Congestion Heatmap")
st.caption(
    "Brief output #2 — corridor × hour grid of median Congestion Ratio. "
    "White = free-flow, orange/red = chronic congestion. Dashed lines mark "
    "the policy-defined peak windows (08–11 AM, 17–20 PM IST)."
)

if df.empty:
    st.warning("No observations yet.")
    st.stop()

ranking = ranking_table(df)
corridor_order = ranking["corridor_id"].tolist() if not ranking.empty else []
hm = hourly_median_cr(df)

# ---------------------------------------------------------------------------
# Weekday panel
# ---------------------------------------------------------------------------
st.subheader("Weekday")

wk_panel = hm[hm["weekday_or_weekend"] == "Weekday"]
if wk_panel.empty:
    st.error("No weekday observations yet.")
else:
    min_n = int(wk_panel["n"].min())
    threshold = GATING["heatmap_cell_weekday"]
    state = gating_state(min_n, "heatmap_cell_weekday")
    if state == "Preliminary":
        st.info(
            f"**Preliminary** — sparsest cell has n={min_n}. Cells with n < 3 "
            "are rendered without an annotated value; their `n` is shown instead. "
            f"Cells stabilise at n ≥ {threshold.stable_n}."
        )
    elif state == "Stable":
        st.success(f"**Stable** — all cells have n ≥ {threshold.stable_n}.")
    n_days_weekday = df[df["weekday_or_weekend"] == "Weekday"]["date"].nunique()
    fig = hourly_heatmap(
        hm, corridor_order,
        title="Median Congestion Ratio — Weekday",
        subtitle=f"{n_days_weekday} weekday(s) of data. Source: Google Routes API v2, 30-min polling.",
        weekday_or_weekend="Weekday",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Weekend panel (gated until first weekend day)
# ---------------------------------------------------------------------------
st.subheader("Weekend / Holiday")

wkend_days = weekend_observations(df)["date"].nunique()
threshold_w = GATING["heatmap_weekend"]

if wkend_days < threshold_w.min_n:
    st.warning(
        f"🔒 **Locked** — weekend heatmap unlocks once the first weekend day of "
        "observations is collected. First Saturday in the audit window: **2026-05-16**."
    )
elif wkend_days < threshold_w.stable_n:
    st.info(
        f"**Preliminary** — {wkend_days} weekend day(s) of data so far. Stabilises "
        f"at {threshold_w.stable_n} weekend days."
    )
    fig = hourly_heatmap(
        hm, corridor_order,
        title="Median Congestion Ratio — Weekend (preliminary)",
        subtitle=f"{wkend_days} weekend day(s) of data.",
        weekday_or_weekend="Weekend",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    fig = hourly_heatmap(
        hm, corridor_order,
        title="Median Congestion Ratio — Weekend",
        subtitle=f"{wkend_days} weekend days of data.",
        weekday_or_weekend="Weekend",
    )
    st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Methodology and full per-cell counts on the **Methodology & Data Quality** page. "
    "Y-axis is sorted by Peak-Hour Congestion Index (worst at top)."
)
