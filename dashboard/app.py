"""
Patna Mobility Congestion Index — entry point.

`streamlit run dashboard/app.py` lands here, then redirects to the
Executive Summary page (which is also the first page in the sidebar nav).

Run locally:
    streamlit run dashboard/app.py

Public hosted version (auto-rebuilt on every git push):
    https://patna-mobility-dashboard.streamlit.app
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Patna Mobility Congestion Index",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.switch_page("pages/0_Executive_Summary.py")
