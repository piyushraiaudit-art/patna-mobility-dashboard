"""
Congestion metrics for the Patna Mobility audit dashboard.

All formulas live here. The dashboard pages, the Excel exporter, and the
Methodology page render their numbers from these functions — single source
of truth across every output.

Hard-coded peak windows (08:00-11:00 AM, 17:00-20:00 PM IST) are deliberate.
Data-driven peak detection is unstable on 2-8 days of data and invites the
"you fit the window to make the numbers look bad" objection. Anchor to
Bihar govt office hours and the National Urban Transport Policy convention.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Peak-window definition (overridable from sidebar, but ships with policy default)
# ---------------------------------------------------------------------------

AM_PEAK_HOURS = (8, 9, 10)
PM_PEAK_HOURS = (17, 18, 19)
PEAK_HOURS = AM_PEAK_HOURS + PM_PEAK_HOURS
ACTIVE_HOURS = tuple(range(6, 22))  # 06:00-21:59 inclusive for ADCI


# ---------------------------------------------------------------------------
# Gating thresholds — n-based sufficiency for each metric
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Threshold:
    min_n: int
    stable_n: int
    label: str


GATING = {
    "phci_weekday": Threshold(min_n=30, stable_n=100,
                              label="weekday peak-hour observations per corridor"),
    "phci_weekend": Threshold(min_n=20, stable_n=60,
                              label="weekend peak-hour observations per corridor"),
    "heatmap_cell_weekday": Threshold(min_n=1, stable_n=4,
                                      label="observations per (corridor, hour, weekday) cell"),
    "heatmap_weekend": Threshold(min_n=1, stable_n=2,
                                 label="weekend days of data"),
    "direction_asymmetry": Threshold(min_n=10, stable_n=30,
                                     label="observations per direction in the peak window"),
    "bti": Threshold(min_n=15, stable_n=40,
                     label="peak-window observations per corridor for BTI"),
    "cv":  Threshold(min_n=10, stable_n=30,
                     label="peak-window observations per corridor for CV"),
}


def gating_state(n: int, key: str) -> str:
    """Return one of 'Locked', 'Preliminary', 'Stable' for the given n."""
    t = GATING[key]
    if n < t.min_n:
        return "Locked"
    if n < t.stable_n:
        return "Preliminary"
    return "Stable"


# Short corridors where ratio is sensitive to signal-cycle noise.
SHORT_CORRIDOR_IDS = {"1", "4", "10", "17", "21", "23"}


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def weekday_observations(df: pd.DataFrame, include_holidays: bool = False) -> pd.DataFrame:
    out = df[df["weekday_or_weekend"] == "Weekday"]
    if not include_holidays:
        out = out[~out["is_bihar_holiday"]]
    return out


def weekend_observations(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["weekday_or_weekend"] == "Weekend"]


def peak_observations(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["hour"].astype(int).isin(PEAK_HOURS)]


def am_peak_observations(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["hour"].astype(int).isin(AM_PEAK_HOURS)]


def pm_peak_observations(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["hour"].astype(int).isin(PM_PEAK_HOURS)]


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def hourly_median_cr(df: pd.DataFrame) -> pd.DataFrame:
    """Median congestion ratio per (corridor_id, direction, hour, weekday_or_weekend).

    Also returns the observation count n for each cell.
    """
    grouped = (
        df.groupby(["corridor_id", "corridor_name", "direction", "hour", "weekday_or_weekend"])
        .agg(
            median_cr=("congestion_ratio", "median"),
            n=("congestion_ratio", "size"),
        )
        .reset_index()
    )
    return grouped


def phci(df: pd.DataFrame) -> pd.DataFrame:
    """Peak-Hour Congestion Index per corridor.

    For each corridor, take the max over the peak hours of the per-(direction, hour)
    weekday median congestion ratio. Both directions are aggregated by taking the
    max — represents "worst direction at worst peak hour".
    """
    wk = weekday_observations(df)
    wk_peak = peak_observations(wk)

    if wk_peak.empty:
        return pd.DataFrame(
            columns=["corridor_id", "corridor_name", "phci", "phci_hour",
                     "phci_direction", "n_peak"]
        )

    cell = (
        wk_peak.groupby(["corridor_id", "corridor_name", "direction", "hour"])
        .agg(median_cr=("congestion_ratio", "median"),
             n=("congestion_ratio", "size"))
        .reset_index()
    )
    idx = cell.groupby(["corridor_id", "corridor_name"])["median_cr"].idxmax()
    worst = cell.loc[idx].reset_index(drop=True)

    n_per_corridor = (
        wk_peak.groupby("corridor_id").size().rename("n_peak").reset_index()
    )

    out = worst.merge(n_per_corridor, on="corridor_id", how="left").rename(
        columns={"median_cr": "phci", "hour": "phci_hour", "direction": "phci_direction"}
    )
    return out[["corridor_id", "corridor_name", "phci", "phci_hour",
                "phci_direction", "n_peak"]].sort_values("phci", ascending=False)


def adci(df: pd.DataFrame) -> pd.DataFrame:
    """All-Day Congestion Index — mean over active hours (06-21) of the hourly median CR."""
    wk = weekday_observations(df)
    active = wk[wk["hour"].astype(int).isin(ACTIVE_HOURS)]
    if active.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "adci", "n_active"])

    hourly = (
        active.groupby(["corridor_id", "corridor_name", "hour"])
        .agg(median_cr=("congestion_ratio", "median"))
        .reset_index()
    )
    out = (
        hourly.groupby(["corridor_id", "corridor_name"])
        .agg(adci=("median_cr", "mean"))
        .reset_index()
    )
    n_active = active.groupby("corridor_id").size().rename("n_active").reset_index()
    out = out.merge(n_active, on="corridor_id", how="left")
    return out.sort_values("adci", ascending=False)


def bti(df: pd.DataFrame) -> pd.DataFrame:
    """Buffer Time Index per corridor, direction (FHWA standard).

    BTI = (p95(duration_traffic_s) - median(duration_traffic_s)) / median(...)
    Computed over the peak window only. Higher = less reliable commute.
    """
    wk_peak = peak_observations(weekday_observations(df))

    def _agg(g: pd.DataFrame) -> pd.Series:
        n = len(g)
        med = g["duration_traffic_s"].median()
        p95 = g["duration_traffic_s"].quantile(0.95)
        bti_val = (p95 - med) / med if med and med > 0 else np.nan
        return pd.Series(
            {
                "median_peak_s": med,
                "p95_peak_s": p95,
                "bti": bti_val,
                "n": n,
            }
        )

    if wk_peak.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "direction",
                                     "median_peak_s", "p95_peak_s", "bti", "n"])

    grouped = (
        wk_peak.groupby(["corridor_id", "corridor_name", "direction"])
        .apply(_agg, include_groups=False)
        .reset_index()
    )
    return grouped.sort_values("bti", ascending=False)


def cv(df: pd.DataFrame) -> pd.DataFrame:
    """Coefficient of variation of peak-window traffic duration per corridor, direction."""
    wk_peak = peak_observations(weekday_observations(df))

    def _agg(g: pd.DataFrame) -> pd.Series:
        n = len(g)
        mu = g["duration_traffic_s"].mean()
        sigma = g["duration_traffic_s"].std(ddof=1) if n > 1 else 0.0
        cv_val = sigma / mu if mu and mu > 0 else np.nan
        return pd.Series({"mu_peak_s": mu, "sigma_peak_s": sigma, "cv": cv_val, "n": n})

    if wk_peak.empty:
        return pd.DataFrame(columns=["corridor_id", "corridor_name", "direction",
                                     "mu_peak_s", "sigma_peak_s", "cv", "n"])

    grouped = (
        wk_peak.groupby(["corridor_id", "corridor_name", "direction"])
        .apply(_agg, include_groups=False)
        .reset_index()
    )
    return grouped.sort_values("cv", ascending=False)


def direction_asymmetry(df: pd.DataFrame) -> pd.DataFrame:
    """AM and PM peak median CR per direction, with asymmetry %.

    asymmetry_pct = |CR_A_to_B - CR_B_to_A| / max(CR_A_to_B, CR_B_to_A) * 100
    """
    wk = weekday_observations(df)

    def _peak_table(sub: pd.DataFrame, label: str) -> pd.DataFrame:
        agg = (
            sub.groupby(["corridor_id", "corridor_name", "direction"])
            .agg(median_cr=("congestion_ratio", "median"),
                 n=("congestion_ratio", "size"))
            .reset_index()
        )
        wide = agg.pivot_table(
            index=["corridor_id", "corridor_name"],
            columns="direction",
            values=["median_cr", "n"],
            aggfunc="first",
        )
        wide.columns = [f"{a}_{b}" for a, b in wide.columns]
        wide = wide.reset_index()
        for col in ("median_cr_A_to_B", "median_cr_B_to_A", "n_A_to_B", "n_B_to_A"):
            if col not in wide.columns:
                wide[col] = np.nan
        denom = wide[["median_cr_A_to_B", "median_cr_B_to_A"]].max(axis=1)
        diff = (wide["median_cr_A_to_B"] - wide["median_cr_B_to_A"]).abs()
        wide["asymmetry_pct"] = (100.0 * diff / denom).round(2)
        wide["peak"] = label
        return wide

    am = _peak_table(am_peak_observations(wk), "AM Peak")
    pm = _peak_table(pm_peak_observations(wk), "PM Peak")
    return pd.concat([am, pm], ignore_index=True)


def ranking_table(df: pd.DataFrame) -> pd.DataFrame:
    """The headline ranking table used on page 1 and the Excel Ranking sheet."""
    p = phci(df)
    a = adci(df)[["corridor_id", "adci", "n_active"]]
    b = (
        bti(df)
        .groupby("corridor_id")
        .agg(bti=("bti", "max"), n_bti=("n", "sum"))
        .reset_index()
    )
    c = (
        cv(df)
        .groupby("corridor_id")
        .agg(cv=("cv", "max"), n_cv=("n", "sum"))
        .reset_index()
    )

    out = (
        p.merge(a, on="corridor_id", how="left")
        .merge(b, on="corridor_id", how="left")
        .merge(c, on="corridor_id", how="left")
    )
    out["is_short_corridor"] = out["corridor_id"].isin(SHORT_CORRIDOR_IDS)
    out = out.sort_values("phci", ascending=False).reset_index(drop=True)
    out.insert(0, "rank", out.index + 1)
    return out


def build_gating_status(df: pd.DataFrame, ranking: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Return (label, state, detail) tuples for the global feature-gating strip.

    Used by the sidebar status pills and by the Executive Summary footer to give
    one consistent picture of which metrics are Locked / Preliminary / Stable.
    """
    out: list[tuple[str, str, str]] = []

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
        out.append(("Weekend heatmap", "Locked", "First Saturday: 2026-05-16"))
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


def minutes_lost_table(df: pd.DataFrame) -> pd.DataFrame:
    """Secondary ranking by absolute minutes lost in peak (cross-context for short corridors)."""
    wk_peak = peak_observations(weekday_observations(df))
    out = (
        wk_peak.groupby(["corridor_id", "corridor_name"])
        .agg(
            median_traffic_min=("duration_traffic_s", lambda s: s.median() / 60.0),
            median_freeflow_min=("duration_freeflow_s", lambda s: s.median() / 60.0),
            n=("congestion_ratio", "size"),
        )
        .reset_index()
    )
    out["minutes_lost"] = (out["median_traffic_min"] - out["median_freeflow_min"]).round(2)
    out["median_traffic_min"] = out["median_traffic_min"].round(2)
    out["median_freeflow_min"] = out["median_freeflow_min"].round(2)
    return out.sort_values("minutes_lost", ascending=False).reset_index(drop=True)
