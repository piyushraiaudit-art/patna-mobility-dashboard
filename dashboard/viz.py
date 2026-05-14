"""
Shared Plotly figure factories for the Patna congestion dashboard.

Every chart on every page goes through this module so the dashboard,
the Excel exporter, and the PNG export produce visually identical
artefacts. Colour scales and annotations are not parameterised — the
design choices on the heatmap (white=1.0 anchor, red=2.0+) are part
of the audit's visual language and must stay consistent.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# The Patna Congestion Heatmap colour scale — manual, not a Plotly default.
# Anchored so that white = free-flow boundary (1.0). Faster-than-free-flow
# values render blue (sanity-check region). Above 1.0 escalates orange→red.
# ---------------------------------------------------------------------------

HEATMAP_COLORSCALE = [
    [0.00, "#3b82f6"],   # 0.8  — faster than free-flow (blue)
    [0.118, "#93c5fd"],  # 1.0  — free-flow boundary, white
    [0.118, "#ffffff"],
    [0.265, "#fcd34d"],  # 1.25 — pale orange
    [0.412, "#f97316"],  # 1.5  — orange
    [0.706, "#dc2626"],  # 2.0  — red
    [1.00, "#7f1d1d"],   # 2.5+ — dark red
]
HEATMAP_ZMIN = 0.8
HEATMAP_ZMAX = 2.5
HEATMAP_ZMID = 1.0


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#6b7280"),
    )
    fig.update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def hourly_heatmap(
    hourly_median: pd.DataFrame,
    corridor_order: list[str],
    title: str,
    subtitle: str,
    weekday_or_weekend: str = "Weekday",
    hours: range = range(6, 23),
) -> go.Figure:
    """Render the corridor × hour heatmap for one panel (Weekday OR Weekend).

    `hourly_median` columns: corridor_id, corridor_name, direction, hour,
                             weekday_or_weekend, median_cr, n
    `corridor_order` is a list of corridor_id strings, top-down on Y axis
                     (worst PHCI first). Both directions of each corridor are
                     collapsed to the per-corridor median of medians for
                     display purposes — the per-direction view lives on page 3.
    """
    sub = hourly_median[hourly_median["weekday_or_weekend"] == weekday_or_weekend].copy()
    if sub.empty:
        return _empty_figure(f"No {weekday_or_weekend.lower()} observations yet.")

    # Collapse both directions: per (corridor, hour) take median of direction medians.
    collapsed = (
        sub.groupby(["corridor_id", "corridor_name", "hour"])
        .agg(median_cr=("median_cr", "median"), n=("n", "sum"))
        .reset_index()
    )

    hour_list = list(hours)
    pivot_val = collapsed.pivot(index="corridor_id", columns="hour", values="median_cr")
    pivot_n = collapsed.pivot(index="corridor_id", columns="hour", values="n")
    name_map = dict(zip(collapsed["corridor_id"], collapsed["corridor_name"]))

    # Reindex Y by the requested PHCI-sorted order, X by full hour range.
    pivot_val = pivot_val.reindex(index=corridor_order, columns=hour_list)
    pivot_n = pivot_n.reindex(index=corridor_order, columns=hour_list).fillna(0)

    y_labels = [
        f"{cid}. {name_map.get(cid, cid)[:50]}" for cid in corridor_order
    ]

    text = pivot_val.round(2).astype(object)
    text = text.where(pivot_n >= 3, "")
    text = text.where(pivot_n > 0, "")
    text_n = pivot_n.astype(int).astype(str).where(
        (pivot_n > 0) & (pivot_n < 3), ""
    )
    text_combined = text.where(text != "", "n=" + text_n).where(pivot_n > 0, "")

    hover = (
        "Corridor: %{customdata[1]}<br>"
        "Hour: %{x}:00<br>"
        "Median CR: %{z:.3f}<br>"
        "n = %{customdata[0]}<extra></extra>"
    )

    customdata = []
    for cid in corridor_order:
        row = []
        for h in hour_list:
            n_val = int(pivot_n.loc[cid, h]) if cid in pivot_n.index else 0
            row.append([n_val, name_map.get(cid, cid)])
        customdata.append(row)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_val.values,
            x=[f"{h:02d}" for h in hour_list],
            y=y_labels,
            colorscale=HEATMAP_COLORSCALE,
            zmin=HEATMAP_ZMIN, zmax=HEATMAP_ZMAX, zmid=HEATMAP_ZMID,
            text=text_combined.values,
            texttemplate="%{text}",
            textfont=dict(size=9),
            hovertemplate=hover,
            customdata=customdata,
            colorbar=dict(
                title="Median CR",
                tickvals=[0.8, 1.0, 1.25, 1.5, 2.0, 2.5],
                tickformat=".2f",
            ),
        )
    )

    # Vertical dashed lines at policy peak window boundaries: 08, 11, 17, 20.
    for hr in (8, 11, 17, 20):
        if hr in hour_list:
            x_pos = hour_list.index(hr) - 0.5
            fig.add_vline(x=x_pos, line=dict(color="#374151", width=1, dash="dash"))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><span style='font-size:11px;color:#6b7280'>{subtitle}</span>",
                   x=0.0, xanchor="left"),
        xaxis_title="Hour of day (IST)",
        yaxis=dict(autorange="reversed"),  # worst at top
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=240, r=40, t=80, b=40),
        height=max(420, 22 * len(corridor_order) + 120),
    )
    return fig


def ranking_bar(ranking: pd.DataFrame, metric: str = "phci",
                title: str = "Peak-Hour Congestion Index — 28 corridors") -> go.Figure:
    """Horizontal bar chart of corridors ranked by PHCI (or any chosen metric).

    Bars coloured on the same scale as the heatmap so the visual language
    is consistent. Short corridors (sensitive to signal-cycle noise) are
    hatched and asterisked.
    """
    if ranking.empty:
        return _empty_figure("Awaiting data.")

    df = ranking.copy().sort_values(metric, ascending=True).reset_index(drop=True)
    labels = [
        f"{r.corridor_id}. {r.corridor_name[:55]}"
        + (" *" if r.is_short_corridor else "")
        for r in df.itertuples()
    ]

    fig = go.Figure(
        data=go.Bar(
            x=df[metric],
            y=labels,
            orientation="h",
            marker=dict(
                color=df[metric],
                colorscale=HEATMAP_COLORSCALE,
                cmin=HEATMAP_ZMIN, cmax=HEATMAP_ZMAX, cmid=HEATMAP_ZMID,
                line=dict(color="#374151", width=0.5),
                showscale=False,
            ),
            text=df[metric].round(3),
            textposition="outside",
            hovertemplate=(
                "Corridor: %{y}<br>"
                f"{metric.upper()}: %{{x:.3f}}<br>"
                "<extra></extra>"
            ),
        )
    )
    fig.add_vline(x=1.0, line=dict(color="#374151", width=1, dash="dash"),
                  annotation_text="Free-flow (1.0)", annotation_position="top")
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.0, xanchor="left"),
        xaxis_title=metric.upper(),
        yaxis_title="",
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=280, r=80, t=60, b=40),
        height=max(420, 22 * len(df) + 100),
    )
    return fig


def direction_asymmetry_chart(asymmetry: pd.DataFrame, peak_label: str) -> go.Figure:
    """Paired horizontal bars per corridor: A_to_B vs B_to_A for one peak window."""
    sub = asymmetry[asymmetry["peak"] == peak_label].copy()
    if sub.empty:
        return _empty_figure(f"No {peak_label} data yet.")
    sub = sub.sort_values("asymmetry_pct", ascending=True)
    labels = [f"{r.corridor_id}. {r.corridor_name[:45]}" for r in sub.itertuples()]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub["median_cr_A_to_B"], y=labels, orientation="h",
        name="A → B", marker=dict(color="#2563eb"),
        hovertemplate="%{y}<br>A→B median CR: %{x:.3f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=sub["median_cr_B_to_A"], y=labels, orientation="h",
        name="B → A", marker=dict(color="#dc2626"),
        hovertemplate="%{y}<br>B→A median CR: %{x:.3f}<extra></extra>",
    ))
    fig.add_vline(x=1.0, line=dict(color="#374151", width=1, dash="dash"))
    fig.update_layout(
        barmode="group",
        title=dict(text=f"<b>Direction asymmetry — {peak_label}</b>",
                   x=0.0, xanchor="left"),
        xaxis_title="Median Congestion Ratio",
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=260, r=40, t=60, b=40),
        height=max(420, 22 * len(sub) + 100),
        legend=dict(orientation="h", y=-0.05),
    )
    return fig


def reliability_chart(bti_df: pd.DataFrame, metric: str = "bti") -> go.Figure:
    """BTI or CV per corridor-direction, horizontal bar.

    Adds a plain-English predictability label as text annotation.
    """
    if bti_df.empty:
        return _empty_figure("Awaiting data.")
    df = bti_df.copy().dropna(subset=[metric])
    df = df.sort_values(metric, ascending=True)
    labels = [f"{r.corridor_id} ({r.direction[0]}{r.direction[-1]}) — {r.corridor_name[:40]}"
              for r in df.itertuples()]

    def english_label(v: float) -> str:
        if metric == "bti":
            if v < 0.15: return "Reliable"
            if v < 0.30: return "Mostly reliable"
            if v < 0.50: return "Unpredictable"
            return "Highly unpredictable"
        else:
            if v < 0.10: return "Stable"
            if v < 0.20: return "Variable"
            if v < 0.35: return "Volatile"
            return "Highly volatile"

    text = [f"{v:.2f} — {english_label(v)}" for v in df[metric]]

    fig = go.Figure(go.Bar(
        x=df[metric], y=labels, orientation="h",
        marker=dict(color=df[metric], colorscale="Reds",
                    cmin=0, cmax=max(0.5, df[metric].max() or 0.5),
                    showscale=False),
        text=text, textposition="outside",
        hovertemplate="%{y}<br>" + metric.upper() + ": %{x:.3f}<extra></extra>",
    ))
    label_text = "Buffer Time Index (FHWA)" if metric == "bti" else "Coefficient of Variation"
    fig.update_layout(
        title=dict(text=f"<b>{label_text} — peak window</b>", x=0.0, xanchor="left"),
        xaxis_title=metric.upper(),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=320, r=200, t=60, b=40),
        height=max(420, 18 * len(df) + 100),
    )
    return fig


def coverage_heatmap(coverage: pd.DataFrame) -> go.Figure:
    """Corridor × date observation count, with cells coloured red/amber/green."""
    if coverage.empty:
        return _empty_figure("No coverage data.")
    pivot = coverage.pivot(index="corridor_id", columns="date", values="n_obs").fillna(0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, "#dc2626"],
            [0.5, "#fcd34d"],
            [1.0, "#16a34a"],
        ],
        zmin=0, zmax=48,
        text=pivot.values.astype(int),
        texttemplate="%{text}",
        textfont=dict(size=10),
        colorbar=dict(title="n obs/day"),
    ))
    fig.update_layout(
        title=dict(text="<b>Observation Coverage — corridor × date</b>",
                   x=0.0, xanchor="left"),
        xaxis_title="Date",
        yaxis_title="Corridor ID",
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=80, r=40, t=60, b=40),
        height=max(420, 16 * len(pivot) + 100),
    )
    return fig


def cr_cdf_chart(cr_values: pd.Series) -> go.Figure:
    """CDF of all CR values — Methodology page sanity check."""
    s = cr_values.dropna().sort_values().reset_index(drop=True)
    if s.empty:
        return _empty_figure("No CR observations.")
    y = (s.rank(method="first") / len(s)).values
    fig = go.Figure(go.Scatter(x=s.values, y=y, mode="lines",
                               line=dict(color="#1f2937", width=2)))
    fig.add_vline(x=1.0, line=dict(color="#dc2626", width=1, dash="dash"),
                  annotation_text="Free-flow (1.0)", annotation_position="top right")
    fig.update_layout(
        title=dict(text="<b>Empirical CDF of Congestion Ratio</b>", x=0.0, xanchor="left"),
        xaxis_title="Congestion Ratio",
        yaxis_title="Cumulative share of observations",
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=60, r=40, t=60, b=40),
        height=380,
    )
    return fig
