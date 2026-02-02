#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Symbol Analytics page with detailed per-symbol performance metrics.
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

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from the_alchemiser.shared.services.alpaca_account_service import AlpacaAccountService


@st.cache_data(ttl=60)
def get_all_traded_symbols() -> list[str]:
    """Get list of all symbols that have been traded."""
    try:
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.Table("alchemiser-dev-trade-ledger")

        # Scan for unique symbols
        response = table.scan(
            FilterExpression=Attr("EntityType").eq("TRADE"),
            ProjectionExpression="symbol",
        )

        symbols = set()
        for item in response.get("Items", []):
            if "symbol" in item:
                symbols.add(item["symbol"])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=Attr("EntityType").eq("TRADE"),
                ProjectionExpression="symbol",
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            for item in response.get("Items", []):
                if "symbol" in item:
                    symbols.add(item["symbol"])

        return sorted(list(symbols))

    except Exception as e:
        st.error(f"Error loading symbols: {e}")
        return []


@st.cache_data(ttl=60)
def get_symbol_trades(symbol: str) -> list[dict[str, Any]]:
    """Get all trades for a specific symbol."""
    try:
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        table_name = "alchemiser-dev-trade-ledger"

        # Query using GSI2 (symbol index)
        response = dynamodb.query(
            TableName=table_name,
            IndexName="GSI2-SymbolIndex",
            KeyConditionExpression="GSI2PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"SYMBOL#{symbol}"}},
        )

        trades = []
        for item in response.get("Items", []):
            if item.get("EntityType", {}).get("S") != "TRADE":
                continue

            strategy_names = item.get("strategy_names", {}).get("L", [])
            strategies = [s.get("S", "") for s in strategy_names]

            trades.append({
                "order_id": item.get("order_id", {}).get("S", ""),
                "symbol": item.get("symbol", {}).get("S", ""),
                "direction": item.get("direction", {}).get("S", ""),
                "filled_qty": float(item.get("filled_qty", {}).get("S", "0")),
                "fill_price": float(item.get("fill_price", {}).get("S", "0")),
                "fill_timestamp": item.get("fill_timestamp", {}).get("S", ""),
                "strategy_names": strategies,
                "correlation_id": item.get("correlation_id", {}).get("S", ""),
            })

        # Sort by timestamp
        trades.sort(key=lambda x: x["fill_timestamp"])
        return trades

    except Exception as e:
        st.error(f"Error loading trades for {symbol}: {e}")
        return []


@st.cache_data(ttl=60)
def get_current_position(symbol: str) -> dict | None:
    """Get current position for a symbol."""
    try:
        account_service = AlpacaAccountService()
        positions = account_service.get_positions()

        for pos in positions:
            if pos.symbol == symbol:
                return {
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0.0,
                    "current_price": float(pos.current_price) if pos.current_price else 0.0,
                    "market_value": float(pos.market_value) if pos.market_value else 0.0,
                    "cost_basis": float(pos.cost_basis) if pos.cost_basis else 0.0,
                    "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0.0,
                    "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0.0,
                }

        return None

    except Exception as e:
        st.error(f"Error loading position: {e}")
        return None


def calculate_symbol_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate comprehensive metrics for a symbol."""
    if not trades:
        return {}

    buy_trades = [t for t in trades if t["direction"] == "BUY"]
    sell_trades = [t for t in trades if t["direction"] == "SELL"]

    total_buy_qty = sum(t["filled_qty"] for t in buy_trades)
    total_sell_qty = sum(t["filled_qty"] for t in sell_trades)
    total_buy_value = sum(t["filled_qty"] * t["fill_price"] for t in buy_trades)
    total_sell_value = sum(t["filled_qty"] * t["fill_price"] for t in sell_trades)

    avg_buy_price = total_buy_value / total_buy_qty if total_buy_qty > 0 else 0
    avg_sell_price = total_sell_value / total_sell_qty if total_sell_qty > 0 else 0

    # Calculate realized P&L (simplified - assumes FIFO matching)
    realized_pl = total_sell_value - (total_sell_qty * avg_buy_price) if total_sell_qty > 0 else 0

    # Get strategies involved
    all_strategies = set()
    for trade in trades:
        all_strategies.update(trade["strategy_names"])

    return {
        "total_trades": len(trades),
        "buy_trades": len(buy_trades),
        "sell_trades": len(sell_trades),
        "total_buy_qty": total_buy_qty,
        "total_sell_qty": total_sell_qty,
        "net_qty": total_buy_qty - total_sell_qty,
        "total_buy_value": total_buy_value,
        "total_sell_value": total_sell_value,
        "avg_buy_price": avg_buy_price,
        "avg_sell_price": avg_sell_price,
        "realized_pl": realized_pl,
        "strategies": sorted(list(all_strategies)),
        "first_trade_date": trades[0]["fill_timestamp"][:10] if trades else "N/A",
        "last_trade_date": trades[-1]["fill_timestamp"][:10] if trades else "N/A",
    }


def show() -> None:
    """Display the symbol analytics page."""
    st.title("📈 Symbol Analytics")
    st.caption("Detailed performance analytics for individual symbols")

    # Symbol selector
    symbols = get_all_traded_symbols()

    if not symbols:
        st.warning("No traded symbols found")
        return

    selected_symbol = st.selectbox("Select Symbol", symbols)

    st.divider()

    # Load data for selected symbol
    trades = get_symbol_trades(selected_symbol)
    position = get_current_position(selected_symbol)
    metrics = calculate_symbol_metrics(trades)

    if not trades:
        st.warning(f"No trade history found for {selected_symbol}")
        return

    # Current Position
    st.subheader("💼 Current Position")

    if position:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Quantity", f"{position['qty']:.4f}")
        with col2:
            st.metric("Market Value", f"${position['market_value']:,.2f}")
        with col3:
            st.metric("Avg Entry", f"${position['avg_entry_price']:.2f}")
        with col4:
            st.metric("Current Price", f"${position['current_price']:.2f}")
        with col5:
            unrealized_plpc = position['unrealized_plpc'] * 100
            st.metric(
                "Unrealized P&L",
                f"${position['unrealized_pl']:+,.2f}",
                delta=f"{unrealized_plpc:+.2f}%",
            )
    else:
        st.info("No current position")

    st.divider()

    # Trading Metrics
    st.subheader("📊 Trading Metrics")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Trades", metrics["total_trades"])
    with col2:
        st.metric("BUY Trades", metrics["buy_trades"])
    with col3:
        st.metric("SELL Trades", metrics["sell_trades"])
    with col4:
        st.metric("Net Qty", f"{metrics['net_qty']:.4f}")
    with col5:
        st.metric("Avg Buy Price", f"${metrics['avg_buy_price']:.2f}")
    with col6:
        st.metric("Avg Sell Price", f"${metrics['avg_sell_price']:.2f}")

    st.divider()

    # P&L Metrics
    st.subheader("💰 P&L Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Buy Value", f"${metrics['total_buy_value']:,.2f}")
    with col2:
        st.metric("Total Sell Value", f"${metrics['total_sell_value']:,.2f}")
    with col3:
        realized_pl = metrics['realized_pl']
        st.metric("Realized P&L (Est.)", f"${realized_pl:+,.2f}")

    st.divider()

    # Strategy Attribution
    st.subheader("🎯 Strategy Attribution")

    if metrics["strategies"]:
        st.write(f"**Strategies involved:** {', '.join(metrics['strategies'])}")

        # Count trades per strategy
        strategy_counts = {}
        for trade in trades:
            for strategy in trade["strategy_names"]:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        strategy_df = pd.DataFrame([
            {"Strategy": strategy, "Trade Count": count}
            for strategy, count in strategy_counts.items()
        ]).sort_values("Trade Count", ascending=False)

        st.dataframe(strategy_df, use_container_width=True, hide_index=True)
    else:
        st.info("No strategy attribution available")

    st.divider()

    # Trade History
    st.subheader("📋 Trade History")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**First Trade:** {metrics['first_trade_date']}")
    with col2:
        st.write(f"**Last Trade:** {metrics['last_trade_date']}")

    # Create trades DataFrame
    df = pd.DataFrame([
        {
            "Date": t["fill_timestamp"][:10],
            "Time": t["fill_timestamp"][11:19],
            "Direction": t["direction"],
            "Qty": t["filled_qty"],
            "Price": t["fill_price"],
            "Value": t["filled_qty"] * t["fill_price"],
            "Strategies": ", ".join(t["strategy_names"][:2]) + ("..." if len(t["strategy_names"]) > 2 else ""),
        }
        for t in trades
    ])

    st.dataframe(
        df.style.format({
            "Qty": "{:.4f}",
            "Price": "${:.2f}",
            "Value": "${:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # Price Chart
    st.subheader("📈 Trade Price History")

    # Create price series
    price_data = pd.DataFrame([
        {
            "Timestamp": pd.to_datetime(t["fill_timestamp"]),
            "Price": t["fill_price"],
            "Direction": t["direction"],
        }
        for t in trades
    ])

    # Separate buy and sell prices for different colors
    buy_prices = price_data[price_data["Direction"] == "BUY"].set_index("Timestamp")["Price"]
    sell_prices = price_data[price_data["Direction"] == "SELL"].set_index("Timestamp")["Price"]

    # Combine for display
    chart_df = pd.DataFrame({
        "BUY": buy_prices,
        "SELL": sell_prices,
    })

    st.line_chart(chart_df, use_container_width=True)

    st.divider()

    # Cumulative Quantity Chart
    st.subheader("📦 Cumulative Position")

    # Calculate cumulative quantity
    cumulative_qty = []
    running_qty = 0.0

    for trade in trades:
        if trade["direction"] == "BUY":
            running_qty += trade["filled_qty"]
        elif trade["direction"] == "SELL":
            running_qty -= trade["filled_qty"]

        cumulative_qty.append({
            "Timestamp": pd.to_datetime(trade["fill_timestamp"]),
            "Cumulative Qty": running_qty,
        })

    qty_df = pd.DataFrame(cumulative_qty).set_index("Timestamp")
    st.line_chart(qty_df["Cumulative Qty"], use_container_width=True)

    # Footer
    st.caption(f"Data for {selected_symbol}. Auto-refreshes every 60 seconds.")
