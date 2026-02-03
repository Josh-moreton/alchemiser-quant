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
    try:
        settings = get_dashboard_settings()
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
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
    st.title("Trade History")
    st.caption("Comprehensive trade analytics with strategy and symbol attribution")

    # Filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Date range
        date_range = st.selectbox(
            "Date Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time", "Custom"],
        )

        if date_range == "Custom":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
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

    with col2:
        # Symbol filter
        symbol_filter = st.text_input("Symbol Filter (optional)", placeholder="e.g., AAPL")

    with col3:
        st.write("")  # Spacing
        st.write("")
        apply_filters = st.button("Apply Filters", type="primary")

    st.divider()

    # Load trades
    start_iso = start_date.isoformat() + "T00:00:00Z" if start_date else None
    end_iso = end_date.isoformat() + "T23:59:59Z" if end_date else None
    symbol = symbol_filter.upper() if symbol_filter else None

    trades = get_trades(start_iso, end_iso, symbol)

    if not trades:
        st.warning("No trades found matching filters")
        return

    # Summary metrics
    st.subheader("Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    total_trades = len(trades)
    buy_trades = [t for t in trades if t["direction"] == "BUY"]
    sell_trades = [t for t in trades if t["direction"] == "SELL"]
    total_value = sum(t["filled_qty"] * t["fill_price"] for t in trades)
    unique_symbols = len(set(t["symbol"] for t in trades))

    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("BUY Trades", len(buy_trades))
    with col3:
        st.metric("SELL Trades", len(sell_trades))
    with col4:
        st.metric("Total Value", f"${total_value:,.2f}")
    with col5:
        st.metric("Unique Symbols", unique_symbols)

    st.divider()

    # Per-Strategy Performance
    st.subheader("Per-Strategy Performance")
    strategy_df = get_strategy_performance(trades)

    if not strategy_df.empty:
        st.dataframe(
            strategy_df.style.format({
                "Total Value": "${:,.2f}",
            }),
            width="stretch",
            hide_index=True,
        )

        # Chart
        st.subheader("Strategy Trade Volume")
        chart_data = strategy_df.set_index("Strategy")["Total Value"]
        st.bar_chart(chart_data, width="stretch")
    else:
        st.info("No strategy attribution data available")

    st.divider()

    # Per-Symbol Performance
    st.subheader("Per-Symbol Performance")
    symbol_df = get_symbol_performance(trades)

    if not symbol_df.empty:
        st.dataframe(
            symbol_df.style.format({
                "Net Qty": "{:.4f}",
                "Total Value": "${:,.2f}",
                "Avg Buy Price": "${:.2f}",
                "Avg Sell Price": "${:.2f}",
            }),
            width="stretch",
            hide_index=True,
        )

        # Top 10 symbols chart
        if len(symbol_df) > 0:
            st.subheader("Top Symbols by Trade Value")
            chart_data = symbol_df.head(10).set_index("Symbol")["Total Value"]
            st.bar_chart(chart_data, width="stretch")
    else:
        st.info("No symbol data available")

    st.divider()

    # Recent Trades Table
    st.subheader("Recent Trades")

    # Show last 50 trades
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
            "Order ID": t["order_id"][:12] + "...",
        }
        for t in recent_trades
    ])

    st.dataframe(
        df.style.format({
            "Qty": "{:.4f}",
            "Price": "${:.2f}",
            "Value": "${:,.2f}",
        }),
        width="stretch",
        hide_index=True,
    )

    if len(trades) > 50:
        st.caption(f"Showing 50 of {len(trades)} trades. Use filters to narrow results.")

    st.divider()

    # Daily trade volume chart
    st.subheader("Daily Trade Volume")
    
    # Group by date
    for trade in trades:
        trade["Date"] = trade["fill_timestamp"][:10]  # Extract YYYY-MM-DD
    
    daily_df = pd.DataFrame(trades)
    if not daily_df.empty:
        daily_volume = daily_df.groupby("Date").agg({
            "filled_qty": "count",  # Count of trades
        }).rename(columns={"filled_qty": "Trade Count"})
        
        st.line_chart(daily_volume["Trade Count"], width="stretch")
