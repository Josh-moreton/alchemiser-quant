#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Enhanced Streamlit dashboard for The Alchemiser Trading System.

Multi-page dashboard with:
- Portfolio & PnL overview
- Last run analysis (strategies, signals, trades)
- Trade history & attribution
- Per-symbol analytics

Run locally: streamlit run scripts/dashboard.py
Deploy: Push to GitHub, connect to Streamlit Cloud (free)
"""

from __future__ import annotations

from pathlib import Path

import _setup_imports  # noqa: F401
import streamlit as st
from dotenv import load_dotenv

# Load .env file before importing modules that use environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Page config
st.set_page_config(
    page_title="Octarine Capital - Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Navigation
st.sidebar.title("📊 Octarine Capital")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Portfolio Overview",
        "🎯 Last Run Analysis", 
        "📊 Trade History",
        "📈 Symbol Analytics",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Real-time trading system dashboard")

# Route to pages
if page == "🏠 Portfolio Overview":
    from dashboard_pages import portfolio_overview
    portfolio_overview.show()
elif page == "🎯 Last Run Analysis":
    from dashboard_pages import last_run_analysis
    last_run_analysis.show()
elif page == "📊 Trade History":
    from dashboard_pages import trade_history
    trade_history.show()
elif page == "📈 Symbol Analytics":
    from dashboard_pages import symbol_analytics
    symbol_analytics.show()
