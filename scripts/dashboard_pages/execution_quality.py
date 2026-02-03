#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Execution Quality (TCA) dashboard page.

Transaction Cost Analysis metrics for monitoring execution quality:
- Slippage analysis (bps, dollar amount)
- Spread capture efficiency
- Walk-the-book step analysis
- Fill timing metrics
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import _setup_imports  # noqa: F401
import boto3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from boto3.dynamodb.conditions import Attr
from dotenv import load_dotenv

from dashboard_settings import get_dashboard_settings

from .components import (
    direction_styled_dataframe,
    hero_metric,
    metric_row,
    section_header,
    styled_dataframe,
)
from .styles import format_currency, format_percent, inject_styles

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_trades_with_execution_quality(
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """Get trades from DynamoDB with execution quality metrics."""
    settings = get_dashboard_settings()
    if not settings.has_aws_credentials():
        st.error(
            "AWS credentials not configured or invalid. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in Streamlit secrets."
        )
        return []

    try:
        dynamodb = boto3.resource("dynamodb", **settings.get_boto3_client_kwargs())
        table = dynamodb.Table(settings.trade_ledger_table)

        # Build filter expression
        filter_expression = Attr("PK").begins_with("TRADE#")

        if start_date or end_date:
            if start_date and end_date:
                filter_expression = filter_expression & Attr("fill_timestamp").between(
                    start_date, end_date
                )
            elif start_date:
                filter_expression = filter_expression & Attr("fill_timestamp").gte(start_date)
            else:
                filter_expression = filter_expression & Attr("fill_timestamp").lte(end_date)

        # Scan table
        response = table.scan(FilterExpression=filter_expression)
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        # Convert to standard dict format
        trades = []
        for item in items:
            if item.get("EntityType") != "TRADE":
                continue

            trade = {
                "order_id": item.get("order_id", ""),
                "symbol": item.get("symbol", ""),
                "direction": item.get("direction", ""),
                "filled_qty": float(item.get("filled_qty", 0)),
                "fill_price": float(item.get("fill_price", 0)),
                "fill_timestamp": item.get("fill_timestamp", ""),
                "order_type": item.get("order_type", "MARKET"),
                # Execution quality fields
                "bid_at_fill": float(item.get("bid_at_fill", 0)) if item.get("bid_at_fill") else None,
                "ask_at_fill": float(item.get("ask_at_fill", 0)) if item.get("ask_at_fill") else None,
                "expected_price": float(item.get("expected_price", 0)) if item.get("expected_price") else None,
                "slippage_bps": float(item.get("slippage_bps", 0)) if item.get("slippage_bps") else None,
                "slippage_amount": float(item.get("slippage_amount", 0)) if item.get("slippage_amount") else None,
                "spread_at_order": float(item.get("spread_at_order", 0)) if item.get("spread_at_order") else None,
                "execution_steps": int(item.get("execution_steps", 0)) if item.get("execution_steps") else None,
                "time_to_fill_ms": int(item.get("time_to_fill_ms", 0)) if item.get("time_to_fill_ms") else None,
            }
            trades.append(trade)

        # Sort by timestamp descending
        trades.sort(key=lambda x: x["fill_timestamp"], reverse=True)
        return trades

    except Exception as e:
        st.error(f"Error loading trades: {e}")
        return []


def calculate_summary_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate summary execution quality metrics."""
    # Filter trades with slippage data
    trades_with_slippage = [t for t in trades if t.get("slippage_bps") is not None]
    trades_with_spread = [
        t for t in trades if t.get("bid_at_fill") and t.get("ask_at_fill")
    ]

    metrics = {
        "total_trades": len(trades),
        "trades_with_tca": len(trades_with_slippage),
        "avg_slippage_bps": 0.0,
        "median_slippage_bps": 0.0,
        "total_slippage_cost": 0.0,
        "worst_slippage_bps": 0.0,
        "best_slippage_bps": 0.0,
        "positive_slippage_count": 0,  # Worse than expected
        "negative_slippage_count": 0,  # Better than expected (price improvement)
        "avg_spread_bps": 0.0,
        "avg_time_to_fill_ms": 0.0,
    }

    if trades_with_slippage:
        slippages = [t["slippage_bps"] for t in trades_with_slippage]
        metrics["avg_slippage_bps"] = sum(slippages) / len(slippages)
        metrics["median_slippage_bps"] = sorted(slippages)[len(slippages) // 2]
        metrics["worst_slippage_bps"] = max(slippages)
        metrics["best_slippage_bps"] = min(slippages)
        metrics["positive_slippage_count"] = len([s for s in slippages if s > 0])
        metrics["negative_slippage_count"] = len([s for s in slippages if s < 0])

        # Total slippage cost
        metrics["total_slippage_cost"] = sum(
            abs(t.get("slippage_amount", 0) or 0) for t in trades_with_slippage
        )

    # Calculate spread metrics
    if trades_with_spread:
        spreads_bps = []
        for t in trades_with_spread:
            mid = (t["bid_at_fill"] + t["ask_at_fill"]) / 2
            if mid > 0:
                spread_bps = ((t["ask_at_fill"] - t["bid_at_fill"]) / mid) * 10000
                spreads_bps.append(spread_bps)
        if spreads_bps:
            metrics["avg_spread_bps"] = sum(spreads_bps) / len(spreads_bps)

    # Time to fill
    trades_with_time = [t for t in trades if t.get("time_to_fill_ms")]
    if trades_with_time:
        metrics["avg_time_to_fill_ms"] = sum(
            t["time_to_fill_ms"] for t in trades_with_time
        ) / len(trades_with_time)

    return metrics


def show() -> None:
    """Display the execution quality (TCA) dashboard page."""
    # Inject styles
    inject_styles()

    st.title("Execution Quality")
    st.caption("Transaction Cost Analysis (TCA) - Monitor fill quality and slippage")

    # =========================================================================
    # FILTER BAR
    # =========================================================================
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        date_range = st.selectbox(
            "Date Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
            label_visibility="collapsed",
        )

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    if date_range == "Last 7 Days":
        start_date = end_date - timedelta(days=7)
    elif date_range == "Last 30 Days":
        start_date = end_date - timedelta(days=30)
    elif date_range == "Last 90 Days":
        start_date = end_date - timedelta(days=90)
    else:  # All Time
        start_date = None
        end_date = None

    start_iso = start_date.isoformat() + "T00:00:00Z" if start_date else None
    end_iso = end_date.isoformat() + "T23:59:59Z" if end_date else None

    # Load trades
    trades = get_trades_with_execution_quality(start_iso, end_iso)

    if not trades:
        st.warning("No trades found matching filters")
        return

    # Calculate metrics
    metrics = calculate_summary_metrics(trades)

    # =========================================================================
    # HERO METRICS
    # =========================================================================
    if metrics["trades_with_tca"] > 0:
        slippage_color = "Good" if metrics["avg_slippage_bps"] < 5 else ("Warning" if metrics["avg_slippage_bps"] < 10 else "Poor")
        hero_metric(
            label="Average Slippage",
            value=f"{metrics['avg_slippage_bps']:.2f} bps ({slippage_color})",
            subtitle=f"Based on {metrics['trades_with_tca']} trades with TCA data",
        )
    else:
        hero_metric(
            label="Average Slippage",
            value="No TCA data",
            subtitle="Execute trades to start collecting execution quality metrics",
        )

    # Summary metrics row
    metric_row([
        {
            "label": "Total Trades",
            "value": f"{metrics['total_trades']:,}",
        },
        {
            "label": "Total Slippage Cost",
            "value": format_currency(metrics["total_slippage_cost"]),
            "delta_positive": False if metrics["total_slippage_cost"] > 0 else None,
        },
        {
            "label": "Price Improvement",
            "value": f"{metrics['negative_slippage_count']:,} trades",
            "delta_positive": True,
        },
        {
            "label": "Avg Time to Fill",
            "value": f"{metrics['avg_time_to_fill_ms']:.0f}ms" if metrics["avg_time_to_fill_ms"] > 0 else "N/A",
        },
    ])

    # =========================================================================
    # TABBED VIEWS
    # =========================================================================
    tab_slippage, tab_spread, tab_timing, tab_details = st.tabs([
        "Slippage Analysis",
        "Spread Analysis",
        "Timing Analysis",
        "Trade Details",
    ])

    with tab_slippage:
        _show_slippage_tab(trades, metrics)

    with tab_spread:
        _show_spread_tab(trades)

    with tab_timing:
        _show_timing_tab(trades)

    with tab_details:
        _show_details_tab(trades)


def _show_slippage_tab(trades: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    """Show slippage analysis tab."""
    section_header("Slippage Distribution")

    trades_with_slippage = [t for t in trades if t.get("slippage_bps") is not None]

    if not trades_with_slippage:
        st.info("No slippage data available yet. New trades will include TCA metrics.")
        return

    # Slippage distribution histogram
    slippages = [t["slippage_bps"] for t in trades_with_slippage]
    df_slippage = pd.DataFrame({"Slippage (bps)": slippages})

    fig_hist = px.histogram(
        df_slippage,
        x="Slippage (bps)",
        nbins=30,
        title="",
        color_discrete_sequence=["#7CF5D4"],
    )
    fig_hist.add_vline(x=0, line_dash="dash", line_color="white", annotation_text="Break-even")
    fig_hist.add_vline(x=metrics["avg_slippage_bps"], line_dash="dot", line_color="orange", annotation_text="Avg")
    fig_hist.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Slippage by symbol
    section_header("Slippage by Symbol")
    symbol_slippage = {}
    for t in trades_with_slippage:
        symbol = t["symbol"]
        if symbol not in symbol_slippage:
            symbol_slippage[symbol] = {"slippages": [], "total_cost": 0}
        symbol_slippage[symbol]["slippages"].append(t["slippage_bps"])
        if t.get("slippage_amount"):
            symbol_slippage[symbol]["total_cost"] += abs(t["slippage_amount"])

    symbol_df = pd.DataFrame([
        {
            "Symbol": s,
            "Trade Count": len(d["slippages"]),
            "Avg Slippage (bps)": sum(d["slippages"]) / len(d["slippages"]),
            "Max Slippage (bps)": max(d["slippages"]),
            "Total Cost ($)": d["total_cost"],
        }
        for s, d in symbol_slippage.items()
    ]).sort_values("Avg Slippage (bps)", ascending=False)

    styled_dataframe(
        symbol_df,
        formats={
            "Avg Slippage (bps)": "{:.2f}",
            "Max Slippage (bps)": "{:.2f}",
            "Total Cost ($)": "${:.2f}",
        },
        highlight_positive_negative=["Avg Slippage (bps)"],
    )

    # Slippage by direction
    col1, col2 = st.columns(2)
    with col1:
        section_header("BUY Orders")
        buy_slippages = [t["slippage_bps"] for t in trades_with_slippage if t["direction"] == "BUY"]
        if buy_slippages:
            avg_buy = sum(buy_slippages) / len(buy_slippages)
            st.metric("Average Slippage", f"{avg_buy:.2f} bps", delta=f"{len(buy_slippages)} orders")
        else:
            st.info("No BUY orders with slippage data")

    with col2:
        section_header("SELL Orders")
        sell_slippages = [t["slippage_bps"] for t in trades_with_slippage if t["direction"] == "SELL"]
        if sell_slippages:
            avg_sell = sum(sell_slippages) / len(sell_slippages)
            st.metric("Average Slippage", f"{avg_sell:.2f} bps", delta=f"{len(sell_slippages)} orders")
        else:
            st.info("No SELL orders with slippage data")


def _show_spread_tab(trades: list[dict[str, Any]]) -> None:
    """Show spread analysis tab."""
    section_header("Bid-Ask Spread Analysis")

    trades_with_spread = [
        t for t in trades if t.get("bid_at_fill") and t.get("ask_at_fill")
    ]

    if not trades_with_spread:
        st.info("No spread data available. Spread is captured when real-time quotes are available during execution.")
        return

    # Calculate spread for each trade
    spread_data = []
    for t in trades_with_spread:
        mid = (t["bid_at_fill"] + t["ask_at_fill"]) / 2
        spread_abs = t["ask_at_fill"] - t["bid_at_fill"]
        spread_bps = (spread_abs / mid) * 10000 if mid > 0 else 0
        spread_data.append({
            "symbol": t["symbol"],
            "spread_bps": spread_bps,
            "spread_abs": spread_abs,
            "direction": t["direction"],
            "fill_price": t["fill_price"],
            "mid_price": mid,
            "timestamp": t["fill_timestamp"],
        })

    df = pd.DataFrame(spread_data)

    # Spread distribution
    fig_spread = px.histogram(
        df,
        x="spread_bps",
        nbins=20,
        title="Spread Distribution (bps)",
        color_discrete_sequence=["#7CF5D4"],
    )
    fig_spread.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_title="Spread (bps)",
    )
    st.plotly_chart(fig_spread, use_container_width=True)

    # Spread by symbol
    section_header("Average Spread by Symbol")
    symbol_spread = df.groupby("symbol").agg({
        "spread_bps": ["mean", "max", "count"],
    }).round(2)
    symbol_spread.columns = ["Avg Spread (bps)", "Max Spread (bps)", "Trade Count"]
    symbol_spread = symbol_spread.sort_values("Avg Spread (bps)", ascending=False)
    st.dataframe(symbol_spread, use_container_width=True)


def _show_timing_tab(trades: list[dict[str, Any]]) -> None:
    """Show timing analysis tab."""
    section_header("Execution Timing")

    trades_with_time = [t for t in trades if t.get("time_to_fill_ms")]

    if not trades_with_time:
        st.info("No timing data available. Time to fill is calculated when fill timestamps are available.")
        return

    # Time to fill distribution
    times = [t["time_to_fill_ms"] for t in trades_with_time]
    df_time = pd.DataFrame({"Time to Fill (ms)": times})

    fig_time = px.histogram(
        df_time,
        x="Time to Fill (ms)",
        nbins=30,
        title="",
        color_discrete_sequence=["#7CF5D4"],
    )
    fig_time.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig_time, use_container_width=True)

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Time", f"{sum(times)/len(times):.0f}ms")
    with col2:
        st.metric("Median Time", f"{sorted(times)[len(times)//2]:.0f}ms")
    with col3:
        st.metric("Min Time", f"{min(times):.0f}ms")
    with col4:
        st.metric("Max Time", f"{max(times):.0f}ms")

    # Execution steps analysis
    section_header("Walk-the-Book Steps")
    trades_with_steps = [t for t in trades if t.get("execution_steps")]

    if trades_with_steps:
        steps = [t["execution_steps"] for t in trades_with_steps]
        step_counts = pd.Series(steps).value_counts().sort_index()

        fig_steps = go.Figure()
        fig_steps.add_trace(go.Bar(
            x=[f"Step {s}" if s < 4 else "Market" for s in step_counts.index],
            y=step_counts.values,
            marker_color="#7CF5D4",
            hovertemplate="Step %{x}<br>Orders: %{y}<extra></extra>",
        ))
        fig_steps.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Execution Step",
            yaxis_title="Order Count",
        )
        st.plotly_chart(fig_steps, use_container_width=True)

        # Step interpretation
        step_1_pct = (step_counts.get(1, 0) / len(steps)) * 100 if steps else 0
        st.caption(
            f"**{step_1_pct:.1f}%** of orders filled at first limit price (50% of spread). "
            "Higher is better - means orders fill at better prices."
        )
    else:
        st.info("No walk-the-book step data available.")


def _show_details_tab(trades: list[dict[str, Any]]) -> None:
    """Show detailed trade log with TCA data."""
    section_header("Execution Quality Details")

    # Build detail table
    detail_rows = []
    for t in trades[:100]:  # Limit to 100 most recent
        slippage_str = f"{t['slippage_bps']:.2f}" if t.get("slippage_bps") is not None else "N/A"
        spread_bps = None
        if t.get("bid_at_fill") and t.get("ask_at_fill"):
            mid = (t["bid_at_fill"] + t["ask_at_fill"]) / 2
            if mid > 0:
                spread_bps = ((t["ask_at_fill"] - t["bid_at_fill"]) / mid) * 10000

        detail_rows.append({
            "Timestamp": t["fill_timestamp"][:19],
            "Symbol": t["symbol"],
            "Direction": t["direction"],
            "Qty": t["filled_qty"],
            "Fill Price": t["fill_price"],
            "Expected": t.get("expected_price") or "N/A",
            "Slippage (bps)": slippage_str,
            "Spread (bps)": f"{spread_bps:.2f}" if spread_bps else "N/A",
            "Time (ms)": t.get("time_to_fill_ms") or "N/A",
            "Steps": t.get("execution_steps") or "N/A",
        })

    df = pd.DataFrame(detail_rows)

    direction_styled_dataframe(
        df,
        formats={
            "Qty": "{:.4f}",
            "Fill Price": "${:.2f}",
        },
    )

    if len(trades) > 100:
        st.caption(f"Showing 100 of {len(trades)} trades. Use date filters to narrow results.")
