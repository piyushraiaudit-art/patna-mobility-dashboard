"""
Patna Mobility Congestion Index — Dashboard entry point.

Run locally:
    streamlit run dashboard/app.py

Public hosted version (auto-rebuilt on every git push to the data repo):
    https://patna-mobility-dashboard.streamlit.app  (URL added in Hour 7)
"""

from __future__ import annotations

import streamlit as st

from dashboard.data import load_observations, data_quality_report, AUDIT_WINDOW_START, AUDIT_WINDOW_END
from dashboard.metrics import (
    GATING, gating_state, ranking_table, weekday_observations, weekend_observations,
    peak_observations,
)

st.set_page_config(
    page_title="Patna Mobility Congestion Index",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Cached data access
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600, show_spinner="Loading observations…")
def cached_load():
    return load_observations()


@st.cache_data(ttl=600, show_spinner="Computing data-quality report…")
def cached_quality(_df_md5: str):
    return data_quality_report()


# ---------------------------------------------------------------------------
# Overview page
# ---------------------------------------------------------------------------

def render_overview():
    st.title("Patna Mobility Congestion Index")
    st.caption(
        "An objective, time-resolved congestion measure for the Patna Urban Mobility "
        "Audit. Free-flow vs. live travel time, every 30 minutes, 28 corridors, "
        f"{AUDIT_WINDOW_START.date()} → {AUDIT_WINDOW_END.date()}."
    )

    df = cached_load()
    rep = cached_quality(_df_md5=df.shape[0])  # cheap cache key
    stats = rep["stats"]

    # Headline numbers ---------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Observations (OK)", f"{stats.total_observations:,}")
    col2.metric("Days covered", stats.days_covered)
    col3.metric("Corridors", f"{stats.corridors_covered}/28")
    col4.metric("FAIL rate", f"{stats.fail_pct:.2f}%")

    ranking = ranking_table(df)
    if not ranking.empty:
        worst = ranking.iloc[0]
        st.success(
            f"**Worst corridor today:** {worst.corridor_id}. {worst.corridor_name} "
            f"— Peak-Hour Congestion Index **{worst.phci:.2f}** "
            f"(at {int(worst.phci_hour):02d}:00, direction {worst.phci_direction})."
        )

    st.divider()

    # Three-sentence methodology pitch ----------------------------------
    st.markdown(
        """
        ### What this dashboard measures
        For each of 28 critical Patna corridors, the tool polls Google Routes API v2 every
        30 minutes for the live travel time **and** the free-flow travel time. The ratio of
        the two — the **Congestion Ratio** — is 1.0 when traffic is flowing freely and rises
        above 1.0 as congestion builds. Aggregated over the 8-day audit window, this produces
        a defensible, hour-by-hour, corridor-by-corridor evidence base for the Patna Urban
        Mobility Audit, replacing subjective "X road is congested" framings with hard numbers.
        """
    )

    # Feature gating status strip ---------------------------------------
    st.subheader("Feature readiness")
    st.caption(
        "Each metric unlocks automatically as more observations accumulate. "
        "Preliminary numbers are usable but should be quoted with their `n`. "
        "Stable means the metric has reached audit-defensible sample size."
    )

    feature_status = _build_gating_status(df, ranking)

    cols = st.columns(len(feature_status))
    for c, (label, state, detail) in zip(cols, feature_status):
        emoji = {"Locked": "🔒", "Preliminary": "🟡", "Stable": "🟢"}[state]
        c.markdown(f"**{label}**  \n{emoji} {state}  \n<span style='font-size:11px;color:#6b7280'>{detail}</span>",
                   unsafe_allow_html=True)

    st.divider()

    # Data freshness footer ---------------------------------------------
    st.caption(
        f"Data as of **{stats.last_timestamp} IST** · "
        f"Window: {AUDIT_WINDOW_START.date()} → {AUDIT_WINDOW_END.date()} · "
        f"MD5 (observations): `{stats.observations_md5[:12]}…` · "
        f"Source: Google Routes API v2, 30-minute polling. "
        f"See Methodology & Data Quality for the full reproducibility signature."
    )


def _build_gating_status(df, ranking):
    """Return list of (label, state, detail) tuples for the status strip."""
    out = []

    if ranking.empty:
        out.append(("Ranking", "Locked", "Awaiting first batches"))
    else:
        min_n_peak = int(ranking["n_peak"].min())
        state = gating_state(min_n_peak, "phci_weekday")
        out.append(("Weekday PHCI", state,
                    f"min n={min_n_peak} per corridor; need ≥ {GATING['phci_weekday'].stable_n} for Stable"))

    wkend = weekend_observations(df)
    wkend_days = wkend["date"].nunique() if not wkend.empty else 0
    if wkend_days == 0:
        out.append(("Weekend heatmap", "Locked",
                    "First Saturday: 2026-05-16"))
    elif wkend_days == 1:
        out.append(("Weekend heatmap", "Preliminary", "1 weekend day in; second on 17 May"))
    else:
        out.append(("Weekend heatmap", "Stable", f"{wkend_days} weekend days"))

    wk_peak = peak_observations(weekday_observations(df))
    if wk_peak.empty:
        out.append(("BTI / Reliability", "Locked", "Awaiting peak-window observations"))
    else:
        per_corridor = wk_peak.groupby("corridor_id").size()
        min_n = int(per_corridor.min())
        state = gating_state(min_n, "bti")
        out.append(("BTI / Reliability", state,
                    f"min n={min_n}; need ≥ {GATING['bti'].stable_n} for Stable"))

    if not wk_peak.empty:
        am = wk_peak[wk_peak["hour"].astype(int).isin([8, 9, 10])]
        n_am = int(am.groupby(["corridor_id", "direction"]).size().min()) if not am.empty else 0
        state = gating_state(n_am, "direction_asymmetry")
        out.append(("Direction asymmetry", state,
                    f"min n={n_am} per direction in AM peak"))
    else:
        out.append(("Direction asymmetry", "Locked", "Awaiting peak-window data"))

    return out


render_overview()
