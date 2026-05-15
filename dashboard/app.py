"""
DIAGNOSTIC build of app.py.

The real dashboard entry point is preserved at dashboard/_app_real.py.
This file is a startup probe — it imports streamlit minimally, then walks
through every subsequent import / I/O / compute step inside try/except
blocks and renders any failure on the page so we can see what's actually
breaking on Streamlit Community Cloud.

Once we identify the bug and fix it, restore _app_real.py over app.py.
"""

from __future__ import annotations

import os
import platform
import sys
import traceback
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Patna — Startup Diagnostic", page_icon="🔍", layout="wide")
st.title("🔍 Patna Dashboard — Startup Diagnostic")
st.caption(
    "Temporary diagnostic build. Reports each startup step so we can see "
    "exactly what is failing on Streamlit Community Cloud."
)


def report_section(title: str):
    st.subheader(title)


def show_step(name: str, func):
    """Run func() inside try/except and render the outcome."""
    try:
        result = func()
        st.success(f"✓ {name}")
        if result is not None:
            st.write(result)
        return result
    except Exception:
        st.error(f"✗ {name}")
        st.code(traceback.format_exc(), language="text")
        st.stop()


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
report_section("1. Environment")
st.code(
    f"Python:     {sys.version}\n"
    f"Platform:   {platform.platform()}\n"
    f"Executable: {sys.executable}\n"
    f"cwd:        {os.getcwd()}\n"
    f"__file__:   {__file__}\n"
    f"Streamlit:  {st.__version__}",
    language="text",
)

report_section("2. sys.path")
st.code("\n".join(sys.path), language="text")

report_section("3. Filesystem at cwd")
try:
    listing = "\n".join(sorted(os.listdir(os.getcwd())))
except Exception:
    listing = traceback.format_exc()
st.code(listing, language="text")

report_section("4. Filesystem at __file__ parent")
try:
    listing = "\n".join(sorted(os.listdir(Path(__file__).resolve().parent)))
except Exception:
    listing = traceback.format_exc()
st.code(listing, language="text")

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
report_section("5. Library imports")
show_step("import pandas", lambda: __import__("pandas").__version__)
show_step("import numpy", lambda: __import__("numpy").__version__)
show_step("import plotly", lambda: __import__("plotly").__version__)
show_step("import openpyxl", lambda: __import__("openpyxl").__version__)
show_step("import pydeck", lambda: __import__("pydeck").__version__)

report_section("6. Project imports")
show_step("import data", lambda: __import__("data").__name__)
show_step("import metrics", lambda: __import__("metrics").__name__)
show_step("import viz", lambda: __import__("viz").__name__)
show_step("import exports", lambda: __import__("exports").__name__)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
from data import load_observations, data_quality_report

report_section("7. Data loading")
df = show_step("load_observations()", lambda: load_observations())
if df is not None:
    st.write(f"shape: {df.shape}")
    st.write(f"date range: {df['date'].min()} → {df['date'].max()}")
    st.write(f"corridors: {df['corridor_id'].nunique()}")

report_section("8. Data quality")
rep = show_step("data_quality_report(df)", lambda: data_quality_report(df))

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
from metrics import ranking_table

report_section("9. Metrics")
ranking = show_step("ranking_table(df)", lambda: ranking_table(df))
if ranking is not None:
    st.dataframe(ranking.head(5), use_container_width=True)

# ---------------------------------------------------------------------------
# All good — point to the real pages
# ---------------------------------------------------------------------------
st.divider()
st.success(
    "All startup steps passed. The diagnostic confirmed the dashboard can load "
    "and compute correctly. Restoring the real app.py now should yield a fully "
    "working dashboard."
)
