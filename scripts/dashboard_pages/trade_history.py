#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Trade History page with per-strategy and per-symbol attribution.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import _setup_imports  # noqa: F401
import boto3
import pandas as pd
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
from .styles import format_currency, inject_styles

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_trades(
    start_date: str | None = None,
    end_date: str | None = None,
    symbol: str | None = None,
) -> list[dict[str, Any]]:
    """Get trades from DynamoDB with optional filters."""
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
                filter_expression = filter_expression & Attr("fill_timestamp").between(start_date, end_date)
            elif start_date:
                filter_expression = filter_expression & Attr("fill_timestamp").gte(start_date)
            else:
                filter_expression = filter_expression & Attr("fill_timestamp").lte(end_date)

        if symbol:
            filter_expression = filter_expression & Attr("symbol").eq(symbol)

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

            strategy_names = item.get("strategy_names", [])
            if isinstance(strategy_names, list):
                strategies = strategy_names
            else:
                strategies = []

            trades.append({
                "order_id": item.get("order_id", ""),
                "symbol": item.get("symbol", ""),
                "direction": item.get("direction", ""),
                "filled_qty": float(item.get("filled_qty", 0)),
                "fill_price": float(item.get("fill_price", 0)),
                "fill_timestamp": item.get("fill_timestamp", ""),
                "strategy_names": strategies,
                "correlation_id": item.get("correlation_id", ""),
            })

        # Sort by timestamp descending
        trades.sort(key=lambda x: x["fill_timestamp"], reverse=True)
        return trades

    except Exception as e:
        st.error(f"Error loading trades: {e}")
        return []


@st.cache_data(ttl=300)
def get_strategy_performance(trades: list[dict[str, Any]]) -> pd.DataFrame:
    """Calculate per-strategy performance metrics."""
    strategy_data = {}

    for trade in trades:
        trade_value = trade["filled_qty"] * trade["fill_price"]

        for strategy in trade["strategy_names"]:
            if strategy not in strategy_data:
                strategy_data[strategy] = {
                    "Strategy": strategy,
                    "Trade Count": 0,
                    "Total Value": 0.0,
                    "BUY Count": 0,
                    "SELL Count": 0,
                    "Symbols": set(),
                }

            data = strategy_data[strategy]
            data["Trade Count"] += 1
            data["Total Value"] += trade_value
            data["Symbols"].add(trade["symbol"])

            if trade["direction"] == "BUY":
                data["BUY Count"] += 1
            elif trade["direction"] == "SELL":
                data["SELL Count"] += 1

    # Convert to DataFrame
    if not strategy_data:
        return pd.DataFrame()

    rows = []
    for data in strategy_data.values():
        rows.append({
            "Strategy": data["Strategy"],
            "Trade Count": data["Trade Count"],
            "Total Value": data["Total Value"],
            "BUY Count": data["BUY Count"],
            "SELL Count": data["SELL Count"],
            "Symbol Count": len(data["Symbols"]),
        })

    return pd.DataFrame(rows).sort_values("Total Value", ascending=False)


@st.cache_data(ttl=300)
def get_symbol_performance(trades: list[dict[str, Any]]) -> pd.DataFrame:
    """Calculate per-symbol performance metrics."""
    symbol_data = {}

    for trade in trades:
        symbol = trade["symbol"]
        trade_value = trade["filled_qty"] * trade["fill_price"]

        if symbol not in symbol_data:
            symbol_data[symbol] = {
                "Symbol": symbol,
                "Trade Count": 0,
                "Total Qty": 0.0,
                "Total Value": 0.0,
                "BUY Count": 0,
                "SELL Count": 0,
                "Avg Buy Price": [],
                "Avg Sell Price": [],
            }

        data = symbol_data[symbol]
        data["Trade Count"] += 1
        data["Total Value"] += trade_value

        if trade["direction"] == "BUY":
            data["BUY Count"] += 1
            data["Total Qty"] += trade["filled_qty"]
            data["Avg Buy Price"].append(trade["fill_price"])
        elif trade["direction"] == "SELL":
            data["SELL Count"] += 1
            data["Total Qty"] -= trade["filled_qty"]
            data["Avg Sell Price"].append(trade["fill_price"])

    # Convert to DataFrame
    if not symbol_data:
        return pd.DataFrame()

    rows = []
    for data in symbol_data.values():
        avg_buy = sum(data["Avg Buy Price"]) / len(data["Avg Buy Price"]) if data["Avg Buy Price"] else 0
        avg_sell = sum(data["Avg Sell Price"]) / len(data["Avg Sell Price"]) if data["Avg Sell Price"] else 0

        rows.append({
            "Symbol": data["Symbol"],
            "Trade Count": data["Trade Count"],
            "Net Qty": data["Total Qty"],
            "Total Value": data["Total Value"],
            "BUY Count": data["BUY Count"],
            "SELL Count": data["SELL Count"],
            "Avg Buy Price": avg_buy,
            "Avg Sell Price": avg_sell,
        })

    return pd.DataFrame(rows).sort_values("Total Value", ascending=False)


def show() -> None:
    """Display the trade history page."""
    # Inject styles
    inject_styles()

    st.title("Trade History")
    st.caption("Comprehensive trade analytics with strategy and symbol attribution")

    # =========================================================================
    # COMPACT FILTER BAR (horizontal)
    # =========================================================================
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        date_range = st.selectbox(
            "Date Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time", "Custom"],
            label_visibility="collapsed",
        )

    with col2:
        if date_range == "Custom":
            start_date = st.date_input("Start", label_visibility="collapsed")
        else:
            start_date = None

    with col3:
        if date_range == "Custom":
            end_date = st.date_input("End", label_visibility="collapsed")
        else:
            end_date = None

    with col4:
        symbol_filter = st.text_input("Symbol", placeholder="e.g., AAPL", label_visibility="collapsed")

    # Calculate date range
    if date_range == "Custom" and start_date and end_date:
        pass  # Use custom dates
    else:
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

    # Load trades
    start_iso = start_date.isoformat() + "T00:00:00Z" if start_date else None
    end_iso = end_date.isoformat() + "T23:59:59Z" if end_date else None
    symbol = symbol_filter.upper() if symbol_filter else None

    trades = get_trades(start_iso, end_iso, symbol)

    if not trades:
        st.warning("No trades found matching filters")
        return

    # =========================================================================
    # SUMMARY METRICS
    # =========================================================================
    total_trades = len(trades)
    buy_trades = [t for t in trades if t["direction"] == "BUY"]
    sell_trades = [t for t in trades if t["direction"] == "SELL"]
    total_value = sum(t["filled_qty"] * t["fill_price"] for t in trades)
    unique_symbols = len(set(t["symbol"] for t in trades))

    hero_metric(
        label="Total Trade Value",
        value=format_currency(total_value),
        subtitle=f"{total_trades} trades across {unique_symbols} symbols",
    )

    metric_row([
        {"label": "Total Trades", "value": f"{total_trades:,}"},
        {"label": "BUY Trades", "value": f"{len(buy_trades):,}", "delta_positive": True},
        {"label": "SELL Trades", "value": f"{len(sell_trades):,}", "delta_positive": False},
        {"label": "Unique Symbols", "value": str(unique_symbols)},
    ])

    # =========================================================================
    # TABBED VIEW: By Strategy | By Symbol | Timeline
    # =========================================================================
    tab_strategy, tab_symbol, tab_timeline, tab_recent = st.tabs([
        "📊 By Strategy",
        "🎯 By Symbol",
        "📈 Timeline",
        "📋 Recent Trades",
    ])

    with tab_strategy:
        section_header("Per-Strategy Performance")
        strategy_df = get_strategy_performance(trades)

        if not strategy_df.empty:
            styled_dataframe(
                strategy_df,
                formats={"Total Value": "${:,.2f}"},
            )

            # Chart
            st.subheader("Strategy Trade Volume")
            chart_data = strategy_df.set_index("Strategy")["Total Value"]
            st.bar_chart(chart_data, use_container_width=True)
        else:
            st.info("No strategy attribution data available")

    with tab_symbol:
        section_header("Per-Symbol Performance")
        symbol_df = get_symbol_performance(trades)

        if not symbol_df.empty:
            styled_dataframe(
                symbol_df,
                formats={
                    "Net Qty": "{:.4f}",
                    "Total Value": "${:,.2f}",
                    "Avg Buy Price": "${:.2f}",
                    "Avg Sell Price": "${:.2f}",
                },
            )

            # Top 10 symbols chart
            if len(symbol_df) > 0:
                st.subheader("Top Symbols by Trade Value")
                chart_data = symbol_df.head(10).set_index("Symbol")["Total Value"]
                st.bar_chart(chart_data, use_container_width=True)
        else:
            st.info("No symbol data available")

    with tab_timeline:
        section_header("Daily Trade Volume")

        # Group by date
        trades_copy = [t.copy() for t in trades]
        for trade in trades_copy:
            trade["Date"] = trade["fill_timestamp"][:10]

        daily_df = pd.DataFrame(trades_copy)
        if not daily_df.empty:
            daily_volume = daily_df.groupby("Date").agg({
                "filled_qty": "count",
            }).rename(columns={"filled_qty": "Trade Count"})

            st.line_chart(daily_volume["Trade Count"], use_container_width=True)

            # Daily value breakdown
            daily_value = daily_df.groupby("Date").apply(
                lambda x: (x["filled_qty"] * x["fill_price"]).sum()
            )
            st.subheader("Daily Trade Value")
            st.bar_chart(daily_value, use_container_width=True)

    with tab_recent:
        section_header("Recent Trades")

        # Show last 50 trades with direction coloring
        recent_trades = trades[:50]
        df = pd.DataFrame([
            {
                "Symbol": t["symbol"],
                "Direction": t["direction"],
                "Qty": t["filled_qty"],
                "Price": t["fill_price"],
                "Value": t["filled_qty"] * t["fill_price"],
                "Timestamp": t["fill_timestamp"][:19],
                "Strategies": ", ".join(t["strategy_names"][:2]) + ("..." if len(t["strategy_names"]) > 2 else ""),
            }
            for t in recent_trades
        ])

        direction_styled_dataframe(
            df,
            formats={
                "Qty": "{:.4f}",
                "Price": "${:.2f}",
                "Value": "${:,.2f}",
            },
        )

        if len(trades) > 50:
            st.caption(f"Showing 50 of {len(trades)} trades. Use filters to narrow results.")
