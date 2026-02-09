"""Business Unit: dashboard | Status: current.

Strategy Performance page -- per-strategy analytics with lot-level detail.

Dual data source architecture:
- StrategyPerformanceTable for fast summary KPIs and time-series charts
- TradeLedger for lot-level drill-down (open/closed lots, trade history)
- Strategy ledger metadata for enrichment (display names, source URLs, assets)

Sections: A) summary grid, B) data quality, C) drill-down, D) comparison.
Tab rendering is delegated to ``_strategy_tabs`` to stay under 500 lines.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from settings import get_dashboard_settings

from data import strategy as sda
from data.risk import calculate_risk_metrics
from pages._strategy_tabs import (
    show_assets_tab,
    show_lots_tab,
    show_risk_metrics_tab,
    show_time_series_tab,
    show_trades_tab,
)
from components.ui import (
    alert_box,
    hero_metric,
    metric_card,
    metric_row,
    progress_bar,
    section_header,
    styled_dataframe,
)
from components.styles import (
    format_currency,
    format_percent,
    inject_styles,
)

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
                "value": (
                    format_percent(capital_deployed) if capital_deployed is not None else "N/A"
                ),
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
        show_time_series_tab(strategy_name)

    # -- Tab 2: Risk Metrics
    with tabs[1]:
        show_risk_metrics_tab(strategy_name)

    # -- Tab 3: Open Lots
    with tabs[2]:
        show_lots_tab(strategy_name, lot_type="open")

    # -- Tab 4: Closed Lots
    with tabs[3]:
        show_lots_tab(strategy_name, lot_type="closed")

    # -- Tab 5: Trade History
    with tabs[4]:
        show_trades_tab(strategy_name)

    # -- Tab 6: Assets
    with tabs[5]:
        show_assets_tab(strategy_name, assets, frontrunners)


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
        risk = calculate_risk_metrics(ts)
        if snap:
            comparison_rows.append(
                {
                    "Strategy": display,
                    "Realized P&L": snap["realized_pnl"],
                    "Win Rate (%)": snap["win_rate"],
                    "Trades": snap["completed_trades"],
                    "P&L Sharpe": risk["pnl_sharpe"],
                    "Max DD": risk["max_drawdown"],
                    "Profit Factor": (
                        risk["profit_factor"] if risk["profit_factor"] is not None else float("nan")
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
                "P&L Sharpe": "{:.2f}",
                "Max DD": "${:,.2f}",
                "Profit Factor": "{:.2f}",
            },
            highlight_positive_negative=["Realized P&L", "P&L Sharpe"],
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
        "TradeLedger (lots). Data cached for 60-300s per query."
    )
