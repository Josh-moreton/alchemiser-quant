#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Simple Streamlit dashboard for P&L visualization.

Run locally: streamlit run scripts/pnl_dashboard.py
Deploy: Push to GitHub, connect to Streamlit Cloud (free)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

# Page config
st.set_page_config(
    page_title="Octarine Capital - P&L Dashboard",
    page_icon="📈",
    layout="wide",
)

# Load data
EXCEL_PATH = Path.home() / "Library/CloudStorage/OneDrive-rwx_t/Octarine Capital/pnl.xlsx"


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data() -> pd.DataFrame:
    """Load P&L data from Excel file."""
    df = pd.read_excel(EXCEL_PATH, sheet_name="pnlTable", engine="openpyxl")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# Load data
try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Excel file not found: {EXCEL_PATH}")
    st.stop()

# Header
st.title("📈 Octarine Capital - P&L Dashboard")
st.caption(f"Data from {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")

# Key metrics row
col1, col2, col3, col4 = st.columns(4)

current_equity = df["Equity"].iloc[-1]
total_pnl = df["Cumulative P&L"].iloc[-1]
total_return = df["Cumulative Return (%)"].iloc[-1]
total_deposits = df["Deposits"].sum()

with col1:
    st.metric("Current Equity", f"${current_equity:,.2f}")
with col2:
    st.metric("Total P&L", f"${total_pnl:+,.2f}", delta=f"{total_return:+.2f}%")
with col3:
    st.metric("Total Deposits", f"${total_deposits:,.2f}")
with col4:
    # Today's P&L
    today_pnl = df["P&L ($)"].iloc[-1]
    today_pct = df["P&L (%)"].iloc[-1]
    st.metric("Latest Day P&L", f"${today_pnl:+,.2f}", delta=f"{today_pct:+.2f}%")

st.divider()

# Charts
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Equity Curve")
    st.line_chart(df.set_index("Date")["Equity"], use_container_width=True)

with col_right:
    st.subheader("Cumulative P&L")
    st.line_chart(df.set_index("Date")["Cumulative P&L"], use_container_width=True)

st.divider()

# Daily P&L bar chart
st.subheader("Daily P&L")
st.bar_chart(df.set_index("Date")["P&L ($)"], use_container_width=True)

st.divider()

# Monthly summary
st.subheader("Monthly Summary")
df["Month"] = df["Date"].dt.to_period("M").astype(str)
monthly = df.groupby("Month").agg({
    "P&L ($)": "sum",
    "Equity": "last",
    "Deposits": "sum",
}).round(2)
monthly.columns = ["P&L ($)", "End Equity", "Deposits"]
st.dataframe(monthly, use_container_width=True)

st.divider()

# Raw data (expandable)
with st.expander("View Raw Data"):
    st.dataframe(df, use_container_width=True)

# Footer
st.caption("Auto-refreshes every 5 minutes. Last updated: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
