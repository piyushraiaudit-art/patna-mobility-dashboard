"""Page 0 — User Guide.

Plain-English explanations of every metric and every dashboard page,
with all short forms expanded on first use. Designed so a non-technical
auditor, an auditee, or a press reporter can understand any number on
the dashboard without a statistics background.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="User Guide", page_icon="📖", layout="wide")

st.title("User Guide")
st.caption(
    "Plain-English guide to every page and every number on this dashboard. "
    "If you are seeing this tool for the first time, read this page first."
)

# ---------------------------------------------------------------------------
# What this dashboard is, in one paragraph
# ---------------------------------------------------------------------------
st.header("What this dashboard is")
st.markdown(
    """
    This is a measurement tool for the **Patna Urban Mobility Audit** being conducted
    by the **Comptroller and Auditor General of India (CAG)**. It does one job: for
    28 important roads of Patna, it asks Google Maps every 30 minutes how long the
    drive currently takes, compares that to how long the drive *would* take with
    zero traffic, and stores the answer. After 8 days, we have approximately
    21,500 measurements. From those, the dashboard produces ranked lists, heatmaps,
    and a map that show **which roads of Patna are congested, when, and by how much**.

    The point of all this is to replace statements like "Bailey Road feels congested"
    with statements like "Bailey Road takes 11 minutes at 6 AM and 36 minutes at
    6:30 PM, every weekday" — numbers that the state government and traffic police
    cannot easily dispute.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# The one number everything is built on: Congestion Ratio
# ---------------------------------------------------------------------------
st.header("The one number everything is built on")
st.subheader("Congestion Ratio (CR)")

st.markdown(
    """
    **Congestion Ratio (CR)** = (how long the trip takes right now) ÷ (how long the
    trip would take with no traffic).

    - **CR = 1.0** → traffic is flowing freely. The drive takes the time Google's model
      expects with no congestion.
    - **CR = 1.5** → the drive is taking 50% longer than it would with no traffic.
      A 20-minute drive now takes 30 minutes.
    - **CR = 2.0** → the drive is taking **twice** as long as it would with no traffic.
      A 20-minute drive now takes 40 minutes.
    - **CR = 0.9** → traffic is *faster* than Google's free-flow estimate. This is real
      and happens in deep off-peak hours. We do not hide these values.

    Every other number on this dashboard is built by summarising many Congestion Ratios
    over time. We collect one CR per road, per direction, every 30 minutes — that is
    48 CRs per direction per day.
    """
)

st.info(
    "**Why a ratio and not minutes?** Different roads are different lengths. A 60-second "
    "delay on a 1 km road is a disaster; the same 60 seconds on a 10 km road is normal. "
    "The Congestion Ratio compares each road to its own free-flow baseline, so all 28 "
    "roads can be compared on the same scale."
)

st.divider()

# ---------------------------------------------------------------------------
# Page 1 — Congestion Index Ranking
# ---------------------------------------------------------------------------
st.header("Page 1 — Congestion Index Ranking")
st.markdown("**What you see on this page:** a chart and table that rank Patna's 28 roads from worst to least congested.")

st.subheader("The headline metric: Peak-Hour Congestion Index (PHCI)")
st.markdown(
    """
    **Peak-Hour Congestion Index (PHCI)** is the answer to the question: *"In the
    worst rush-hour slot of any weekday, on the worst direction of this road, how
    bad does congestion get?"*

    **How it is calculated, in plain words:**
    1. Take all the Congestion Ratio (CR) measurements collected for this road in
       peak hours — i.e., morning rush (8 AM to 11 AM) and evening rush (5 PM to
       8 PM), weekdays only.
    2. For each peak hour separately (8 AM, 9 AM, 10 AM, 5 PM, 6 PM, 7 PM), and
       each direction separately, take the **middle value** of all measurements
       in that hour (the median — see glossary).
    3. The PHCI of the road is the **largest** of those six middle values, across
       both directions.

    In one sentence: PHCI is the worst it gets, on the worst direction, in the
    worst rush-hour slot, on a typical weekday.

    **How to read a PHCI number:**

    | PHCI value | What it means |
    |---|---|
    | Below 1.10 | Road is essentially free-flowing even at peak hour |
    | 1.10 to 1.25 | Mild peak-hour congestion |
    | 1.25 to 1.50 | Noticeable congestion — drivers can tell |
    | 1.50 to 2.00 | Heavy peak congestion — drivers must plan around it |
    | Above 2.00 | Severe — peak drive is more than twice the free-flow time |
    """
)

st.subheader("The secondary metric: All-Day Congestion Index (ADCI)")
st.markdown(
    """
    **All-Day Congestion Index (ADCI)** answers: *"Across the entire active day
    (6 AM to 10 PM), how congested is this road on average?"*

    A road can have a high PHCI but a low ADCI — meaning it gets very bad at peak
    but is fine the rest of the day. Or a road can have a moderate PHCI but a high
    ADCI — meaning it stays congested for many hours, not just at peak. Both kinds
    of road matter for different audit recommendations.

    **How it is calculated:** for each active hour of the day, take the middle CR
    value. Then average those hourly middle values together.
    """
)

st.subheader("The cross-check metric: peak minutes lost per trip")
st.markdown(
    """
    Same data, different lens. A 1 km short road can show a dramatic CR of 2.0 but
    only **60 seconds** of real delay (because the free-flow time is also short).
    A 7 km long road can show a modest CR of 1.3 but **5 minutes** of real delay.

    The "minutes lost" table on Page 1 ranks roads by how many real minutes a
    peak-hour driver loses compared to driving in free-flow conditions. Use this
    cross-check before recommending interventions for short corridors.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Page 2 — Hourly Heatmap
# ---------------------------------------------------------------------------
st.header("Page 2 — Hourly Heatmap")
st.markdown(
    """
    **What you see on this page:** a coloured grid where every **row** is one of
    Patna's 28 roads and every **column** is one hour of the day (6 AM to 10 PM).
    Each cell is coloured by how congested that road is at that hour.

    **The colour scale:**

    | Colour | What it means |
    |---|---|
    | White | Free-flowing (Congestion Ratio around 1.0) |
    | Pale orange | Mild congestion (1.10 to 1.25) |
    | Orange | Noticeable congestion (1.25 to 1.50) |
    | Red | Heavy congestion (1.50 to 2.00) |
    | Dark red | Severe congestion (above 2.00) |
    | Blue | Faster than free-flow (rare; off-peak) |
    | Grey with diagonal lines | Not enough measurements yet to draw a conclusion |

    **What to look for:**
    - **Wide red bands** in a row mean the road stays congested for many hours — a
      long peak window, not just a brief spike.
    - **Two distinct red blocks** in a row mean two separate rush-hour peaks (one
      in the morning, one in the evening) — typical of office-commuter corridors.
    - **A single red block** without the other usually means one-direction commuter
      flow.
    - **Dashed vertical lines** at 8, 11, 17, and 20 mark the peak window
      boundaries. Anything red inside these lines is the focus of audit findings.

    The Weekday panel and the Weekend panel are shown separately because traffic
    patterns differ. The Weekend panel is locked until the first Saturday or
    Sunday's data has been collected (16 May 2026 onwards).
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Page 3 — Direction Asymmetry
# ---------------------------------------------------------------------------
st.header("Page 3 — Direction Asymmetry")
st.markdown(
    """
    **What you see on this page:** for each road, the morning (8 AM to 11 AM) and
    evening (5 PM to 8 PM) Congestion Ratio split into the two directions of travel.

    **What "direction asymmetry" means:**
    Most commuter corridors are unbalanced. People drive *into* the city in the
    morning and *out of* the city in the evening. So one direction is much more
    congested than the other at any given peak. Example: Anisabad to Gandhi Maidan
    (heading north into the central business district) is heavily congested in the
    morning, while Gandhi Maidan to Anisabad (heading south, away from the city)
    is moderate. The reverse holds in the evening.

    **Why this matters for audit findings:**
    Symmetric congestion (both directions equally bad) typically means a capacity
    problem — the road is simply too narrow or has too few lanes for the demand.
    Asymmetric congestion typically means a flow problem — directional measures
    like one-way regulation during peak, contra-flow lanes, or signal-cycle
    retiming can help. The audit can recommend different interventions for the
    two patterns.

    **The asymmetry % number:**
    The bigger the difference between the two directions' Congestion Ratios, the
    higher the asymmetry percentage. 0% means perfectly symmetric. 40% means one
    direction is much worse than the other.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Page 4 — Reliability Index
# ---------------------------------------------------------------------------
st.header("Page 4 — Reliability Index")
st.markdown(
    """
    **What you see on this page:** two charts showing, for each road, how
    **predictable** (or unpredictable) the peak-hour commute is.

    A road can be **slow on average but predictable** (every day at 6 PM it takes
    exactly 30 minutes) — bad, but at least a commuter can plan for it. A road
    can also be **fast on average but unreliable** (most days it takes 15 minutes,
    but on a bad day it suddenly takes 40 minutes) — worse, because the commuter
    must always budget for the bad day.

    The audit cares about both. We measure unreliability two different ways and
    show both, so any reader can pick the lens they prefer.
    """
)

st.subheader("Metric 1: Buffer Time Index (BTI)")
st.markdown(
    r"""
    **Buffer Time Index (BTI)** answers: *"How much extra time must a commuter
    budget to arrive on time 95 days out of 100?"*

    **How it is calculated, in plain words:**
    1. Take all the peak-hour drive durations for this road and direction.
    2. Find the typical drive duration (the median).
    3. Find the drive duration on a bad day — specifically, the 95th-percentile
       day, meaning 5% of days are worse than this and 95% are better.
    4. BTI = (bad-day duration − typical duration) ÷ typical duration.

    **How to read a BTI number:**

    | BTI value | Plain-English meaning |
    |---|---|
    | Below 0.15 | Reliable — the commute is roughly the same time every day |
    | 0.15 to 0.30 | Mostly reliable |
    | 0.30 to 0.50 | Unpredictable — must budget significant extra time |
    | Above 0.50 | Highly unpredictable — must budget large buffer |

    A BTI of 0.30 means: *to arrive on time 95 days out of 100, a commuter must
    budget 30% extra time*. So a 20-minute typical drive needs a 26-minute budget.

    This metric is the **US Federal Highway Administration (FHWA) standard** from
    their Mobility Monitoring Program, which makes it citable in the audit report.
    """
)

st.subheader("Metric 2: Coefficient of Variation (CV)")
st.markdown(
    r"""
    **Coefficient of Variation (CV)** is a simpler, more general measure of how
    spread-out the daily drive times are.

    **How it is calculated, in plain words:**
    CV = (standard deviation of peak drive times) ÷ (average peak drive time).

    Standard deviation measures how far typical days swing away from the average
    day. Dividing by the average makes the number unitless and comparable across
    roads.

    **How to read a CV number:**

    | CV value | Plain-English meaning |
    |---|---|
    | Below 0.10 | Drive times are very stable |
    | 0.10 to 0.20 | Some daily variation |
    | 0.20 to 0.35 | Significantly variable |
    | Above 0.35 | Highly volatile drive times |

    **Why both BTI and CV?**
    BTI tells you the cost of being on time. CV tells you the underlying
    variability. If both numbers say the road is unpredictable, the finding is
    doubly defensible. If they disagree, that itself is worth investigating.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Page 5 — Corridor Map
# ---------------------------------------------------------------------------
st.header("Page 5 — Corridor Map")
st.markdown(
    """
    **What you see on this page:** a map of Patna with all 28 audited roads drawn
    on top, each one coloured by its Peak-Hour Congestion Index (PHCI). Hovering
    any road shows its full statistics.

    **The colour scale is the same as the heatmap:** white = free-flow, orange =
    moderate, red = bad, dark red = severe.

    **Limitation to be aware of:** at present, each road on the map is drawn as a
    **straight line** between its start and end points. The straight line *does
    not* show which actual streets the route uses. This is purely a display
    limitation — the Congestion Ratio numbers themselves are calculated on the
    real road network. A planned upgrade will draw each road along its actual
    street geometry. Until then, use the **corridor name** (e.g., "Bailey Road:
    Income Tax Roundabout ↔ Hartali Mor") to know which streets are being
    measured.

    **What this map is good for:** sharing with the press, the State Government,
    and citizens. It is the single image that conveys "this is where Patna's
    traffic problem is" at a glance.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Pages 6 and 7 — short version, since these are mostly self-explanatory
# ---------------------------------------------------------------------------
st.header("Page 6 — Methodology & Data Quality")
st.markdown(
    """
    Reference page for reviewers. Contains the mathematical formulas, the coverage
    matrix (how complete the data is), the failure log (which API calls failed and
    why), the distance-drift table (proof that we audited whether Google measured
    the same road each time), and a reproducibility hash so two reviewers on two
    laptops can confirm they are looking at identical numbers.

    Open this page when a finding is challenged — every number on every other
    page is reconstructible from here.
    """
)

st.header("Page 7 — Downloads")
st.markdown(
    """
    One-click downloads of:
    - A **10-sheet Excel workbook** (`.xlsx`) suitable as the formal annexure to
      the audit report.
    - A **ZIP of all charts** as high-resolution PNG images (300 DPI, dots per
      inch — the print-quality standard) for embedding in the Word/PDF report.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Glossary of every short form
# ---------------------------------------------------------------------------
st.header("Glossary — all short forms in one place")
st.markdown(
    """
    | Short form | Full term | Plain-English meaning |
    |---|---|---|
    | **CR** | Congestion Ratio | (drive time now) ÷ (drive time with no traffic) |
    | **PHCI** | Peak-Hour Congestion Index | Worst weekday peak-hour CR, taken on the worst direction |
    | **ADCI** | All-Day Congestion Index | Average CR across active hours (6 AM to 10 PM) |
    | **BTI** | Buffer Time Index | Extra time to budget to be on time 95 days out of 100 |
    | **CV** | Coefficient of Variation | Day-to-day variability of peak drive times |
    | **OD pair** | Origin-Destination pair | One direction of one road (start point → end point) |
    | **IST** | Indian Standard Time | The clock our timestamps use (UTC+5:30) |
    | **API** | Application Programming Interface | The Google service we ask "how long does this drive take?" |
    | **CSV** | Comma-Separated Values | The file format the measurements are stored in |
    | **MD5** | Message-Digest algorithm 5 | A short fingerprint of a file — same input gives same MD5 |
    | **p95** | 95th percentile | The value that 95% of measurements are below |
    | **median** | (no short form) | The middle value when measurements are sorted in order |
    | **n** | (sample size) | The number of measurements behind a given number |
    | **FHWA** | Federal Highway Administration (US) | The agency whose BTI definition we use |
    | **CAG** | Comptroller and Auditor General (of India) | The audit body conducting this study |
    | **JPV** | Joint Physical Verification | The on-site inspection pillar of this audit |
    | **GCP** | Google Cloud Platform | The infrastructure that runs the data collector |
    | **DPI** | Dots Per Inch | Image resolution (300 DPI = print quality) |
    """
)

st.divider()

# ---------------------------------------------------------------------------
# A note on "preliminary" vs "stable"
# ---------------------------------------------------------------------------
st.header("\"Locked\", \"Preliminary\", and \"Stable\" badges")
st.markdown(
    """
    Many pages show a small badge above each chart indicating how trustworthy the
    number currently is:

    - 🔒 **Locked** — there is not enough data yet to compute the metric. The
      chart is hidden until more measurements arrive.
    - 🟡 **Preliminary** — there is enough data to compute the metric, but the
      sample size is small. Quote the number along with its `n` (sample size).
    - 🟢 **Stable** — the sample size has crossed the threshold for
      audit-defensibility. The number can be cited in the report without caveat.

    These badges update automatically as the data collector adds new measurements
    every 30 minutes. By 20 May 2026 (end of the audit window), every metric on
    every page should be Stable.
    """
)

st.caption(
    "If anything on the dashboard is still unclear after reading this guide, "
    "the Methodology & Data Quality page (Page 6) contains the mathematical "
    "formulas and the full data-quality audit."
)
