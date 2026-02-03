#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Streamlit P&L dashboard fetching directly from Alpaca API.

Displays deposit-adjusted P&L metrics, equity curves, and monthly summaries.
Uses the shared PnLService with a 5-minute cache for API efficiency.

Run locally: streamlit run scripts/pnl_dashboard.py
Deploy: Push to GitHub, connect to Streamlit Cloud (free)
"""

from __future__ import annotations

from pathlib import Path

import _setup_imports  # noqa: F401
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load .env file before importing modules that use environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from the_alchemiser.shared.services.pnl_service import PnLService

# Page config
st.set_page_config(
    page_title="Octarine Capital - P&L Dashboard",
    page_icon=None,
    layout="wide",
)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data() -> pd.DataFrame:
    """Load P&L data from Alpaca API with deposit adjustments.

    Returns:
        DataFrame with columns: Date, Equity, P&L ($), P&L (%), Deposits,
        Withdrawals, Cumulative P&L, Cumulative Return (%)

    """
    service = PnLService()
    daily_records, _ = service.get_all_daily_records(period="1A")

    # Filter to active trading days only (equity > 0)
    active_records = [r for r in daily_records if r.equity > 0]

    if not active_records:
        return pd.DataFrame()

    # Convert to DataFrame
    rows = []
    for rec in active_records:
        rows.append({
            "Date": pd.to_datetime(rec.date),
            "Equity": float(rec.equity),
            "P&L ($)": float(rec.profit_loss),
            "P&L (%)": float(rec.profit_loss_pct),
            "Deposits": float(rec.deposit) if rec.deposit else 0.0,
            "Withdrawals": float(rec.withdrawal) if rec.withdrawal else 0.0,
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("Date").reset_index(drop=True)

    # Calculate cumulative columns
    df["Cumulative P&L"] = df["P&L ($)"].cumsum()

    # Cumulative return: (cumulative_pnl / first_equity) * 100
    first_equity = df.iloc[0]["Equity"] - df.iloc[0]["P&L ($)"]
    if first_equity > 0:
        df["Cumulative Return (%)"] = (df["Cumulative P&L"] / first_equity * 100).round(4)
    else:
        df["Cumulative Return (%)"] = 0.0

    return df


# Load data
try:
    df = load_data()
    if df.empty:
        st.error("No trading data available from Alpaca.")
        st.stop()
except Exception as e:
    st.error(f"Failed to load data from Alpaca: {e}")
    st.stop()

# Header
st.title("Octarine Capital - P&L Dashboard")
st.caption(
    f"Data from {df['Date'].min().strftime('%Y-%m-%d')} "
    f"to {df['Date'].max().strftime('%Y-%m-%d')}"
)

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
    st.line_chart(df.set_index("Date")["Equity"], width="stretch")

with col_right:
    st.subheader("Cumulative P&L")
    st.line_chart(df.set_index("Date")["Cumulative P&L"], width="stretch")

st.divider()

# Daily P&L bar chart
st.subheader("Daily P&L")
st.bar_chart(df.set_index("Date")["P&L ($)"], width="stretch")

st.divider()

# Monthly summary
st.subheader("Monthly Summary")
df["Month"] = df["Date"].dt.to_period("M").astype(str)
monthly = (
    df.groupby("Month")
    .agg({
        "P&L ($)": "sum",
        "Equity": "last",
        "Deposits": "sum",
    })
    .round(2)
)
monthly.columns = ["P&L ($)", "End Equity", "Deposits"]
st.dataframe(monthly, width="stretch")

st.divider()

# Raw data (expandable)
with st.expander("View Raw Data"):
    st.dataframe(df, width="stretch")

# Footer
st.caption(
    "Data from Alpaca API (deposit-adjusted). "
    f"Auto-refreshes every 5 minutes. Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
)
