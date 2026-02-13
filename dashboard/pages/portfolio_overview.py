#!/usr/bin/env python3
"""Business Unit: dashboard | Status: current.

Portfolio Overview page with enhanced metrics and per-symbol performance.

Data is read from a DynamoDB single-table populated every 6 hours by the
account_data Lambda.  The dashboard never calls Alpaca directly.
"""

from __future__ import annotations

import _setup_imports  # noqa: F401
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import streamlit.components.v1 as components

from components.ui import (
    hero_metric,
    metric_card,
    metric_row,
    section_header,
    styled_dataframe,
)
from components.styles import format_currency, format_percent, inject_styles

from data import account as data_access
from data import strategy as strategy_data


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_pnl_data() -> pd.DataFrame:
    """Load P&L data from DynamoDB (pre-computed by account_data Lambda)."""
    daily_records = data_access.get_all_pnl_records()

    # Filter to active trading days only (equity > 0)
    active_records = [r for r in daily_records if r.equity > 0]

    if not active_records:
        return pd.DataFrame()

    # Convert to DataFrame
    rows = []
    for rec in active_records:
        rows.append(
            {
                "Date": pd.to_datetime(rec.date),
                "Equity": float(rec.equity),
                "P&L ($)": float(rec.profit_loss),
                "P&L (%)": float(rec.profit_loss_pct),
                "Deposits": float(rec.deposit) if rec.deposit else 0.0,
                "Withdrawals": float(rec.withdrawal) if rec.withdrawal else 0.0,
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values("Date").reset_index(drop=True)

    # Calculate cumulative columns
    df["Cumulative P&L"] = df["P&L ($)"].cumsum()
    df["Cumulative Deposits"] = df["Deposits"].cumsum()

    # Time-Weighted Return (TWR): compound daily returns to get true trading performance
    # This removes the effect of deposit timing - shows actual trading skill
    # Formula: TWR = (1 + r1) * (1 + r2) * ... * (1 + rn) - 1
    daily_returns_decimal = df["P&L (%)"] / 100  # Convert % to decimal
    df["Cumulative Return (%)"] = (((1 + daily_returns_decimal).cumprod() - 1) * 100).round(2)

    return df


@st.cache_data(ttl=300)  # Cache for 5 minutes (data refreshed by Lambda every 6h)
def load_account_snapshot() -> dict[str, float]:
    """Load latest account snapshot from DynamoDB.

    Returns:
        Dictionary with keys: current_equity, last_equity, today_pnl, today_pct

    """
    try:
        account_dict = data_access.get_latest_account_data()
        if not account_dict:
            return {}

        # Extract equity values
        current_equity = float(account_dict.get("equity", 0))
        last_equity = float(account_dict.get("last_equity", 0))

        # Calculate today's P&L
        today_pnl = current_equity - last_equity
        today_pct = (today_pnl / last_equity * 100) if last_equity > 0 else 0.0

        return {
            "current_equity": current_equity,
            "last_equity": last_equity,
            "today_pnl": today_pnl,
            "today_pct": today_pct,
        }
    except Exception as e:
        st.error(f"Error loading account snapshot: {e}")
        return {}


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_positions() -> pd.DataFrame:
    """Load current positions from DynamoDB."""
    try:
        positions = data_access.get_latest_positions()

        if not positions:
            return pd.DataFrame()

        rows = []
        for pos in positions:
            rows.append(
                {
                    "Symbol": pos.symbol,
                    "Qty": float(pos.qty),
                    "Avg Entry": f"${float(pos.avg_entry_price):.2f}",
                    "Current Price": f"${float(pos.current_price):.2f}",
                    "Market Value": float(pos.market_value),
                    "Cost Basis": float(pos.cost_basis),
                    "Unrealized P&L": float(pos.unrealized_pl),
                    "Unrealized P&L %": float(pos.unrealized_plpc) * 100,
                }
            )

        return pd.DataFrame(rows).sort_values("Market Value", ascending=False)
    except Exception as e:
        st.error(f"Error loading positions: {e}")
        return pd.DataFrame()


def calculate_period_metrics(df: pd.DataFrame, months: int) -> dict[str, float] | None:
    """Calculate performance metrics for a specific period.

    Args:
        df: DataFrame with Date, P&L ($), P&L (%) columns
        months: Number of months to look back (1, 3, or 6)

    Returns:
        Dict with period_pnl, period_return, annualized_return or None if insufficient data

    """
    if df.empty:
        return None

    last_date = df["Date"].iloc[-1]
    cutoff_date = last_date - pd.DateOffset(months=months)

    period_df = df[df["Date"] > cutoff_date]

    if period_df.empty or len(period_df) < 2:
        return None

    # Total P&L for the period
    period_pnl = period_df["P&L ($)"].sum()

    # TWR for the period (compound daily returns)
    daily_returns_decimal = period_df["P&L (%)"] / 100
    period_twr = ((1 + daily_returns_decimal).prod() - 1) * 100

    # Annualize the return
    days_in_period = (period_df["Date"].iloc[-1] - period_df["Date"].iloc[0]).days
    if days_in_period > 0:
        years = days_in_period / 365.25
        twr_decimal = period_twr / 100
        if twr_decimal > -1:  # Avoid math errors with extreme losses
            annualized = ((1 + twr_decimal) ** (1 / years) - 1) * 100
        else:
            annualized = -100.0
    else:
        annualized = 0.0

    return {
        "period_pnl": period_pnl,
        "period_return": period_twr,
        "annualized_return": annualized,
        "trading_days": len(period_df),
    }


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
        metrics["Sharpe Ratio"] = (avg_return / std_return) * (252**0.5)
    else:
        metrics["Sharpe Ratio"] = 0.0

    # Max Drawdown
    cumulative_returns = (1 + daily_returns).cumprod()
    running_max = pd.Series(cumulative_returns).expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    metrics["Max Drawdown"] = drawdown.min() * 100  # Convert to percentage

    # Volatility (annualized)
    metrics["Volatility"] = std_return * (252**0.5) * 100  # Convert to percentage

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
    # Inject styles for this page
    inject_styles()

    st.title("Portfolio Overview")
    st.caption("Comprehensive portfolio analytics and performance metrics")

    # Load data
    try:
        df = load_pnl_data()
        if df.empty:
            st.error("No trading data available from account data store.")
            return
    except Exception as e:
        st.error(f"Failed to load data from DynamoDB account data table: {e}")
        return

    # Load account snapshot for current equity and today's P&L
    snapshot = load_account_snapshot()

    # Calculate key metrics
    # Use snapshot equity if available, fallback to historical
    current_equity = snapshot.get("current_equity", df["Equity"].iloc[-1])
    total_pnl = df["Cumulative P&L"].iloc[-1]
    total_return = df["Cumulative Return (%)"].iloc[-1]  # This is TWR
    total_deposits = df["Deposits"].sum()

    # Use snapshot today's P&L if available, fallback to historical
    if snapshot:
        today_pnl = snapshot.get("today_pnl", df["P&L ($)"].iloc[-1])
        today_pct = snapshot.get("today_pct", df["P&L (%)"].iloc[-1])
    else:
        today_pnl = df["P&L ($)"].iloc[-1]
        today_pct = df["P&L (%)"].iloc[-1]

    # Calculate annualized TWR (CAGR) for forward projection
    first_date = df["Date"].iloc[0]
    last_date = df["Date"].iloc[-1]
    years = (last_date - first_date).days / 365.25

    if years > 0:
        twr_decimal = total_return / 100
        annualized_return = ((1 + twr_decimal) ** (1 / years) - 1) * 100
    else:
        annualized_return = 0.0

    # =========================================================================
    # HERO METRIC: Current Equity
    # =========================================================================
    hero_metric(
        label="Current Equity",
        value=format_currency(current_equity),
        subtitle=f"Total Deposits: {format_currency(total_deposits)}",
    )

    # =========================================================================
    # KEY METRICS ROW (3 columns)
    # =========================================================================
    metric_row(
        [
            {
                "label": "Total P&L",
                "value": format_currency(total_pnl, include_sign=True),
                "delta": format_percent(total_return, include_sign=True),
                "delta_positive": total_pnl > 0,
                "accent": True,
            },
            {
                "label": "Today's P&L",
                "value": format_currency(today_pnl, include_sign=True),
                "delta": format_percent(today_pct, include_sign=True),
                "delta_positive": today_pnl > 0,
            },
            {
                "label": "Annualized Return",
                "value": format_percent(annualized_return, include_sign=True),
                "delta_positive": annualized_return > 0,
            },
        ]
    )

    # =========================================================================
    # PERIOD PERFORMANCE (1M, 3M, 6M)
    # =========================================================================
    section_header("Period Performance")

    period_configs = [
        (1, "1 Month"),
        (3, "3 Month"),
        (6, "6 Month"),
    ]

    period_metrics_list = []
    for months, label in period_configs:
        metrics = calculate_period_metrics(df, months)
        if metrics:
            period_metrics_list.append(
                {
                    "label": label,
                    "value": format_currency(metrics["period_pnl"], include_sign=True),
                    "delta": f"{format_percent(metrics['period_return'], include_sign=True)} ({format_percent(metrics['annualized_return'], include_sign=True)} ann.)",
                    "delta_positive": metrics["period_pnl"] > 0,
                }
            )
        else:
            period_metrics_list.append(
                {
                    "label": label,
                    "value": "N/A",
                    "delta": "Insufficient data",
                    "delta_positive": True,
                }
            )

    metric_row(period_metrics_list)

    # =========================================================================
    # RISK METRICS
    # =========================================================================
    risk_metrics = calculate_risk_metrics(df)

    if risk_metrics:
        section_header("Risk Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            sharpe = risk_metrics.get("Sharpe Ratio", 0.0)
            metric_card("Sharpe Ratio", f"{sharpe:.2f}")
        with col2:
            max_dd = risk_metrics.get("Max Drawdown", 0.0)
            metric_card("Max Drawdown", f"{max_dd:.2f}%")
        with col3:
            vol = risk_metrics.get("Volatility", 0.0)
            metric_card("Volatility (Ann.)", f"{vol:.2f}%")
        with col4:
            win_rate = risk_metrics.get("Win Rate", 0.0)
            metric_card("Win Rate", f"{win_rate:.1f}%")
        with col5:
            avg_win = risk_metrics.get("Avg Win", 0.0)
            avg_loss = risk_metrics.get("Avg Loss", 0.0)
            metric_card("Avg Win / Loss", f"{avg_win:.2f}% / {avg_loss:.2f}%")

    # =========================================================================
    # TWO-COLUMN LAYOUT: Equity Curve (60%) + Positions (40%)
    # =========================================================================
    section_header("Performance & Positions")

    col_chart, col_positions = st.columns([6, 4])

    with col_chart:
        st.subheader("Equity Curve")
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Equity"],
                mode="lines",
                name="Equity",
                line=dict(color="#7CF5D4", width=2),
                hovertemplate="Date: %{x|%b %d, %Y}<br>Equity: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title=""),
            yaxis=dict(title="", tickformat="$,.0f"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_positions:
        st.subheader("Current Positions")
        positions_df = load_positions()

        if not positions_df.empty:
            # Compact display for sidebar
            display_df = positions_df[
                ["Symbol", "Qty", "Unrealized P&L", "Unrealized P&L %"]
            ].copy()
            styled_dataframe(
                display_df,
                formats={
                    "Unrealized P&L": "${:+,.2f}",
                    "Unrealized P&L %": "{:+.2f}%",
                },
                highlight_positive_negative=["Unrealized P&L", "Unrealized P&L %"],
                height=300,
            )

            # Summary stats
            total_market_value = positions_df["Market Value"].sum()
            total_unrealized_pl = positions_df["Unrealized P&L"].sum()
            st.caption(
                f"**Total Value:** {format_currency(total_market_value)} | "
                f"**Unrealized P&L:** {format_currency(total_unrealized_pl, include_sign=True)}"
            )
        else:
            st.info("No open positions")

    # =========================================================================
    # DAILY P&L BAR CHART (full width)
    # =========================================================================
    section_header("Daily P&L")
    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in df["P&L ($)"]]
    fig_pnl = go.Figure()
    fig_pnl.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["P&L ($)"],
            marker_color=colors,
            hovertemplate="Date: %{x|%b %d, %Y}<br>P&L: $%{y:+,.2f}<extra></extra>",
        )
    )
    fig_pnl.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(title=""),
        yaxis=dict(title="", tickformat="$,.0f"),
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(fig_pnl, use_container_width=True)

    # =========================================================================
    # CUMULATIVE P&L CHART (full width)
    # =========================================================================
    section_header("Cumulative P&L")
    cum_color = "#4CAF50" if df["Cumulative P&L"].iloc[-1] >= 0 else "#F44336"
    fig_cum = go.Figure()
    fig_cum.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Cumulative P&L"],
            mode="lines",
            fill="tozeroy",
            line=dict(color=cum_color, width=2),
            hovertemplate="Date: %{x|%b %d, %Y}<br>Cumulative P&L: $%{y:+,.0f}<extra></extra>",
        )
    )
    fig_cum.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(title=""),
        yaxis=dict(title="", tickformat="$,.0f"),
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(fig_cum, use_container_width=True)

    # =========================================================================
    # TEARSHEETS (collapsible)
    # =========================================================================
    with st.expander("Tearsheets", expanded=False):
        available = strategy_data.get_available_tearsheets()
        if not available:
            st.info(
                "No tearsheets found in S3. Generate with:\n\n"
                "```\npython scripts/generate_tearsheets.py --stage prod\n"
                "python scripts/generate_tearsheets.py --stage prod --account\n```"
            )
        else:
            has_account = "_account" in available
            strategy_names = [n for n in available if n != "_account"]

            mode_options: list[str] = []
            if has_account:
                mode_options.append("Account")
            if strategy_names:
                mode_options.append("Strategy")

            selected_name: str | None = None
            if len(mode_options) > 1:
                mode = st.radio("Tearsheet type", mode_options, horizontal=True)
            elif mode_options:
                mode = mode_options[0]
            else:
                mode = None

            if mode == "Account":
                selected_name = "_account"
            elif mode == "Strategy" and strategy_names:
                metadata = strategy_data.get_all_strategy_metadata()
                display_map = {
                    name: metadata.get(name, {}).get("display_name", name)
                    for name in strategy_names
                }
                selected_name = st.selectbox(
                    "Select strategy",
                    options=strategy_names,
                    format_func=lambda x: display_map.get(x, x),
                )

            if selected_name:
                with st.spinner("Loading tearsheet..."):
                    html = strategy_data.get_tearsheet_html(selected_name)
                if html:
                    components.html(html, height=800, scrolling=True)
                else:
                    st.warning(f"No tearsheet found for '{selected_name}'.")

    # =========================================================================
    # DAILY PnL TABLE (collapsible)
    # =========================================================================
    with st.expander("Daily PnL Table", expanded=False):
        pnl_table_df = df[["Date", "Equity", "P&L ($)", "P&L (%)", "Deposits"]].copy()
        pnl_table_df = pnl_table_df.sort_values("Date", ascending=False).reset_index(drop=True)
        st.dataframe(
            pnl_table_df,
            width="stretch",
            height=500,
            column_config={
                "Date": st.column_config.DateColumn("Date"),
                "Equity": st.column_config.NumberColumn("Equity", format="$%.2f"),
                "P&L ($)": st.column_config.NumberColumn("P&L ($)", format="$%.2f"),
                "P&L (%)": st.column_config.NumberColumn("P&L (%)", format="%.4f%%"),
                "Deposits": st.column_config.NumberColumn("Deposits", format="$%.2f"),
            },
        )
        csv = pnl_table_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="daily_pnl_records.csv",
            mime="text/csv",
        )

    # =========================================================================
    # MONTHLY SUMMARY (collapsible)
    # =========================================================================
    with st.expander("Monthly Summary", expanded=False):
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
        monthly = (
            df.groupby("Month")
            .agg(
                {
                    "P&L ($)": "sum",
                    "Equity": "last",
                    "Deposits": "sum",
                }
            )
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
                monthly.loc[month, "Return %"] = monthly.loc[month, "P&L ($)"] / start_equity * 100

        styled_dataframe(
            monthly.reset_index(),
            formats={
                "P&L ($)": "${:+,.2f}",
                "End Equity": "${:,.2f}",
                "Deposits": "${:,.2f}",
                "Return %": "{:+.2f}%",
            },
            highlight_positive_negative=["P&L ($)", "Return %"],
        )

    # =========================================================================
    # FULL POSITIONS TABLE (collapsible)
    # =========================================================================
    if not positions_df.empty:
        with st.expander("Full Position Details", expanded=False):
            styled_dataframe(
                positions_df,
                formats={
                    "Market Value": "${:,.2f}",
                    "Cost Basis": "${:,.2f}",
                    "Unrealized P&L": "${:+,.2f}",
                    "Unrealized P&L %": "{:+.2f}%",
                },
                highlight_positive_negative=["Unrealized P&L", "Unrealized P&L %"],
            )

    # =========================================================================
    # RAW DATA (collapsible)
    # =========================================================================
    with st.expander("View Raw Data"):
        st.dataframe(df, width="stretch")

    # Footer with data freshness
    last_updated = data_access.get_data_last_updated()
    freshness = f" Last updated: {last_updated}." if last_updated else ""
    st.caption(
        f"Data sourced from DynamoDB (refreshed every 6 hours by account_data Lambda)."
        f"{freshness} Dashboard cache: 5 minutes."
    )
