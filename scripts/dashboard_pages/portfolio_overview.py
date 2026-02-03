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

from alpaca.trading.client import TradingClient

from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
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
    df["Cumulative Deposits"] = df["Deposits"].cumsum()

    # Time-Weighted Return (TWR): compound daily returns to get true trading performance
    # This removes the effect of deposit timing - shows actual trading skill
    # Formula: TWR = (1 + r1) × (1 + r2) × ... × (1 + rn) - 1
    daily_returns_decimal = df["P&L (%)"] / 100  # Convert % to decimal
    df["Cumulative Return (%)"] = (
        ((1 + daily_returns_decimal).cumprod() - 1) * 100
    ).round(2)

    return df


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_positions() -> pd.DataFrame:
    """Load current positions from Alpaca."""
    try:
        api_key, secret_key, endpoint = get_alpaca_keys()
        if not api_key or not secret_key:
            st.error("Alpaca API keys not configured")
            return pd.DataFrame()
        
        # Determine if paper trading based on endpoint
        paper = endpoint and "paper" in endpoint.lower() if endpoint else True
        trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
        account_service = AlpacaAccountService(trading_client)
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
                "Avg Entry": f"${float(pos.avg_entry_price):.2f}" if pos.avg_entry_price else "N/A",
                "Current Price": f"${float(pos.current_price):.2f}" if pos.current_price else "N/A",
                "Market Value": market_value,
                "Cost Basis": cost_basis,
                "Unrealized P&L": unrealized_pl,
                "Unrealized P&L %": unrealized_plpc * 100,
            })

        return pd.DataFrame(rows).sort_values("Market Value", ascending=False)
    except Exception as e:
        st.error(f"Error loading positions: {e}")
        return pd.DataFrame()


def calculate_risk_metrics(df: pd.DataFrame) -> dict[str, float]:
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
    st.title("Portfolio Overview")
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
    st.subheader("Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    current_equity = df["Equity"].iloc[-1]
    total_pnl = df["Cumulative P&L"].iloc[-1]
    total_return = df["Cumulative Return (%)"].iloc[-1]  # This is TWR
    total_deposits = df["Deposits"].sum()
    today_pnl = df["P&L ($)"].iloc[-1]
    today_pct = df["P&L (%)"].iloc[-1]
    
    # Calculate annualized TWR (CAGR) for forward projection
    # Uses time-weighted return which removes deposit timing effects
    # Formula: (1 + TWR)^(1/years) - 1
    first_date = df["Date"].iloc[0]
    last_date = df["Date"].iloc[-1]
    years = (last_date - first_date).days / 365.25
    
    if years > 0:
        twr_decimal = total_return / 100  # Convert TWR from % to decimal
        # Annualize the TWR - this is the proper forward projection metric
        annualized_return = ((1 + twr_decimal) ** (1 / years) - 1) * 100
    else:
        annualized_return = 0.0

    with col1:
        st.metric("Current Equity", f"${current_equity:,.2f}")
    with col2:
        st.metric("Total P&L", f"${total_pnl:+,.2f}", delta=f"{total_return:+.2f}%")
    with col3:
        st.metric("Total Deposits", f"${total_deposits:,.2f}")
    with col4:
        st.metric("Latest Day P&L", f"${today_pnl:+,.2f}", delta=f"{today_pct:+.2f}%")
    with col5:
        st.metric("Ann. Return", f"{annualized_return:+.2f}%")

    st.divider()

    # Risk metrics row
    st.subheader("Risk Metrics")
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
    st.subheader("Current Positions")
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
            width="stretch",
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
        width="stretch",
    )

    st.divider()

    # Raw data (expandable)
    with st.expander("View Raw Data"):
        st.dataframe(df, width="stretch")

    # Footer
    st.caption(
        f"Data from Alpaca API (deposit-adjusted). "
        f"Cache refreshes every 5 minutes."
    )
