"""Business Unit: dashboard | Status: current.

Strategy detail tab renderers for the Strategy Performance page.

Each function renders one tab inside the strategy drill-down view.
Extracted from strategy_performance.py to keep modules under the
500-line target.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import strategy as sda
from components.ui import (
    metric_card,
    section_header,
    styled_dataframe,
    direction_styled_dataframe,
)
from components.styles import format_currency

_logger = logging.getLogger(__name__)


def show_time_series_tab(strategy_name: str) -> None:
    """Render cumulative P&L and metrics over time."""
    section_header("Realized P&L Over Time")
    time_series = sda.get_strategy_time_series(strategy_name)

    if len(time_series) < 2:
        st.info(
            "Not enough data points for time-series charts. "
            "Data accumulates with each trade execution."
        )
        return

    df = pd.DataFrame(time_series)
    df["timestamp"] = pd.to_datetime(df["snapshot_timestamp"])
    df = df.sort_values("timestamp")

    # Deduplicate to daily granularity (keep last snapshot per day)
    df["date"] = df["timestamp"].dt.date
    df = df.drop_duplicates(subset="date", keep="last")

    # Cumulative P&L line chart
    final_pnl = df["realized_pnl"].iloc[-1]
    line_color = "#10B981" if final_pnl >= 0 else "#EF4444"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["realized_pnl"],
            mode="lines",
            fill="tozeroy",
            line={"color": line_color, "width": 2},
            fillcolor=("rgba(16, 185, 129, 0.1)" if final_pnl >= 0 else "rgba(239, 68, 68, 0.1)"),
            hovertemplate=("Date: %{x|%b %d, %Y}<br>Realized P&L: $%{y:,.2f}<extra></extra>"),
        )
    )
    fig.update_layout(
        height=350,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        xaxis={"title": ""},
        yaxis={"title": "Realized P&L ($)", "tickformat": "$,.0f"},
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Win rate trend
    if "win_rate" in df.columns:
        section_header("Win Rate Trend")
        fig_wr = go.Figure()
        fig_wr.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["win_rate"],
                mode="lines",
                line={"color": "#7CF5D4", "width": 2},
                hovertemplate=("Date: %{x|%b %d, %Y}<br>Win Rate: %{y:.1f}%<extra></extra>"),
            )
        )
        fig_wr.update_layout(
            height=250,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            xaxis={"title": ""},
            yaxis={"title": "Win Rate (%)", "range": [0, 100]},
            hovermode="x unified",
            showlegend=False,
        )
        st.plotly_chart(fig_wr, use_container_width=True)


def show_risk_metrics_tab(strategy_name: str) -> None:
    """Render risk and return metrics from S3 analytics."""
    section_header("Risk & Return Metrics")
    metrics = sda.get_strategy_metrics(strategy_name)

    if metrics is None or metrics.get("data_points", 0) < 5:
        st.info(
            "Need at least 5 data points for risk metrics. "
            "More trade executions will populate this."
        )
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            "P&L Sharpe",
            f"{metrics.get('pnl_sharpe', 0):.2f}",
            delta_positive=metrics.get("pnl_sharpe", 0) > 0,
        )
    with col2:
        metric_card(
            "Max Drawdown",
            format_currency(metrics.get("max_drawdown", 0)),
        )
    with col3:
        metric_card(
            "Volatility (Ann.)",
            format_currency(metrics.get("annualized_volatility", 0)),
        )
    with col4:
        pf = metrics.get("profit_factor")
        pf_str = f"{pf:.2f}" if pf is not None else "N/A"
        metric_card(
            "Profit Factor",
            pf_str,
            delta_positive=pf is not None and pf > 1.0,
        )

    # Tearsheet link (generated locally via scripts/generate_tearsheets.py)
    tearsheet_url = sda.get_strategy_tearsheet_url(strategy_name)
    if tearsheet_url:
        st.markdown(f"[View Full Tearsheet]({tearsheet_url})")

    # Drawdown chart from time series
    time_series = sda.get_strategy_time_series(strategy_name)
    if len(time_series) < 3:
        return

    pnl_values = [s.get("realized_pnl", 0.0) for s in time_series]
    timestamps = [s["snapshot_timestamp"] for s in time_series]

    drawdowns: list[float] = []
    peak = pnl_values[0]
    for pnl in pnl_values:
        if pnl > peak:
            peak = pnl
        drawdowns.append(pnl - peak)

    if any(not math.isclose(d, 0.0, abs_tol=1e-9) for d in drawdowns):
        section_header("Drawdown Chart")
        fig_dd = go.Figure()
        fig_dd.add_trace(
            go.Scatter(
                x=[pd.to_datetime(t) for t in timestamps],
                y=drawdowns,
                mode="lines",
                fill="tozeroy",
                line={"color": "#EF4444", "width": 1.5},
                fillcolor="rgba(239, 68, 68, 0.15)",
                hovertemplate=("Date: %{x|%b %d, %Y}<br>Drawdown: $%{y:,.2f}<extra></extra>"),
            )
        )
        fig_dd.update_layout(
            height=250,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            xaxis={"title": ""},
            yaxis={"title": "Drawdown ($)", "tickformat": "$,.0f"},
            hovermode="x unified",
            showlegend=False,
        )
        st.plotly_chart(fig_dd, use_container_width=True)


def _render_open_lots(lots: list[dict[str, Any]]) -> None:
    """Render open lots table with unrealized P&L and position pie chart."""
    price_map = sda.get_current_price_map()

    rows = []
    for lot in lots:
        symbol = lot["symbol"]
        entry_price = lot["entry_price"]
        remaining_qty = lot["remaining_qty"]
        cost_basis = lot["cost_basis"]
        current_price = price_map.get(symbol)

        row: dict[str, Any] = {
            "Symbol": symbol,
            "Entry Date": lot["entry_timestamp"][:10] if lot["entry_timestamp"] else "",
            "Entry Price": entry_price,
            "Qty": lot["entry_qty"],
            "Remaining": remaining_qty,
            "Cost Basis": cost_basis,
        }

        if current_price is not None:
            market_value = remaining_qty * current_price
            unrealized = market_value - (remaining_qty * entry_price)
            unrealized_pct = (unrealized / (remaining_qty * entry_price) * 100) if entry_price > 0 else 0.0
            row["Current Price"] = current_price
            row["Market Value"] = market_value
            row["Unrealized P&L"] = unrealized
            row["Unrealized %"] = unrealized_pct

        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return

    df = df.sort_values("Symbol")

    has_prices = "Current Price" in df.columns

    # Book summary metrics
    total_cost = df["Cost Basis"].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Open Lots", str(len(df)))
    with col2:
        metric_card("Total Cost Basis", f"${total_cost:,.2f}")
    if has_prices:
        total_market = df["Market Value"].sum()
        total_unrealized = df["Unrealized P&L"].sum()
        with col3:
            metric_card(
                "Unrealized P&L",
                f"${total_unrealized:+,.2f}",
                delta_positive=total_unrealized > 0,
            )

    formats: dict[str, str] = {
        "Entry Price": "${:.2f}",
        "Qty": "{:.4f}",
        "Remaining": "{:.4f}",
        "Cost Basis": "${:,.2f}",
    }
    highlight_cols: list[str] = []
    if has_prices:
        formats["Current Price"] = "${:.2f}"
        formats["Market Value"] = "${:,.2f}"
        formats["Unrealized P&L"] = "${:+,.2f}"
        formats["Unrealized %"] = "{:+.1f}%"
        highlight_cols = ["Unrealized P&L", "Unrealized %"]

    styled_dataframe(df, formats=formats, highlight_positive_negative=highlight_cols)

    if len(df) <= 1:
        return

    fig_pie = go.Figure()
    pie_values = df["Market Value"] if has_prices else df["Cost Basis"]
    pie_label = "Market Value" if has_prices else "Cost Basis"
    fig_pie.add_trace(
        go.Pie(
            labels=df["Symbol"],
            values=pie_values,
            hole=0.4,
            hovertemplate=(
                f"%{{label}}<br>{pie_label}: $%{{value:,.2f}}<br>%{{percent}}<extra></extra>"
            ),
            marker={
                "colors": [
                    "#7CF5D4",
                    "#10B981",
                    "#34D399",
                    "#6EE7B7",
                    "#A7F3D0",
                    "#059669",
                    "#047857",
                    "#065F46",
                    "#064E3B",
                    "#022C22",
                ]
            },
        )
    )
    fig_pie.update_layout(
        height=300,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
        },
    )
    st.plotly_chart(fig_pie, use_container_width=True)


def _render_closed_lots(lots: list[dict[str, Any]]) -> None:
    """Render closed lots table with P&L distribution histogram."""
    rows = []
    for lot in lots:
        exits = lot.get("exit_records", [])
        if exits:
            total_exit_qty = sum(e["exit_qty"] for e in exits)
            total_exit_value = sum(e["exit_qty"] * e["exit_price"] for e in exits)
            avg_exit = total_exit_value / total_exit_qty if total_exit_qty > 0 else 0.0
        else:
            avg_exit = 0.0

        pnl = lot["realized_pnl"]
        cost_basis = lot["cost_basis"]
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0

        hold_days = _compute_hold_duration(
            lot["entry_timestamp"], lot.get("fully_closed_at", "")
        )

        rows.append(
            {
                "Symbol": lot["symbol"],
                "Entry Date": lot["entry_timestamp"][:10] if lot["entry_timestamp"] else "",
                "Entry Price": lot["entry_price"],
                "Avg Exit": avg_exit,
                "Qty": lot["entry_qty"],
                "P&L": pnl,
                "P&L %": pnl_pct,
                "Hold": hold_days,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return

    df = df.sort_values("Entry Date", ascending=False)
    styled_dataframe(
        df,
        formats={
            "Entry Price": "${:.2f}",
            "Avg Exit": "${:.2f}",
            "Qty": "{:.4f}",
            "P&L": "${:,.2f}",
            "P&L %": "{:+.1f}%",
        },
        highlight_positive_negative=["P&L", "P&L %"],
    )

    section_header("P&L Distribution")
    pnl_vals = df["P&L"].tolist()
    fig_hist = go.Figure()
    fig_hist.add_trace(
        go.Histogram(
            x=pnl_vals,
            nbinsx=20,
            marker_color="#7CF5D4",
            hovertemplate=("Range: $%{x:,.2f}<br>Count: %{y}<extra></extra>"),
        )
    )
    fig_hist.update_layout(
        height=250,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        xaxis={"title": "P&L ($)", "tickformat": "$,.0f"},
        yaxis={"title": "Count"},
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)


def _compute_hold_duration(entry_ts: str, closed_ts: str) -> str:
    """Compute hold duration string from entry and close timestamps."""
    if not entry_ts or not closed_ts:
        return ""
    try:
        entry_dt = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
        close_dt = datetime.fromisoformat(closed_ts.replace("Z", "+00:00"))
        delta = close_dt - entry_dt
        return f"{delta.days}d"
    except (ValueError, TypeError):
        _logger.warning(
            "Malformed lot timestamps: entry=%s closed=%s", entry_ts, closed_ts
        )
        return ""


def show_lots_tab(strategy_name: str, lot_type: str) -> None:
    """Render open or closed lots table."""
    section_header(f"{'Open' if lot_type == 'open' else 'Closed'} Lots")

    lots_data = sda.get_strategy_lots(strategy_name)
    lots = lots_data.get(lot_type, [])

    if not lots:
        st.info(f"No {lot_type} lots found for this strategy.")
        return

    if lot_type == "open":
        _render_open_lots(lots)
    else:
        _render_closed_lots(lots)


def show_trades_tab(strategy_name: str) -> None:
    """Render individual trades attributed to this strategy."""
    section_header("Trade History")

    trades = sda.get_strategy_trades(strategy_name)

    if not trades:
        st.info("No trade history found for this strategy.")
        return

    rows = []
    for t in trades:
        rows.append(
            {
                "Date": t["fill_timestamp"][:10] if t["fill_timestamp"] else "",
                "Time": t["fill_timestamp"][11:19] if len(t["fill_timestamp"]) > 19 else "",
                "Symbol": t["symbol"],
                "Direction": t["direction"],
                "Qty": t["quantity"],
                "Price": t["price"],
                "Value": t["strategy_trade_value"],
                "Weight": t["weight"],
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Date", ascending=False)
        direction_styled_dataframe(
            df,
            formats={
                "Qty": "{:.4f}",
                "Price": "${:.2f}",
                "Value": "${:,.2f}",
                "Weight": "{:.1%}",
            },
        )

        # Trade value over time
        if len(df) > 1:
            section_header("Trade Values Over Time")
            df_chart = df.copy()
            df_chart["Timestamp"] = pd.to_datetime(
                df_chart["Date"] + " " + df_chart["Time"], errors="coerce"
            )
            df_chart = df_chart.dropna(subset=["Timestamp"]).sort_values("Timestamp")

            buy_df = df_chart[df_chart["Direction"] == "BUY"]
            sell_df = df_chart[df_chart["Direction"] == "SELL"]

            fig_tv = go.Figure()
            if not buy_df.empty:
                fig_tv.add_trace(
                    go.Scatter(
                        x=buy_df["Timestamp"],
                        y=buy_df["Value"],
                        mode="markers",
                        name="BUY",
                        marker={"color": "#4CAF50", "size": 8},
                        hovertemplate=("%{x|%b %d}<br>Value: $%{y:,.2f}<extra>BUY</extra>"),
                    )
                )
            if not sell_df.empty:
                fig_tv.add_trace(
                    go.Scatter(
                        x=sell_df["Timestamp"],
                        y=sell_df["Value"],
                        mode="markers",
                        name="SELL",
                        marker={"color": "#F44336", "size": 8},
                        hovertemplate=("%{x|%b %d}<br>Value: $%{y:,.2f}<extra>SELL</extra>"),
                    )
                )
            fig_tv.update_layout(
                height=300,
                margin={"l": 0, "r": 0, "t": 10, "b": 0},
                xaxis={"title": ""},
                yaxis={"title": "Trade Value ($)", "tickformat": "$,.0f"},
                hovermode="closest",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                },
            )
            st.plotly_chart(fig_tv, use_container_width=True)


def show_assets_tab(
    strategy_name: str,
    assets: list[str],
    frontrunners: list[str],
) -> None:
    """Render asset composition from strategy ledger metadata."""
    section_header("Asset Composition")

    if not assets and not frontrunners:
        st.info(
            "No asset metadata available. Run 'python scripts/strategy_ledger.py sync' to populate."
        )
        return

    col1, col2 = st.columns(2)
    with col1:
        metric_card("Traded Assets", str(len(assets)))
        if assets:
            st.markdown("  ".join(f"`{a}`" for a in sorted(assets)))
    with col2:
        metric_card("Indicator-Only (Frontrunners)", str(len(frontrunners)))
        if frontrunners:
            st.markdown("  ".join(f"`{f}`" for f in sorted(frontrunners)))
