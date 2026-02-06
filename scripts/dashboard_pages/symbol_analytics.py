#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Symbol Analytics page with detailed per-symbol performance metrics.
"""

from __future__ import annotations

from typing import Any

import _setup_imports  # noqa: F401
import boto3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from boto3.dynamodb.conditions import Attr

from dashboard_settings import get_dashboard_settings

from .components import (
    direction_styled_dataframe,
    hero_metric,
    metric_card,
    metric_row,
    section_header,
    styled_dataframe,
)
from .styles import format_currency, format_percent, get_colors, inject_styles

from . import data_access


@st.cache_data(ttl=60)
def get_all_traded_symbols() -> list[str]:
    """Get list of all symbols that have been traded."""
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
    settings = get_dashboard_settings()
    if not settings.has_aws_credentials():
        return []  # Error already shown by get_all_traded_symbols
    
    try:
        dynamodb = boto3.client("dynamodb", **settings.get_boto3_client_kwargs())
        table_name = settings.trade_ledger_table

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

            # Note: Numeric fields stored as strings in DynamoDB for this table
            # This matches the implementation in dynamodb_trade_ledger_repository.py
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


@st.cache_data(ttl=300)
def get_current_position(symbol: str) -> dict | None:
    """Get current position for a symbol from DynamoDB."""
    try:
        positions = data_access.get_latest_positions()

        for pos in positions:
            if pos.symbol == symbol:
                return {
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "current_price": float(pos.current_price),
                    "market_value": float(pos.market_value),
                    "cost_basis": float(pos.cost_basis),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
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
    # Inject styles
    inject_styles()

    st.title("Symbol Analytics")
    st.caption("Detailed performance analytics for individual symbols")

    # Symbol selector
    symbols = get_all_traded_symbols()

    if not symbols:
        st.warning("No traded symbols found")
        return

    selected_symbol = st.selectbox("Select Symbol", symbols)

    # Load data for selected symbol
    trades = get_symbol_trades(selected_symbol)
    position = get_current_position(selected_symbol)
    metrics = calculate_symbol_metrics(trades)

    if not trades:
        st.warning(f"No trade history found for {selected_symbol}")
        return

    # =========================================================================
    # SYMBOL HERO with inline stats
    # =========================================================================
    if position:
        hero_metric(
            label=selected_symbol,
            value=format_currency(position["market_value"]),
            subtitle=f"{position['qty']:.4f} shares @ {format_currency(position['current_price'])} | "
                     f"Unrealized: {format_currency(position['unrealized_pl'], include_sign=True)} "
                     f"({format_percent(position['unrealized_plpc'] * 100, include_sign=True)})",
        )
    else:
        hero_metric(
            label=selected_symbol,
            value="No Position",
            subtitle=f"First trade: {metrics.get('first_trade_date', 'N/A')} | "
                     f"Last trade: {metrics.get('last_trade_date', 'N/A')}",
        )

    # =========================================================================
    # TRADING METRICS ROW
    # =========================================================================
    metric_row([
        {"label": "Total Trades", "value": str(metrics.get("total_trades", 0))},
        {"label": "BUY / SELL", "value": f"{metrics.get('buy_trades', 0)} / {metrics.get('sell_trades', 0)}"},
        {"label": "Net Qty", "value": f"{metrics.get('net_qty', 0):.4f}"},
        {"label": "Avg Buy", "value": format_currency(metrics.get("avg_buy_price", 0))},
        {"label": "Avg Sell", "value": format_currency(metrics.get("avg_sell_price", 0))},
    ])

    # =========================================================================
    # P&L METRICS
    # =========================================================================
    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card("Total Buy Value", format_currency(metrics.get("total_buy_value", 0)))
    with col2:
        metric_card("Total Sell Value", format_currency(metrics.get("total_sell_value", 0)))
    with col3:
        realized_pl = metrics.get("realized_pl", 0)
        metric_card(
            "Realized P&L (Est.)",
            format_currency(realized_pl, include_sign=True),
            delta_positive=realized_pl > 0 if realized_pl != 0 else None,
        )

    # =========================================================================
    # TABBED CHARTS: Price History | Position | Trade History
    # =========================================================================
    tab_price, tab_position, tab_trades, tab_strategy = st.tabs([
        "📈 Price History",
        "📊 Position",
        "📋 Trades",
        "🎯 Strategy Attribution",
    ])

    with tab_price:
        section_header("Trade Price History")

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

        fig = go.Figure()
        if not buy_prices.empty:
            fig.add_trace(go.Scatter(
                x=buy_prices.index,
                y=buy_prices.values,
                mode="markers",
                name="BUY",
                marker=dict(color="#4CAF50", size=8),
                hovertemplate="Date: %{x|%b %d, %Y}<br>Buy Price: $%{y:.2f}<extra></extra>",
            ))
        if not sell_prices.empty:
            fig.add_trace(go.Scatter(
                x=sell_prices.index,
                y=sell_prices.values,
                mode="markers",
                name="SELL",
                marker=dict(color="#F44336", size=8),
                hovertemplate="Date: %{x|%b %d, %Y}<br>Sell Price: $%{y:.2f}<extra></extra>",
            ))
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title=""),
            yaxis=dict(title="Price ($)", tickformat="$.2f"),
            hovermode="closest",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_position:
        section_header("Cumulative Position Over Time")

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
        fig_qty = go.Figure()
        fig_qty.add_trace(go.Scatter(
            x=qty_df.index,
            y=qty_df["Cumulative Qty"],
            mode="lines",
            fill="tozeroy",
            line=dict(color="#7CF5D4", width=2),
            hovertemplate="Date: %{x|%b %d, %Y}<br>Qty: %{y:.4f}<extra></extra>",
        ))
        fig_qty.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title=""),
            yaxis=dict(title="Quantity"),
            hovermode="x unified",
            showlegend=False,
        )
        st.plotly_chart(fig_qty, use_container_width=True)

        # Current position details
        if position:
            section_header("Current Position")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                metric_card("Quantity", f"{position['qty']:.4f}")
            with col2:
                metric_card("Avg Entry", format_currency(position["avg_entry_price"]))
            with col3:
                metric_card("Current Price", format_currency(position["current_price"]))
            with col4:
                metric_card("Cost Basis", format_currency(position["cost_basis"]))

    with tab_trades:
        section_header("Trade History")

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

        direction_styled_dataframe(
            df,
            formats={
                "Qty": "{:.4f}",
                "Price": "${:.2f}",
                "Value": "${:,.2f}",
            },
        )

    with tab_strategy:
        section_header("Strategy Attribution")

        if metrics.get("strategies"):
            # Count trades per strategy
            strategy_counts = {}
            strategy_values = {}
            for trade in trades:
                trade_value = trade["filled_qty"] * trade["fill_price"]
                for strategy in trade["strategy_names"]:
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                    strategy_values[strategy] = strategy_values.get(strategy, 0) + trade_value

            strategy_df = pd.DataFrame([
                {
                    "Strategy": strategy,
                    "Trade Count": strategy_counts[strategy],
                    "Total Value": strategy_values[strategy],
                }
                for strategy in strategy_counts
            ]).sort_values("Total Value", ascending=False)

            styled_dataframe(
                strategy_df,
                formats={"Total Value": "${:,.2f}"},
            )

            # Horizontal bar chart for strategy attribution
            st.subheader("Trade Value by Strategy")
            fig_strat = go.Figure()
            fig_strat.add_trace(go.Bar(
                y=strategy_df["Strategy"],
                x=strategy_df["Total Value"],
                orientation="h",
                marker_color="#7CF5D4",
                hovertemplate="%{y}<br>Value: $%{x:,.2f}<extra></extra>",
            ))
            fig_strat.update_layout(
                height=max(200, len(strategy_df) * 30),
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(title="Total Value ($)", tickformat="$,.0f"),
                yaxis=dict(title=""),
                showlegend=False,
            )
            st.plotly_chart(fig_strat, use_container_width=True)
        else:
            st.info("No strategy attribution available")

    # Footer
    st.caption(f"Data for {selected_symbol}. Auto-refreshes every 60 seconds.")
