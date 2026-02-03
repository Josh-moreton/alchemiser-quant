#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Portfolio Overview page with enhanced metrics and per-symbol performance.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import _setup_imports  # noqa: F401
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from the_alchemiser.shared.services.alpaca_account_service import AlpacaAccountService
from the_alchemiser.shared.services.pnl_service import PnLService


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_pnl_data() -> pd.DataFrame:
    """Load P&L data from Alpaca API with deposit adjustments."""
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


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_positions() -> pd.DataFrame:
    """Load current positions from Alpaca."""
    try:
        account_service = AlpacaAccountService()
        positions = account_service.get_positions()

        if not positions:
            return pd.DataFrame()

        rows = []
        for pos in positions:
            market_value = float(pos.market_value) if pos.market_value else 0.0
            cost_basis = float(pos.cost_basis) if pos.cost_basis else 0.0
            unrealized_pl = float(pos.unrealized_pl) if pos.unrealized_pl else 0.0
            unrealized_plpc = float(pos.unrealized_plpc) if pos.unrealized_plpc else 0.0

            rows.append({
                "Symbol": pos.symbol,
                "Qty": float(pos.qty),
                "Avg Entry": f"${pos.avg_entry_price:.2f}" if pos.avg_entry_price else "N/A",
                "Current Price": f"${pos.current_price:.2f}" if pos.current_price else "N/A",
                "Market Value": market_value,
                "Cost Basis": cost_basis,
                "Unrealized P&L": unrealized_pl,
                "Unrealized P&L %": unrealized_plpc * 100,
            })

        return pd.DataFrame(rows).sort_values("Market Value", ascending=False)
    except Exception as e:
        st.error(f"Error loading positions: {e}")
        return pd.DataFrame()


def calculate_risk_metrics(df: pd.DataFrame) -> dict:
    """Calculate portfolio risk metrics."""
    if df.empty or len(df) < 2:
        return {}

    daily_returns = df["P&L (%)"].values / 100.0  # Convert to decimal

    # Calculate metrics
    metrics = {}

    # Sharpe Ratio (annualized, assuming 252 trading days)
    avg_return = daily_returns.mean()
    std_return = daily_returns.std()
    if std_return > 0:
        metrics["Sharpe Ratio"] = (avg_return / std_return) * (252 ** 0.5)
    else:
        metrics["Sharpe Ratio"] = 0.0

    # Max Drawdown
    cumulative_returns = (1 + daily_returns).cumprod()
    running_max = pd.Series(cumulative_returns).expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    metrics["Max Drawdown"] = drawdown.min() * 100  # Convert to percentage

    # Volatility (annualized)
    metrics["Volatility"] = std_return * (252 ** 0.5) * 100  # Convert to percentage

    # Win rate
    winning_days = (daily_returns > 0).sum()
    total_days = len(daily_returns)
    metrics["Win Rate"] = (winning_days / total_days * 100) if total_days > 0 else 0.0

    # Average win/loss
    wins = daily_returns[daily_returns > 0]
    losses = daily_returns[daily_returns < 0]
    metrics["Avg Win"] = wins.mean() * 100 if len(wins) > 0 else 0.0
    metrics["Avg Loss"] = losses.mean() * 100 if len(losses) > 0 else 0.0

    return metrics


def show() -> None:
    """Display the portfolio overview page."""
    st.title("📈 Portfolio Overview")
    st.caption("Comprehensive portfolio analytics and performance metrics")

    # Load data
    try:
        df = load_pnl_data()
        if df.empty:
            st.error("No trading data available from Alpaca.")
            return
    except Exception as e:
        st.error(f"Failed to load data from Alpaca: {e}")
        return

    # Key metrics row
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    current_equity = df["Equity"].iloc[-1]
    total_pnl = df["Cumulative P&L"].iloc[-1]
    total_return = df["Cumulative Return (%)"].iloc[-1]
    total_deposits = df["Deposits"].sum()
    today_pnl = df["P&L ($)"].iloc[-1]
    today_pct = df["P&L (%)"].iloc[-1]

    with col1:
        st.metric("Current Equity", f"${current_equity:,.2f}")
    with col2:
        st.metric("Total P&L", f"${total_pnl:+,.2f}", delta=f"{total_return:+.2f}%")
    with col3:
        st.metric("Total Deposits", f"${total_deposits:,.2f}")
    with col4:
        st.metric("Latest Day P&L", f"${today_pnl:+,.2f}", delta=f"{today_pct:+.2f}%")
    with col5:
        # Calculate total trading days
        st.metric("Trading Days", len(df))

    st.divider()

    # Risk metrics row
    st.subheader("🎯 Risk Metrics")
    risk_metrics = calculate_risk_metrics(df)

    if risk_metrics:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            sharpe = risk_metrics.get("Sharpe Ratio", 0.0)
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
        with col2:
            max_dd = risk_metrics.get("Max Drawdown", 0.0)
            st.metric("Max Drawdown", f"{max_dd:.2f}%")
        with col3:
            vol = risk_metrics.get("Volatility", 0.0)
            st.metric("Volatility (Ann.)", f"{vol:.2f}%")
        with col4:
            win_rate = risk_metrics.get("Win Rate", 0.0)
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col5:
            avg_win = risk_metrics.get("Avg Win", 0.0)
            avg_loss = risk_metrics.get("Avg Loss", 0.0)
            st.metric("Avg Win", f"{avg_win:.2f}%")
            st.caption(f"Avg Loss: {avg_loss:.2f}%")

    st.divider()

    # Current Positions
    st.subheader("💼 Current Positions")
    positions_df = load_positions()

    if not positions_df.empty:
        # Format currency columns
        st.dataframe(
            positions_df.style.format({
                "Market Value": "${:,.2f}",
                "Cost Basis": "${:,.2f}",
                "Unrealized P&L": "${:+,.2f}",
                "Unrealized P&L %": "{:+.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Summary stats
        total_market_value = positions_df["Market Value"].sum()
        total_unrealized_pl = positions_df["Unrealized P&L"].sum()
        st.caption(
            f"**Total Market Value:** ${total_market_value:,.2f} | "
            f"**Total Unrealized P&L:** ${total_unrealized_pl:+,.2f}"
        )
    else:
        st.info("No open positions")

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
    st.subheader("📅 Monthly Summary")
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

    # Add return % column
    monthly["Return %"] = 0.0
    for i, month in enumerate(monthly.index):
        if i == 0:
            start_equity = df.iloc[0]["Equity"] - df.iloc[0]["P&L ($)"]
        else:
            prev_month = monthly.index[i - 1]
            start_equity = monthly.loc[prev_month, "End Equity"]

        if start_equity > 0:
            monthly.loc[month, "Return %"] = (monthly.loc[month, "P&L ($)"] / start_equity * 100)

    st.dataframe(
        monthly.style.format({
            "P&L ($)": "${:+,.2f}",
            "End Equity": "${:,.2f}",
            "Deposits": "${:,.2f}",
            "Return %": "{:+.2f}%",
        }),
        use_container_width=True,
    )

    st.divider()

    # Raw data (expandable)
    with st.expander("📊 View Raw Data"):
        st.dataframe(df, use_container_width=True)

    # Footer
    st.caption(
        f"Data from Alpaca API (deposit-adjusted). "
        f"Cache refreshes every 5 minutes."
    )
