"""
Shared UI chrome for the Patna Mobility dashboard.

Single source of truth for the Modern-SaaS visual language: global CSS,
page header, KPI tiles, "so what" callouts, sidebar status pills, and the
sidebar glossary expander. Every page imports from this module and calls
`apply_page_chrome(...)` at the top so the look stays consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import streamlit as st

__all__ = [
    "KPI",
    "ACCENT_COLORS",
    "apply_page_chrome",
    "audit_context_caption",
    "callout",
    "heatmap_color_legend",
    "inject_global_css",
    "kpi_row",
    "page_header",
    "render_sidebar",
    "sidebar_freshness_footer",
    "sidebar_glossary_expander",
    "sidebar_status_pills",
    "top_rank_list",
]


# ---------------------------------------------------------------------------
# Global CSS — injected once per page render. Streamlit re-runs the script
# top-to-bottom, so calling this from every page is fine.
# ---------------------------------------------------------------------------

_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; letter-spacing: -0.01em; }

/* Page header */
.patna-hero {
    background: linear-gradient(135deg, #EEF2FF 0%, #F8FAFC 60%, #FFFFFF 100%);
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 22px 26px;
    margin: 4px 0 18px 0;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.patna-hero-title {
    font-size: 26px;
    font-weight: 700;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.patna-hero-subtitle {
    font-size: 13.5px;
    color: #475569;
    margin-top: 6px;
    font-weight: 400;
    line-height: 1.5;
}
.patna-hero-eyebrow {
    font-size: 11px;
    font-weight: 600;
    color: #4F46E5;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}

/* KPI cards */
.patna-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 12px;
    margin: 4px 0 18px 0;
}
.patna-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 16px 12px 16px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    position: relative;
    overflow: hidden;
}
.patna-card::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--accent, #4F46E5);
}
.patna-kpi-label {
    font-size: 10.5px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0;
}
.patna-kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #0F172A;
    margin: 4px 0 2px 0;
    line-height: 1.15;
    letter-spacing: -0.01em;
}
.patna-kpi-sublabel {
    font-size: 11.5px;
    color: #64748B;
    margin: 0;
    line-height: 1.4;
}

/* Callouts */
.patna-callout {
    border-radius: 12px;
    padding: 14px 18px;
    margin: 14px 0;
    border-left: 4px solid var(--accent, #4F46E5);
    background: var(--bg, #EEF2FF);
}
.patna-callout-title {
    font-size: 12px;
    font-weight: 700;
    color: var(--accent, #4F46E5);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 6px 0;
}
.patna-callout-body {
    font-size: 13.5px;
    color: #1E293B;
    line-height: 1.55;
    margin: 0;
}
.patna-callout-body ul { margin: 6px 0 0 18px; padding: 0; }
.patna-callout-body li { margin-bottom: 4px; }

/* Status pills (sidebar) */
.patna-status-list { margin: 4px 0 12px 0; padding: 0; list-style: none; }
.patna-status-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0;
    border-bottom: 1px dashed #E2E8F0;
    font-size: 12px;
}
.patna-status-row:last-child { border-bottom: none; }
.patna-status-label { color: #334155; font-weight: 500; }
.patna-status-pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.patna-pill-locked     { background: #F1F5F9; color: #64748B; }
.patna-pill-prelim     { background: #FEF3C7; color: #92400E; }
.patna-pill-stable     { background: #D1FAE5; color: #065F46; }

/* Ranked-list (paired with mini-map) */
.patna-ranklist {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.patna-ranklist-title {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 10px 0;
}
.patna-ranklist-row {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 0;
    border-bottom: 1px solid #F1F5F9;
}
.patna-ranklist-row:last-child { border-bottom: none; }
.patna-ranklist-badge {
    flex: 0 0 auto;
    width: 26px; height: 26px;
    border-radius: 999px;
    color: #FFFFFF;
    font-weight: 700;
    font-size: 13px;
    display: inline-flex; align-items: center; justify-content: center;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.15);
}
.patna-ranklist-body { flex: 1 1 auto; min-width: 0; }
.patna-ranklist-name {
    font-size: 13px;
    font-weight: 600;
    color: #0F172A;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.patna-ranklist-meta {
    font-size: 11px;
    color: #64748B;
    margin-top: 2px;
}
.patna-ranklist-phci {
    flex: 0 0 auto;
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
    font-variant-numeric: tabular-nums;
}
.patna-ranklist-foot {
    font-size: 10.5px;
    color: #94A3B8;
    margin: 8px 0 0 0;
    padding-top: 8px;
    border-top: 1px dashed #E2E8F0;
    line-height: 1.4;
}

/* Heatmap inline legend */
.patna-legend {
    display: flex; flex-wrap: wrap; gap: 6px;
    align-items: center;
    margin: 6px 0 10px 0;
    font-size: 11.5px;
    color: #475569;
}
.patna-legend-chip {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 6px;
    font-weight: 600;
    border: 1px solid rgba(15, 23, 42, 0.08);
}

/* Audit context caption */
.patna-context {
    font-size: 11.5px;
    color: #64748B;
    padding: 8px 12px;
    background: #F8FAFC;
    border-radius: 8px;
    margin: 8px 0 14px 0;
    border: 1px solid #E2E8F0;
}

/* Sidebar tweaks */
[data-testid="stSidebar"] { background: #F8FAFC; }
[data-testid="stSidebar"] .patna-side-title {
    font-size: 14px; font-weight: 700; color: #0F172A; margin: 0;
    letter-spacing: -0.01em;
}
[data-testid="stSidebar"] .patna-side-sub {
    font-size: 11px; color: #64748B; margin: 2px 0 12px 0;
}

/* Print */
@media print {
    [data-testid="stSidebar"], [data-testid="stToolbar"], [data-testid="stHeader"] {
        display: none !important;
    }
    .patna-card, .patna-callout, .patna-hero {
        page-break-inside: avoid;
        box-shadow: none !important;
    }
    body { font-size: 11pt; }
    .stPlotlyChart, .stDeckGlJsonChart { page-break-inside: avoid; }
}
</style>
"""


def inject_global_css() -> None:
    """Inject the global stylesheet. Idempotent — safe to call from every page."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

def page_header(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    """Render the standard page hero block."""
    parts = ['<div class="patna-hero">']
    if eyebrow:
        parts.append(f'<div class="patna-hero-eyebrow">{eyebrow}</div>')
    parts.append(f'<div class="patna-hero-title">{title}</div>')
    if subtitle:
        parts.append(f'<div class="patna-hero-subtitle">{subtitle}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

ACCENT_COLORS = {
    "indigo":  "#4F46E5",
    "amber":   "#F59E0B",
    "rose":    "#EF4444",
    "emerald": "#10B981",
    "cyan":    "#06B6D4",
    "violet":  "#8B5CF6",
    "slate":   "#64748B",
}


@dataclass
class KPI:
    label: str
    value: str
    sublabel: str = ""
    accent: str = "indigo"


def kpi_row(cards: Iterable[KPI | dict]) -> None:
    """Render a responsive grid of KPI cards.

    Accepts KPI dataclass instances or plain dicts with the same keys.
    """
    items = []
    for c in cards:
        if isinstance(c, dict):
            c = KPI(**c)
        accent = ACCENT_COLORS.get(c.accent, ACCENT_COLORS["indigo"])
        items.append(
            f'<div class="patna-card" style="--accent:{accent};">'
            f'<div class="patna-kpi-label">{c.label}</div>'
            f'<div class="patna-kpi-value">{c.value}</div>'
            + (f'<div class="patna-kpi-sublabel">{c.sublabel}</div>' if c.sublabel else "")
            + '</div>'
        )
    st.markdown(
        f'<div class="patna-kpi-grid">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Callout box
# ---------------------------------------------------------------------------

_CALLOUT_VARIANTS = {
    "insight": ("#4F46E5", "#EEF2FF"),
    "warning": ("#D97706", "#FEF3C7"),
    "good":    ("#059669", "#D1FAE5"),
    "neutral": ("#475569", "#F1F5F9"),
}


def callout(body: str, kind: str = "insight", title: str = "") -> None:
    """Render a "so what" callout box. `body` may contain Markdown/HTML."""
    accent, bg = _CALLOUT_VARIANTS.get(kind, _CALLOUT_VARIANTS["insight"])
    title_html = (
        f'<div class="patna-callout-title" style="color:{accent};">{title}</div>'
        if title else ""
    )
    st.markdown(
        f'<div class="patna-callout" style="--accent:{accent}; --bg:{bg};">'
        f'{title_html}'
        f'<div class="patna-callout-body">{body}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Audit context caption — small footer used after charts
# ---------------------------------------------------------------------------

def audit_context_caption(extra: str = "") -> None:
    base = ("28 Patna corridors · 13–20 May 2026 · Google Routes API v2 (30-min polling). "
            "Data-driven evidence base for the Patna Urban Mobility Audit.")
    text = f"{base} {extra}".strip()
    st.markdown(f'<div class="patna-context">{text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Heatmap inline legend
# ---------------------------------------------------------------------------

def top_rank_list(ranking, top_n: int = 5, title: str = "Top corridors",
                  footer: str = "") -> None:
    """Color-matched ranked list designed to sit beside the mini-map.

    `ranking` must include columns: rank, corridor_name, phci, phci_hour
    (and optionally phci_direction). Badge colors mirror the PHCI colour
    scale used on the map, so a number in the list visually maps to a
    line on the map without any text labels on the map itself.
    """
    if ranking is None or len(ranking) == 0:
        return
    rows_html = []
    sub = ranking.head(top_n)
    for _, r in sub.iterrows():
        phci_v = float(r["phci"])
        rgb = _phci_rgb(phci_v)
        badge_bg = f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"
        name = str(r["corridor_name"])
        meta_bits = []
        if "phci_hour" in r and r["phci_hour"] is not None:
            try:
                meta_bits.append(f"worst at {int(r['phci_hour']):02d}:00")
            except (TypeError, ValueError):
                pass
        if "phci_direction" in r and r["phci_direction"]:
            meta_bits.append(str(r["phci_direction"]))
        meta = " · ".join(meta_bits) or "&nbsp;"
        rows_html.append(
            f'<div class="patna-ranklist-row">'
            f'<span class="patna-ranklist-badge" style="background:{badge_bg};">'
            f'{int(r["rank"])}</span>'
            f'<div class="patna-ranklist-body">'
            f'<div class="patna-ranklist-name" title="{name}">{name}</div>'
            f'<div class="patna-ranklist-meta">{meta}</div>'
            f'</div>'
            f'<span class="patna-ranklist-phci">PHCI {phci_v:.2f}</span>'
            f'</div>'
        )
    foot_html = f'<div class="patna-ranklist-foot">{footer}</div>' if footer else ""
    st.markdown(
        f'<div class="patna-ranklist">'
        f'<div class="patna-ranklist-title">{title}</div>'
        + "".join(rows_html) + foot_html + "</div>",
        unsafe_allow_html=True,
    )


def _phci_rgb(v: float) -> tuple[int, int, int]:
    """Mirror viz._phci_to_rgb so badge colors match the map lines."""
    if v != v:  # NaN
        return (156, 163, 175)
    if v < 1.0:
        return (59, 130, 246)
    if v < 1.25:
        return (252, 211, 77)
    if v < 1.5:
        return (249, 115, 22)
    if v < 2.0:
        return (220, 38, 38)
    return (127, 29, 29)


def heatmap_color_legend() -> None:
    """The CR colour-scale legend used above the heatmap and the map."""
    chips = [
        ("&lt; 1.0 (faster)", "#3b82f6", "white"),
        ("1.0 free-flow",     "#FFFFFF", "#0F172A"),
        ("1.0–1.25",          "#fcd34d", "#0F172A"),
        ("1.25–1.5",          "#f97316", "white"),
        ("1.5–2.0",           "#dc2626", "white"),
        ("≥ 2.0",             "#7f1d1d", "white"),
    ]
    spans = "".join(
        f'<span class="patna-legend-chip" style="background:{bg};color:{fg};">{label}</span>'
        for label, bg, fg in chips
    )
    st.markdown(
        f'<div class="patna-legend"><span style="font-weight:600;color:#334155;">'
        f'Median Congestion Ratio:</span>{spans}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar — global chrome on every page
# ---------------------------------------------------------------------------

def sidebar_status_pills(status_list: list[tuple[str, str, str]]) -> None:
    """Render the metric-readiness strip in the sidebar."""
    pill_class = {
        "Locked":      "patna-pill-locked",
        "Preliminary": "patna-pill-prelim",
        "Stable":      "patna-pill-stable",
    }
    rows = []
    for label, state, _detail in status_list:
        cls = pill_class.get(state, "patna-pill-locked")
        rows.append(
            f'<li class="patna-status-row">'
            f'<span class="patna-status-label">{label}</span>'
            f'<span class="patna-status-pill {cls}">{state}</span>'
            f'</li>'
        )
    st.sidebar.markdown(
        '<div style="font-size:11px;font-weight:600;color:#64748B;'
        'text-transform:uppercase;letter-spacing:0.06em;margin:6px 0 2px 0;">'
        'Metric readiness</div>'
        f'<ul class="patna-status-list">{"".join(rows)}</ul>',
        unsafe_allow_html=True,
    )


def sidebar_glossary_expander() -> None:
    """Collapsible 'How to read this dashboard' for every page."""
    with st.sidebar.expander("How to read this dashboard"):
        st.markdown(
            """
**Congestion Ratio (CR)** — live travel time ÷ free-flow travel time.
A CR of 1.50 means the trip took 50% longer than free-flow.

**PHCI** — Peak-Hour Congestion Index. Worst-direction, worst-peak-hour
weekday median CR per corridor. Headline metric.

**ADCI** — All-Day Congestion Index. Mean of hourly median CRs across
06:00–21:59. Captures spread, not just peak.

**BTI** — Buffer Time Index (FHWA standard).
*(p95 − median) ÷ median* peak duration. A BTI of 0.30 means commuters
must budget 30% extra time to be on-time 95 days out of 100.

**CV** — Coefficient of Variation. σ ÷ μ of peak duration. Cross-check
on BTI; less sensitive to small samples.

**Peak windows** — 08–11 AM and 17–20 PM IST (NUTP convention,
Bihar govt office hours).

**Gating** — Locked = insufficient data; Preliminary = directional only,
quote with `n`; Stable = audit-defensible.
            """
        )


def sidebar_freshness_footer(stats) -> None:
    """Last timestamp + reproducibility hash in the sidebar footer."""
    st.sidebar.markdown(
        f'<div style="font-size:10.5px;color:#64748B;margin-top:14px;'
        f'padding-top:10px;border-top:1px solid #E2E8F0;line-height:1.5;">'
        f'<b>As of:</b> {stats.last_timestamp} IST<br>'
        f'<b>MD5:</b> <code style="font-size:10px;">{stats.observations_md5[:12]}…</code><br>'
        f'<b>Source:</b> Google Routes API v2'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_sidebar(df, ranking, stats) -> None:
    """One call to render the global sidebar chrome on every page.

    Order: brand block → status pills → glossary expander → freshness footer.
    """
    from metrics import build_gating_status

    st.sidebar.markdown(
        '<div class="patna-side-title">Patna Mobility Audit</div>'
        '<div class="patna-side-sub">CAG audit window · 13–20 May 2026</div>',
        unsafe_allow_html=True,
    )
    sidebar_status_pills(build_gating_status(df, ranking))
    sidebar_glossary_expander()
    sidebar_freshness_footer(stats)


# ---------------------------------------------------------------------------
# Page setup helper — called at top of every page
# ---------------------------------------------------------------------------

def apply_page_chrome(df, ranking, stats) -> None:
    """One-stop setup: inject CSS + render the sidebar."""
    inject_global_css()
    render_sidebar(df, ranking, stats)
