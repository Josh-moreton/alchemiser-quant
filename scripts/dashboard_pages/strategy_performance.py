"""Business Unit: scripts | Status: current.

Strategy Performance page -- per-strategy analytics with lot-level detail.

Dual data source architecture:
- StrategyPerformanceTable for fast summary KPIs and time-series charts
- TradeLedger for lot-level drill-down (open/closed lots, trade history)
- Strategy ledger metadata for enrichment (display names, source URLs, assets)

Sections:
A. Summary grid -- all strategies at a glance
B. Data quality -- attribution coverage audit
C. Strategy drill-down -- individual strategy detail with tabs
D. Strategy comparison -- overlay multiple strategies
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dashboard_settings import get_dashboard_settings

from . import strategy_data_access as sda
from .components import (
    alert_box,
    direction_styled_dataframe,
    hero_metric,
    metric_card,
    metric_row,
    progress_bar,
    section_header,
    styled_dataframe,
)
from .styles import (
    format_currency,
    format_percent,
    inject_styles,
)

# ---------------------------------------------------------------------------
# Risk metrics calculations (adapted from portfolio_overview)
# ---------------------------------------------------------------------------


def _calculate_risk_metrics(
    time_series: list[dict[str, Any]],
) -> dict[str, float]:
    """Calculate risk metrics from strategy performance time series.

    Uses daily changes in realized_pnl as the return proxy.

    Returns dict with sharpe, max_drawdown, volatility, profit_factor.
    """
    if len(time_series) < 3:
        return {
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "volatility": 0.0,
            "profit_factor": 0.0,
        }

    pnl_values = [s["realized_pnl"] for s in time_series]

    # Daily changes in realized P&L (returns proxy)
    daily_changes = [pnl_values[i] - pnl_values[i - 1] for i in range(1, len(pnl_values))]

    if not daily_changes:
        return {
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "volatility": 0.0,
            "profit_factor": 0.0,
        }

    # -- Sharpe ratio (annualized, risk-free = 0)
    import math

    avg_change = sum(daily_changes) / len(daily_changes)
    variance = sum((c - avg_change) ** 2 for c in daily_changes) / max(len(daily_changes) - 1, 1)
    std_change = math.sqrt(variance)
    sharpe = (avg_change / std_change) * math.sqrt(252) if std_change > 0 else 0.0

    # -- Max drawdown (peak-to-trough in cumulative P&L)
    running_max = pnl_values[0]
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    for pnl in pnl_values:
        if pnl > running_max:
            running_max = pnl
        drawdown = running_max - pnl
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            if not math.isclose(running_max, 0.0, abs_tol=1e-9):
                max_drawdown_pct = (drawdown / abs(running_max)) * 100

    # -- Volatility (annualized std of daily P&L changes)
    volatility = std_change * math.sqrt(252)

    # -- Profit factor (sum of gains / sum of losses)
    gross_wins = sum(c for c in daily_changes if c > 0)
    gross_losses = abs(sum(c for c in daily_changes if c < 0))
    profit_factor = (
        gross_wins / gross_losses
        if not math.isclose(gross_losses, 0.0, abs_tol=1e-9)
        else float("inf")
        if gross_wins > 0
        else 0.0
    )

    return {
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown_pct,
        "volatility": volatility,
        "profit_factor": profit_factor,
    }


# ---------------------------------------------------------------------------
# Section A: Summary Grid
# ---------------------------------------------------------------------------


def _show_summary_grid(
    snapshots: list[dict[str, Any]],
    metadata: dict[str, dict[str, Any]],
) -> None:
    """Render the all-strategies summary grid."""
    section_header("All Strategies Overview")

    if not snapshots:
        st.info(
            "No strategy performance data available yet. "
            "Data is populated after each trade execution."
        )
        return

    # Aggregate KPIs
    total_pnl = sum(s["realized_pnl"] for s in snapshots)
    total_trades = sum(s["completed_trades"] for s in snapshots)
    total_wins = sum(s["winning_trades"] for s in snapshots)
    total_holdings = sum(s["current_holdings"] for s in snapshots)
    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0.0

    hero_metric(
        label="Total Realized P&L (All Strategies)",
        value=format_currency(total_pnl, include_sign=True),
        subtitle=(
            f"{len(snapshots)} active strategies | "
            f"{total_trades} completed trades | "
            f"{total_holdings} open lots"
        ),
    )

    capital_deployed = sda.get_capital_deployed()
    metric_row(
        [
            {
                "label": "Active Strategies",
                "value": str(len(snapshots)),
            },
            {
                "label": "Overall Win Rate",
                "value": format_percent(overall_win_rate),
            },
            {
                "label": "Total Trades",
                "value": str(total_trades),
            },
            {
                "label": "Capital Deployed",
                "value": (format_percent(capital_deployed) if capital_deployed else "N/A"),
            },
        ]
    )

    # Build summary DataFrame
    rows = []
    for snap in snapshots:
        name = snap["strategy_name"]
        meta = metadata.get(name, {})
        display = meta.get("display_name", name)
        rows.append(
            {
                "Strategy": display,
                "Realized P&L": snap["realized_pnl"],
                "Win Rate (%)": snap["win_rate"],
                "Trades": snap["completed_trades"],
                "Open Lots": snap["current_holdings"],
                "Holdings Value": snap["current_holdings_value"],
                "Avg Profit": snap["avg_profit_per_trade"],
            }
        )

    df = pd.DataFrame(rows).sort_values("Realized P&L", ascending=False)

    styled_dataframe(
        df,
        formats={
            "Realized P&L": "${:,.2f}",
            "Win Rate (%)": "{:.1f}%",
            "Holdings Value": "${:,.2f}",
            "Avg Profit": "${:,.2f}",
        },
        highlight_positive_negative=["Realized P&L", "Avg Profit"],
    )

    # Horizontal bar chart: P&L by strategy
    st.markdown("")
    colors_list = ["#10B981" if v >= 0 else "#EF4444" for v in df["Realized P&L"]]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["Strategy"],
            x=df["Realized P&L"],
            orientation="h",
            marker_color=colors_list,
            hovertemplate="%{y}<br>P&L: $%{x:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(300, len(df) * 28),
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        xaxis={"title": "Realized P&L ($)", "tickformat": "$,.0f"},
        yaxis={"title": "", "autorange": "reversed"},
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Section B: Data Quality
# ---------------------------------------------------------------------------


def _show_data_quality() -> None:
    """Render the attribution coverage audit panel."""
    section_header("Attribution Data Quality")

    coverage = sda.get_attribution_coverage(days=30)
    total = coverage["total_trades"]
    pct = coverage["coverage_pct"]

    col1, col2 = st.columns([2, 1])
    with col1:
        progress_bar(
            value=pct,
            max_value=100,
            label="30-day Attribution Coverage",
            warning_threshold=90,
            danger_threshold=75,
        )
    with col2:
        metric_card(
            label="Attributed / Total",
            value=f"{coverage['attributed_trades']} / {total}",
        )

    if pct < 90 and total > 0:
        alert_box(
            f"{total - coverage['attributed_trades']} trades in the last 30 days "
            "have incomplete strategy attribution (missing weights or names).",
            alert_type="warning",
        )

        unattributed = coverage.get("unattributed", [])
        if unattributed:
            with st.expander(f"View {len(unattributed)} unattributed trades", expanded=False):
                udf = pd.DataFrame(unattributed)
                if not udf.empty:
                    udf = udf[
                        [
                            "fill_timestamp",
                            "symbol",
                            "direction",
                            "has_names",
                            "has_weights",
                        ]
                    ].sort_values("fill_timestamp", ascending=False)
                    udf.columns = [
                        "Timestamp",
                        "Symbol",
                        "Direction",
                        "Has Names",
                        "Has Weights",
                    ]
                    st.dataframe(udf, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------------------
# Section C: Strategy Drill-Down
# ---------------------------------------------------------------------------


def _show_strategy_detail(
    strategy_name: str,
    metadata: dict[str, dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> None:
    """Render the drill-down view for a single strategy."""
    meta = metadata.get(strategy_name, {})
    display_name = meta.get("display_name", strategy_name)
    source_url = meta.get("source_url", "")
    date_updated = meta.get("date_updated", "")
    assets = meta.get("assets", [])
    frontrunners = meta.get("frontrunners", [])

    # Header with metadata
    st.subheader(display_name)
    info_parts = []
    if source_url:
        info_parts.append(f"[Source]({source_url})")
    if date_updated:
        info_parts.append(f"Updated: {date_updated}")
    if info_parts:
        st.caption(" | ".join(info_parts))

    # Current snapshot KPIs
    snap = next((s for s in snapshots if s["strategy_name"] == strategy_name), None)
    if snap:
        metric_row(
            [
                {
                    "label": "Realized P&L",
                    "value": format_currency(snap["realized_pnl"], include_sign=True),
                    "delta_positive": snap["realized_pnl"] > 0,
                },
                {
                    "label": "Win Rate",
                    "value": format_percent(snap["win_rate"]),
                },
                {
                    "label": "Completed Trades",
                    "value": str(snap["completed_trades"]),
                },
                {
                    "label": "Open Lots",
                    "value": str(snap["current_holdings"]),
                },
                {
                    "label": "Avg Profit/Trade",
                    "value": format_currency(snap["avg_profit_per_trade"], include_sign=True),
                },
            ]
        )

    # Tabbed detail views
    tabs = st.tabs(
        [
            "P&L Time Series",
            "Risk Metrics",
            "Open Lots",
            "Closed Lots",
            "Trade History",
            "Assets",
        ]
    )

    # -- Tab 1: Time Series
    with tabs[0]:
        _show_time_series_tab(strategy_name)

    # -- Tab 2: Risk Metrics
    with tabs[1]:
        _show_risk_metrics_tab(strategy_name)

    # -- Tab 3: Open Lots
    with tabs[2]:
        _show_lots_tab(strategy_name, lot_type="open")

    # -- Tab 4: Closed Lots
    with tabs[3]:
        _show_lots_tab(strategy_name, lot_type="closed")

    # -- Tab 5: Trade History
    with tabs[4]:
        _show_trades_tab(strategy_name)

    # -- Tab 6: Assets
    with tabs[5]:
        _show_assets_tab(strategy_name, assets, frontrunners)


def _show_time_series_tab(strategy_name: str) -> None:
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


def _show_risk_metrics_tab(strategy_name: str) -> None:
    """Render risk and return metrics."""
    section_header("Risk & Return Metrics")
    time_series = sda.get_strategy_time_series(strategy_name)

    if len(time_series) < 5:
        st.info(
            "Need at least 5 data points for risk metrics. "
            "More trade executions will populate this."
        )
        return

    metrics = _calculate_risk_metrics(time_series)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            "Sharpe Ratio",
            f"{metrics['sharpe']:.2f}",
            delta_positive=metrics["sharpe"] > 0,
        )
    with col2:
        metric_card(
            "Max Drawdown",
            format_currency(metrics["max_drawdown"]),
        )
    with col3:
        metric_card(
            "Volatility (Ann.)",
            format_currency(metrics["volatility"]),
        )
    with col4:
        pf = metrics["profit_factor"]
        pf_str = f"{pf:.2f}" if pf != float("inf") else "Inf"
        metric_card(
            "Profit Factor",
            pf_str,
            delta_positive=pf > 1.0 if pf != float("inf") else True,
        )

    # Drawdown chart
    pnl_values = [s["realized_pnl"] for s in time_series]
    timestamps = [s["snapshot_timestamp"] for s in time_series]

    running_max_vals: list[float] = []
    drawdowns: list[float] = []
    peak = pnl_values[0]
    for pnl in pnl_values:
        if pnl > peak:
            peak = pnl
        running_max_vals.append(peak)
        drawdowns.append(pnl - peak)

    import math

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


def _show_lots_tab(strategy_name: str, lot_type: str) -> None:
    """Render open or closed lots table."""
    section_header(f"{'Open' if lot_type == 'open' else 'Closed'} Lots")

    lots_data = sda.get_strategy_lots(strategy_name)
    lots = lots_data.get(lot_type, [])

    if not lots:
        st.info(f"No {lot_type} lots found for this strategy.")
        return

    if lot_type == "open":
        rows = []
        for lot in lots:
            rows.append(
                {
                    "Symbol": lot["symbol"],
                    "Entry Date": lot["entry_timestamp"][:10] if lot["entry_timestamp"] else "",
                    "Entry Price": lot["entry_price"],
                    "Qty": lot["entry_qty"],
                    "Remaining": lot["remaining_qty"],
                    "Cost Basis": lot["cost_basis"],
                }
            )
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Symbol")
            styled_dataframe(
                df,
                formats={
                    "Entry Price": "${:.2f}",
                    "Qty": "{:.4f}",
                    "Remaining": "{:.4f}",
                    "Cost Basis": "${:,.2f}",
                },
            )

            # Pie chart of open positions by cost basis
            if len(df) > 1:
                fig_pie = go.Figure()
                fig_pie.add_trace(
                    go.Pie(
                        labels=df["Symbol"],
                        values=df["Cost Basis"],
                        hole=0.4,
                        hovertemplate=(
                            "%{label}<br>Cost Basis: $%{value:,.2f}<br>%{percent}<extra></extra>"
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

    else:
        rows = []
        for lot in lots:
            # Compute average exit from exit records
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

            # Hold duration
            entry_ts = lot["entry_timestamp"]
            closed_ts = lot.get("fully_closed_at", "")
            hold_days = ""
            if entry_ts and closed_ts:
                try:
                    entry_dt = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
                    close_dt = datetime.fromisoformat(closed_ts.replace("Z", "+00:00"))
                    delta = close_dt - entry_dt
                    hold_days = f"{delta.days}d"
                except (ValueError, TypeError):
                    pass

            rows.append(
                {
                    "Symbol": lot["symbol"],
                    "Entry Date": entry_ts[:10] if entry_ts else "",
                    "Entry Price": lot["entry_price"],
                    "Avg Exit": avg_exit,
                    "Qty": lot["entry_qty"],
                    "P&L": pnl,
                    "P&L %": pnl_pct,
                    "Hold": hold_days,
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
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

            # P&L distribution histogram
            section_header("P&L Distribution")
            pnl_vals = df["P&L"].tolist()
            ["#10B981" if v >= 0 else "#EF4444" for v in pnl_vals]
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


def _show_trades_tab(strategy_name: str) -> None:
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


def _show_assets_tab(
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


# ---------------------------------------------------------------------------
# Section D: Strategy Comparison
# ---------------------------------------------------------------------------


def _show_comparison(
    snapshots: list[dict[str, Any]],
    metadata: dict[str, dict[str, Any]],
) -> None:
    """Render multi-strategy comparison overlay."""
    section_header("Strategy Comparison")

    strategy_names = sorted(s["strategy_name"] for s in snapshots)
    display_map = {
        name: metadata.get(name, {}).get("display_name", name) for name in strategy_names
    }

    selected = st.multiselect(
        "Select strategies to compare (2-6)",
        options=strategy_names,
        format_func=lambda x: display_map.get(x, x),
        max_selections=6,
    )

    if len(selected) < 2:
        st.info("Select at least 2 strategies to compare.")
        return

    # Overlaid P&L line chart
    accent_colors = [
        "#7CF5D4",
        "#10B981",
        "#F59E0B",
        "#3B82F6",
        "#8B5CF6",
        "#EF4444",
    ]

    fig_cmp = go.Figure()
    comparison_rows: list[dict[str, Any]] = []

    for i, name in enumerate(selected):
        ts = sda.get_strategy_time_series(name)
        if not ts:
            continue

        df_ts = pd.DataFrame(ts)
        df_ts["timestamp"] = pd.to_datetime(df_ts["snapshot_timestamp"])
        df_ts = df_ts.sort_values("timestamp")
        # Deduplicate to daily
        df_ts["date"] = df_ts["timestamp"].dt.date
        df_ts = df_ts.drop_duplicates(subset="date", keep="last")

        color = accent_colors[i % len(accent_colors)]
        display = display_map.get(name, name)

        fig_cmp.add_trace(
            go.Scatter(
                x=df_ts["timestamp"],
                y=df_ts["realized_pnl"],
                mode="lines",
                name=display,
                line={"color": color, "width": 2},
                hovertemplate=(
                    f"{display}<br>Date: %{{x|%b %d, %Y}}<br>P&L: $%{{y:,.2f}}<extra></extra>"
                ),
            )
        )

        # Side-by-side metrics
        snap = next((s for s in snapshots if s["strategy_name"] == name), None)
        risk = _calculate_risk_metrics(ts)
        if snap:
            comparison_rows.append(
                {
                    "Strategy": display,
                    "Realized P&L": snap["realized_pnl"],
                    "Win Rate (%)": snap["win_rate"],
                    "Trades": snap["completed_trades"],
                    "Sharpe": risk["sharpe"],
                    "Max DD": risk["max_drawdown"],
                    "Profit Factor": (
                        risk["profit_factor"] if risk["profit_factor"] != float("inf") else 999.99
                    ),
                }
            )

    fig_cmp.update_layout(
        height=400,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        xaxis={"title": ""},
        yaxis={"title": "Realized P&L ($)", "tickformat": "$,.0f"},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    # Comparison table
    if comparison_rows:
        cdf = pd.DataFrame(comparison_rows)
        styled_dataframe(
            cdf,
            formats={
                "Realized P&L": "${:,.2f}",
                "Win Rate (%)": "{:.1f}%",
                "Sharpe": "{:.2f}",
                "Max DD": "${:,.2f}",
                "Profit Factor": "{:.2f}",
            },
            highlight_positive_negative=["Realized P&L", "Sharpe"],
        )


# ---------------------------------------------------------------------------
# Main page entry point
# ---------------------------------------------------------------------------


def show() -> None:
    """Display the Strategy Performance page."""
    inject_styles()

    st.title("Strategy Performance")
    st.caption("Per-strategy analytics, lot-level P&L tracking, and attribution quality monitoring")

    settings = get_dashboard_settings()
    if not settings.has_aws_credentials():
        st.error(
            "AWS credentials not configured. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in "
            "Streamlit secrets or environment variables."
        )
        return

    # Load shared data
    snapshots = sda.get_all_strategy_snapshots()
    metadata = sda.get_all_strategy_metadata()

    # ----- Section A: Summary Grid -----
    _show_summary_grid(snapshots, metadata)

    st.markdown("---")

    # ----- Section B: Data Quality -----
    with st.expander("Attribution Data Quality", expanded=False):
        _show_data_quality()

    st.markdown("---")

    # ----- Section C: Strategy Drill-Down -----
    section_header("Strategy Detail")

    if not snapshots:
        st.info("No strategy data to drill into.")
        return

    strategy_names = sorted(s["strategy_name"] for s in snapshots)
    display_map = {
        name: metadata.get(name, {}).get("display_name", name) for name in strategy_names
    }

    selected_strategy = st.selectbox(
        "Select Strategy",
        options=strategy_names,
        format_func=lambda x: display_map.get(x, x),
    )

    if selected_strategy:
        _show_strategy_detail(selected_strategy, metadata, snapshots)

    st.markdown("---")

    # ----- Section D: Comparison -----
    if len(snapshots) >= 2:
        _show_comparison(snapshots, metadata)

    # Footer
    st.caption(
        "Data from StrategyPerformanceTable (snapshots) and "
        "TradeLedger (lots). Auto-refreshes every 60 seconds."
    )
