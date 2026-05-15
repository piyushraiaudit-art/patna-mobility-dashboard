"""Page 7 — Downloads.

Maps to brief output #6: the multi-sheet Excel workbook intended as a direct
annexure to the audit report, plus a zip of all dashboard charts as
1600×1000 PNGs at 300 DPI for embedding in the formal Word/PDF report.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from data import data_quality_report, load_observations
from exports import build_excel_annexure, build_png_zip
from metrics import (
    bti as compute_bti, direction_asymmetry, hourly_median_cr, ranking_table,
)
from ui import apply_page_chrome, audit_context_caption, page_header
from viz import (
    coverage_heatmap, cr_cdf_chart, direction_asymmetry_chart, hourly_heatmap,
    ranking_bar, reliability_chart,
)

st.set_page_config(page_title="Downloads", page_icon="⬇️", layout="wide")


@st.cache_data(ttl=600)
def _load():
    return load_observations()


df = _load()
ranking = ranking_table(df)
rep = data_quality_report(df) if not df.empty else None
stats = rep["stats"] if rep is not None else None

if stats is not None:
    apply_page_chrome(df, ranking, stats)

page_header(
    title="Downloads",
    subtitle=("Audit-report-ready artefacts. The Excel workbook is the formal "
              "annexure; the PNG zip carries every chart at 1600×1000 / 300 DPI."),
    eyebrow="Page 7",
)

if df.empty:
    st.warning("No observations yet — exports unavailable.")
    st.stop()

stamp = datetime.now().strftime("%Y%m%d_%H%M")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Excel annexure (10 sheets)")
    st.markdown(
        "- **Cover** — audit metadata, MD5 hashes  \n"
        "- **Ranking** — PHCI / ADCI / BTI / CV per corridor  \n"
        "- **Hourly Medians** — raw of the heatmap  \n"
        "- **Direction Asymmetry** — AM/PM peak by direction  \n"
        "- **Reliability** — BTI + CV per corridor-direction  \n"
        "- **Coverage** — corridor × date, conditional-formatted  \n"
        "- **FAIL Log** — every failed API call with `error_msg`  \n"
        "- **Distance Drift** — re-route audit table  \n"
        "- **Methodology** — formulas, peak window, filters  \n"
        "- **Raw Observations** — full OK-filtered dataset"
    )
    with st.spinner("Building workbook…"):
        xlsx_bytes = build_excel_annexure(df, rep)
    st.download_button(
        "⬇ Download Patna_Congestion_Audit_Annexure.xlsx",
        data=xlsx_bytes,
        file_name=f"Patna_Congestion_Audit_Annexure_{stamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with col2:
    st.subheader("Charts — 300 DPI PNG bundle")
    st.markdown(
        "Each dashboard chart at 1600 × 1000 pixels, scale 2 (= 3200 × 2000 "
        "effective pixels). Drop straight into the Word report annexure with "
        "no rescaling artefacts."
    )
    if st.button("Build PNG bundle", use_container_width=True):
        order = ranking["corridor_id"].tolist()
        hm = hourly_median_cr(df)
        figs = {
            "01_ranking_phci.png": ranking_bar(ranking),
            "02a_heatmap_weekday.png": hourly_heatmap(
                hm, order, "Median Congestion Ratio — Weekday",
                "Source: Google Routes API v2, 30-min polling.",
                weekday_or_weekend="Weekday",
            ),
            "02b_heatmap_weekend.png": hourly_heatmap(
                hm, order, "Median Congestion Ratio — Weekend",
                "Source: Google Routes API v2, 30-min polling.",
                weekday_or_weekend="Weekend",
            ),
            "03a_direction_asymmetry_am.png": direction_asymmetry_chart(
                direction_asymmetry(df), "AM Peak"
            ),
            "03b_direction_asymmetry_pm.png": direction_asymmetry_chart(
                direction_asymmetry(df), "PM Peak"
            ),
            "04a_reliability_bti.png": reliability_chart(compute_bti(df), "bti"),
            "06_coverage_matrix.png": coverage_heatmap(rep["coverage"]),
            "06b_cr_cdf.png": cr_cdf_chart(rep["cr_distribution"]),
        }
        with st.spinner("Rendering PNGs (kaleido) …"):
            png_zip = build_png_zip(figs)
        st.download_button(
            "⬇ Download Patna_Congestion_Charts.zip",
            data=png_zip,
            file_name=f"Patna_Congestion_Charts_{stamp}.zip",
            mime="application/zip",
            use_container_width=True,
        )
        st.caption(
            "If any PNG file is replaced by a `.error.txt`, the kaleido package "
            "is not installed. Run `pip install kaleido==0.2.1` and rebuild."
        )

st.divider()
audit_context_caption(
    "Both bundles are stamped with the build timestamp in the filename. The Excel "
    "cover sheet carries the observations MD5 — match against Page 6 to confirm "
    "provenance."
)
