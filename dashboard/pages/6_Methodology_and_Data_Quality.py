"""Page 6 — Methodology & Data Quality.

This is the audit-defensibility page for CAG senior review. Six sections:
  1. Formulas (rendered as LaTeX)
  2. Coverage matrix (corridor × date)
  3. FAIL log (with the 56 bootstrap fails surfaced transparently)
  4. Distance drift table (defends against "did Google measure the same path?")
  5. Reproducibility signature (MD5 hashes + pinned versions)
  6. Triangulation hooks (Citizen Survey, JPV, peer-city placeholders)

Non-negotiable for the 101-city Mobility Audit Best-Practice framing.
"""

from __future__ import annotations

import platform
import sys

import pandas as pd
import plotly
import streamlit as st

from data import (
    AUDIT_WINDOW_END, AUDIT_WINDOW_START, data_quality_report, load_observations,
)
from metrics import (
    AM_PEAK_HOURS, PM_PEAK_HOURS, ACTIVE_HOURS, SHORT_CORRIDOR_IDS,
)
from viz import coverage_heatmap, cr_cdf_chart

st.set_page_config(page_title="Methodology & Data Quality", page_icon="📐", layout="wide")


@st.cache_data(ttl=600)
def _load():
    return load_observations()


df = _load()
rep = data_quality_report(df)
stats = rep["stats"]

st.title("Methodology & Data Quality")
st.caption(
    "The audit-defensibility page. Formulas, coverage, failure log, distance drift, "
    "and a reproducibility signature so two reviewers on two laptops can confirm "
    "they are looking at identical numbers."
)

# ---------------------------------------------------------------------------
# 1. Formulas
# ---------------------------------------------------------------------------
st.header("1. Formulas")

st.markdown("**Instant Congestion Ratio** — already stored in the CSV as `congestion_ratio`:")
st.latex(r"\text{CR}_{i,t} = \frac{\text{duration\_traffic\_s}_{i,t}}{\text{duration\_freeflow\_s}_{i,t}}")
st.caption(
    "Excluded if `api_status != \"OK\"`, `duration_freeflow_s ≤ 0`, or either field is null. "
    "`duration_traffic_s` is Google's live travel time given current traffic; "
    "`duration_freeflow_s` is Google's `staticDuration` — the model's estimate of "
    "the same route with no congestion."
)

st.markdown("**Hourly Median Congestion Ratio** (median, not mean — defends against single-batch spikes):")
st.latex(r"\text{CR}^{h}_{i,d} = \mathrm{median}_{t \in \text{hour } h}\bigl(\text{CR}_{i,t}\bigr)")

st.markdown("**Peak-Hour Congestion Index (PHCI)** — the headline ranking metric:")
st.latex(
    r"\text{PHCI}_i = \max\bigl(\mathrm{median}(\text{CR}_{i,d,h}) : "
    r"h \in \{8,9,10,17,18,19\},\ d \in \text{weekdays}\bigr)"
)
st.caption("Both directions of a corridor are aggregated by taking the max — represents \"worst direction at worst peak hour\".")

st.markdown("**All-Day Congestion Index (ADCI)** — mean of hourly medians over active hours 06-21:")
st.latex(r"\text{ADCI}_i = \mathrm{mean}_{h \in [6, 22]}\bigl(\text{CR}^{h}_{i}\bigr)")

st.markdown("**Buffer Time Index (BTI)** — FHWA Mobility Monitoring Program standard:")
st.latex(
    r"\text{BTI}_i = \frac{p_{95}(\text{duration\_traffic}_{i,\text{peak}}) - "
    r"\mathrm{median}(\text{duration\_traffic}_{i,\text{peak}})}"
    r"{\mathrm{median}(\text{duration\_traffic}_{i,\text{peak}})}"
)
st.caption("Interpretation: BTI=0.30 means \"budget 30% extra time to arrive on time 95 days out of 100\".")

st.markdown("**Coefficient of Variation (CV)** — cross-check on BTI:")
st.latex(
    r"\text{CV}_i = \frac{\sigma(\text{duration\_traffic}_{i,\text{peak}})}"
    r"{\mu(\text{duration\_traffic}_{i,\text{peak}})}"
)

st.subheader("Peak window — hard-coded, not data-driven")
st.markdown(
    f"- **AM peak**: hours {sorted(AM_PEAK_HOURS)[0]:02d}:00–{sorted(AM_PEAK_HOURS)[-1]+1:02d}:00 IST.  \n"
    f"- **PM peak**: hours {sorted(PM_PEAK_HOURS)[0]:02d}:00–{sorted(PM_PEAK_HOURS)[-1]+1:02d}:00 IST.  \n"
    f"- **Active hours** (for ADCI): {ACTIVE_HOURS[0]:02d}:00–{ACTIVE_HOURS[-1]+1:02d}:00 IST.  \n\n"
    "Anchored to Bihar State Government office hours and the National Urban Transport "
    "Policy convention. **Not** detected from the data — with 2–8 days of observations, "
    "data-driven peak detection is unstable and invites the \"you fit the window to "
    "make the numbers look bad\" objection. The auditor can override the window from "
    "the sidebar of pages 1, 3, and 4."
)

st.subheader("Sample-size sufficiency thresholds")
st.markdown(
    "Each metric and chart self-gates by observation count: **Locked** (insufficient), "
    "**Preliminary** (usable with `n` quoted), **Stable** (audit-defensible). "
    "Thresholds live in `dashboard/metrics.py:GATING` and are visible on every page."
)

st.subheader("Empirical CR distribution — sanity check")
st.markdown(
    "Values below 1.0 are real and not a bug: in deep off-peak, Google's live "
    "`duration` can be faster than its `staticDuration` model estimate. We do not "
    f"clamp. Empirical range in the current dataset: **{rep['cr_distribution'].min():.3f}** "
    f"to **{rep['cr_distribution'].max():.3f}**, median **{rep['cr_distribution'].median():.3f}**."
)
st.plotly_chart(cr_cdf_chart(rep["cr_distribution"]), use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 2. Coverage matrix
# ---------------------------------------------------------------------------
st.header("2. Observation Coverage")
st.markdown(
    "Every cell counts the OK observations collected for a given corridor on a "
    "given date. Full coverage is **48 batches/day × 1 corridor = 48** (cron every "
    "30 minutes; one row per corridor per batch). Red < 30, amber 30–44, green ≥ 45."
)
st.plotly_chart(coverage_heatmap(rep["coverage"]), use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 3. FAIL log
# ---------------------------------------------------------------------------
st.header("3. Failed API calls — transparency log")
st.markdown(
    f"**{stats.fail_count}** failed Routes API calls in the cumulative log "
    f"({stats.fail_pct:.2f}% of total). All failures are surfaced here so reviewers "
    "can confirm no observation is silently hidden. The OK-only filter on every "
    "other page excludes these rows."
)

if stats.fail_count > 0:
    st.subheader("Failure summary")
    st.dataframe(rep["fail_summary"], use_container_width=True, hide_index=True)

    st.markdown(
        ":information_source: **Known cause for the 56 fails on 2026-05-12 20:47:** "
        "the first manual test run used `datetime.now()` as `departureTime`, which "
        "Google rejects when the time is in the past at the moment the request "
        "reaches the server. Fixed in `collect_travel_times.py` before the cron "
        "schedule started. No further failures from this cause are expected."
    )

    with st.expander("Raw FAIL rows"):
        fail_display = rep["fail_log"][[
            "timestamp_ist", "corridor_id", "corridor_name", "direction",
            "api_status", "error_msg",
        ]]
        st.dataframe(fail_display, use_container_width=True, hide_index=True)
else:
    st.success("No failed API calls in the cumulative log.")

st.divider()

# ---------------------------------------------------------------------------
# 4. Distance drift
# ---------------------------------------------------------------------------
st.header("4. Distance drift — did Google measure the same path each time?")
st.markdown(
    "**Yes, ratios are route-invariant.** For each call, Google returns both "
    "`duration_traffic_s` and `duration_freeflow_s` for the *same chosen route*. "
    "The Congestion Ratio is therefore dimensionless and does not depend on which "
    "alternative path was selected on a given run. We report distance drift here "
    "so reviewers see we have audited the question explicitly."
)
st.markdown(
    "The table below shows, for each (corridor, direction), how many distinct "
    "`distance_m` values Google returned and the max-vs-min spread. Cells flagged "
    "with **Re-route = True** are where the spread exceeds 25% of `est_distance_km` "
    "in `corridors.csv` — a hint that Google occasionally picked a meaningfully "
    "different path."
)

drift = rep["distance_drift"].copy()
drift["delta_pct_of_est"] = drift["delta_pct_of_est"].round(2)
st.dataframe(drift, use_container_width=True, hide_index=True)

if drift["reroute_flag"].any():
    n_flagged = int(drift["reroute_flag"].sum())
    st.caption(
        f"{n_flagged} (corridor, direction) pair(s) flagged for re-routing. "
        "The ratio-based metrics on every other page remain valid regardless."
    )

st.divider()

# ---------------------------------------------------------------------------
# 5. Reproducibility signature
# ---------------------------------------------------------------------------
st.header("5. Reproducibility signature")
st.markdown(
    "Two reviewers on two laptops, running the same code against the same input "
    "files, should see **identical** MD5 hashes below. If hashes match and the "
    "versions below match, every number on every page matches by construction."
)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Input hashes (MD5 of sorted CSV serialisation):**")
    st.code(
        f"observations:  {stats.observations_md5}\n"
        f"corridors.csv: {stats.corridors_md5}",
        language="text",
    )
    st.markdown("**Data window:**")
    st.code(
        f"first observation: {stats.first_timestamp} IST\n"
        f"last observation:  {stats.last_timestamp} IST\n"
        f"days covered:      {stats.days_covered}\n"
        f"corridors:         {stats.corridors_covered}/28",
        language="text",
    )
with col2:
    st.markdown("**Software versions:**")
    st.code(
        f"python:    {sys.version.split()[0]}\n"
        f"platform:  {platform.platform()}\n"
        f"pandas:    {pd.__version__}\n"
        f"plotly:    {plotly.__version__}\n"
        f"streamlit: {st.__version__}",
        language="text",
    )
    st.markdown("**Audit collection window:**")
    st.code(
        f"start: {AUDIT_WINDOW_START.date()} 00:00 IST\n"
        f"end:   {AUDIT_WINDOW_END.date()} 23:59 IST\n"
        f"polling: every 30 minutes\n"
        f"OD pairs: 56 (28 corridors × 2 directions)",
        language="text",
    )

st.markdown(
    "Short corridors (sensitive to single signal cycles): "
    + ", ".join(sorted(SHORT_CORRIDOR_IDS))
    + ". These are footnoted on the Ranking page and require higher `n` before "
    "their peak-hour cells render in the heatmap."
)

st.divider()

# ---------------------------------------------------------------------------
# 6. Triangulation hooks
# ---------------------------------------------------------------------------
st.header("6. Triangulation with the rest of the audit")
st.markdown(
    "The Patna Mobility Audit has three pillars: the Citizen Survey, the Joint "
    "Physical Verification (JPV), and this Congestion Index Tool. The three are "
    "designed to triangulate. The tables below are placeholders for the cross-"
    "references that will be populated as the other two pillars complete — their "
    "presence here, even unfilled, demonstrates that this tool is designed for "
    "triangulation, not as a standalone artefact."
)

with st.expander("Citizen Survey alignment (placeholder)"):
    st.markdown(
        "For each corridor in the survey, compare the share of respondents who "
        "reported 'high congestion' against the corridor's PHCI. Alignment ⇒ "
        "the audit finding is doubly defensible. Divergence ⇒ probe further."
    )
    st.dataframe(
        pd.DataFrame({
            "corridor_id": [], "citizen_high_congestion_pct": [], "phci": [],
            "alignment": [],
        }),
        use_container_width=True,
    )

with st.expander("Joint Physical Verification photographs (placeholder)"):
    st.markdown(
        "Link JPV photograph IDs to corridor IDs so the audit report can pair "
        "ground-truth images with the quantitative finding for the same corridor."
    )
    st.dataframe(
        pd.DataFrame({"corridor_id": [], "jpv_photo_id": [], "observation_time": []}),
        use_container_width=True,
    )

with st.expander("Peer-city comparison (placeholder — 101-city programme)"):
    st.markdown(
        "When peer audit offices run this tool for their cities, the same metric "
        "definitions enable apples-to-apples comparison. Each peer city contributes "
        "their PHCI distribution and the worst-corridor BTI."
    )
    st.dataframe(
        pd.DataFrame({
            "city": [], "median_PHCI": [], "p95_PHCI": [], "worst_corridor_BTI": [],
        }),
        use_container_width=True,
    )

st.caption(
    "Methodology page last refreshed at the same data-cache TTL as every other page. "
    "Re-running the dashboard against the same input files will reproduce every "
    "number above to the last decimal."
)
