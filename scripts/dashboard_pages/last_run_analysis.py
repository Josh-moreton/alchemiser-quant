#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Last Run Analysis page showing the most recent workflow execution details.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import _setup_imports  # noqa: F401
import boto3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from dashboard_settings import get_dashboard_settings

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_recent_sessions(limit: int = 10) -> list[dict[str, Any]]:
    """Get recent aggregation sessions from DynamoDB."""
    settings = get_dashboard_settings()
    table_name = settings.aggregation_sessions_table
    
    try:
        dynamodb = boto3.client("dynamodb", region_name=settings.aws_region)

        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression="SK = :sk",
            ExpressionAttributeValues={":sk": {"S": "METADATA"}},
            Limit=50,  # Get more to filter and sort
        )

        sessions = []
        for item in response.get("Items", []):
            session_id = item.get("session_id", {}).get("S", "")
            correlation_id = item.get("correlation_id", {}).get("S", "")
            status = item.get("status", {}).get("S", "")
            created_at = item.get("created_at", {}).get("S", "")
            total_strategies = int(item.get("total_strategies", {}).get("N", 0))
            completed_strategies = int(item.get("completed_strategies", {}).get("N", 0))

            # Get merged signal if available
            merged_signal_str = item.get("merged_signal", {}).get("S")
            merged_signal = json.loads(merged_signal_str) if merged_signal_str else None

            sessions.append({
                "session_id": session_id,
                "correlation_id": correlation_id,
                "status": status,
                "created_at": created_at,
                "total_strategies": total_strategies,
                "completed_strategies": completed_strategies,
                "merged_signal": merged_signal,
            })

        # Sort by created_at descending
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions[:limit]

    except dynamodb.exceptions.ResourceNotFoundException:
        st.error(
            f"DynamoDB table `{table_name}` not found. "
            "Ensure the prod stack is deployed and the table exists."
        )
        return []
    except Exception as e:
        error_msg = str(e)
        if "AccessDenied" in error_msg or "not authorized" in error_msg.lower():
            st.error(
                "AWS credentials lack DynamoDB read permissions. "
                "Check that the IAM user has the AlchemiserDashboardReadOnly policy attached."
            )
        elif "credentials" in error_msg.lower() or "security token" in error_msg.lower():
            st.error(
                "AWS credentials not configured or invalid. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in Streamlit secrets."
            )
        else:
            st.error(f"Error loading sessions: {e}")
        return []


@st.cache_data(ttl=60)
def get_rebalance_plan(correlation_id: str) -> dict[str, Any] | None:
    """Get rebalance plan for a correlation ID."""
    try:
        settings = get_dashboard_settings()
        dynamodb = boto3.client("dynamodb", region_name=settings.aws_region)
        table_name = settings.rebalance_plans_table

        response = dynamodb.query(
            TableName=table_name,
            IndexName="GSI1-CorrelationIndex",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"CORR#{correlation_id}"}},
            Limit=1,
            ScanIndexForward=False,
        )

        if not response.get("Items"):
            return None

        item = response["Items"][0]
        # Note: Numeric fields stored as strings ('S' type) in this table's schema
        # This matches the repository implementation in dynamodb_rebalance_plan_repository.py
        plan_data_str = item.get("plan_data", {}).get("S", "{}")
        return json.loads(plan_data_str)

    except Exception as e:
        st.error(f"Error loading rebalance plan: {e}")
        return None


@st.cache_data(ttl=60)
def get_trades_for_correlation(correlation_id: str) -> list[dict[str, Any]]:
    """Get trades for a correlation ID."""
    try:
        settings = get_dashboard_settings()
        dynamodb = boto3.client("dynamodb", region_name=settings.aws_region)
        table_name = settings.trade_ledger_table

        response = dynamodb.query(
            TableName=table_name,
            IndexName="GSI1-CorrelationIndex",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"CORR#{correlation_id}"}},
        )

        trades = []
        for item in response.get("Items", []):
            if item.get("EntityType", {}).get("S") != "TRADE":
                continue

            order_id = item.get("order_id", {}).get("S", "")
            symbol = item.get("symbol", {}).get("S", "")
            direction = item.get("direction", {}).get("S", "")
            filled_qty = item.get("filled_qty", {}).get("S", "0")
            fill_price = item.get("fill_price", {}).get("S", "0")
            fill_timestamp = item.get("fill_timestamp", {}).get("S", "")
            strategy_names = item.get("strategy_names", {}).get("L", [])

            # Extract strategy names from DynamoDB list
            strategies = [s.get("S", "") for s in strategy_names]

            trades.append({
                "order_id": order_id,
                "symbol": symbol,
                "direction": direction,
                "filled_qty": float(filled_qty),
                "fill_price": float(fill_price),
                "fill_timestamp": fill_timestamp,
                "strategy_names": strategies,
                "trade_value": float(filled_qty) * float(fill_price),
            })

        # Sort by timestamp
        trades.sort(key=lambda x: x["fill_timestamp"])
        return trades

    except Exception as e:
        st.error(f"Error loading trades: {e}")
        return []


def show_signal_analysis(signal: dict[str, Any]) -> None:
    """Display signal analysis."""
    st.subheader("Aggregated Signal")

    allocations = signal.get("allocations") or signal.get("target_allocations") or {}

    if not allocations:
        st.warning("No allocations found in signal")
        return

    # Convert to DataFrame
    df = pd.DataFrame([
        {"Symbol": symbol, "Weight": float(weight) * 100}
        for symbol, weight in allocations.items()
    ]).sort_values("Weight", ascending=False)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    total_weight = sum(float(v) for v in allocations.values()) * 100

    with col1:
        st.metric("Total Symbols", len(allocations))
    with col2:
        st.metric("Total Weight", f"{total_weight:.1f}%")
    with col3:
        if total_weight > 101:
            st.metric("Status", "Over-allocated", delta=f"{total_weight - 100:.1f}%")
        elif total_weight < 99:
            st.metric("Status", "Under-allocated", delta=f"{total_weight - 100:.1f}%")
        else:
            st.metric("Status", "Balanced")

    # Allocations table
    st.dataframe(
        df.style.format({"Weight": "{:.2f}%"}),
        width="stretch",
        hide_index=True,
    )

    # Pie chart
    if len(df) <= 20:  # Only show for reasonable number of symbols
        st.subheader("Allocation Distribution")
        chart_data = df.set_index("Symbol")["Weight"]
        st.bar_chart(chart_data, width="stretch")


def show_rebalance_plan_analysis(plan: dict[str, Any]) -> None:
    """Display rebalance plan analysis."""
    st.subheader("Rebalance Plan")

    # Metadata
    metadata = plan.get("metadata", {})
    portfolio_value = metadata.get("portfolio_value", plan.get("total_portfolio_value", 0))
    cash_balance = metadata.get("cash_balance", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Portfolio Value", f"${float(portfolio_value):,.2f}")
    with col2:
        st.metric("Cash Balance", f"${float(cash_balance):,.2f}")
    with col3:
        total_trade_value = plan.get("total_trade_value", 0)
        st.metric("Total Trade Value", f"${float(total_trade_value):,.2f}")
    with col4:
        st.metric("Plan ID", plan.get("plan_id", "N/A")[:8] + "...")

    items = plan.get("items", [])

    # Separate by action
    buys = [i for i in items if i.get("action") == "BUY"]
    sells = [i for i in items if i.get("action") == "SELL"]
    holds = [i for i in items if i.get("action") == "HOLD"]

    # Summary
    st.subheader("Trade Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        total_buy = sum(Decimal(str(i.get("trade_amount", 0))) for i in buys)
        st.metric("BUY Orders", len(buys), delta=f"${float(total_buy):,.2f}")

    with col2:
        total_sell = sum(abs(Decimal(str(i.get("trade_amount", 0)))) for i in sells)
        st.metric("SELL Orders", len(sells), delta=f"${float(total_sell):,.2f}")

    with col3:
        st.metric("HOLD Positions", len(holds))

    # Show BUY orders
    if buys:
        st.subheader("🟢 BUY Orders")
        buy_df = pd.DataFrame([
            {
                "Symbol": i.get("symbol", "?"),
                "Current $": float(i.get("current_value", 0)),
                "Target $": float(i.get("target_value", 0)),
                "Trade $": float(i.get("trade_amount", 0)),
                "Current %": float(i.get("current_weight", 0)) * 100,
                "Target %": float(i.get("target_weight", 0)) * 100,
            }
            for i in buys
        ]).sort_values("Trade $", ascending=False)

        st.dataframe(
            buy_df.style.format({
                "Current $": "${:,.2f}",
                "Target $": "${:,.2f}",
                "Trade $": "${:,.2f}",
                "Current %": "{:.2f}%",
                "Target %": "{:.2f}%",
            }),
            width="stretch",
            hide_index=True,
        )

    # Show SELL orders
    if sells:
        st.subheader("🔴 SELL Orders")
        sell_df = pd.DataFrame([
            {
                "Symbol": i.get("symbol", "?"),
                "Current $": float(i.get("current_value", 0)),
                "Target $": float(i.get("target_value", 0)),
                "Trade $": float(i.get("trade_amount", 0)),
                "Current %": float(i.get("current_weight", 0)) * 100,
                "Target %": float(i.get("target_weight", 0)) * 100,
            }
            for i in sells
        ]).sort_values("Trade $", ascending=True)

        st.dataframe(
            sell_df.style.format({
                "Current $": "${:,.2f}",
                "Target $": "${:,.2f}",
                "Trade $": "${:,.2f}",
                "Current %": "{:.2f}%",
                "Target %": "{:.2f}%",
            }),
            width="stretch",
            hide_index=True,
        )

    # Show HOLD positions
    if holds:
        with st.expander(f"View {len(holds)} HOLD Positions"):
            hold_df = pd.DataFrame([
                {
                    "Symbol": i.get("symbol", "?"),
                    "Value $": float(i.get("current_value", 0)),
                    "Weight %": float(i.get("current_weight", 0)) * 100,
                }
                for i in holds
            ])

            st.dataframe(
                hold_df.style.format({
                    "Value $": "${:,.2f}",
                    "Weight %": "{:.2f}%",
                }),
                width="stretch",
                hide_index=True,
            )


def show_trades_analysis(trades: list[dict[str, Any]]) -> None:
    """Display trades analysis."""
    st.subheader("📊 Executed Trades")

    if not trades:
        st.info("No trades found for this run")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    total_trades = len(trades)
    buy_trades = [t for t in trades if t["direction"] == "BUY"]
    sell_trades = [t for t in trades if t["direction"] == "SELL"]
    total_value = sum(t["trade_value"] for t in trades)

    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("BUY Trades", len(buy_trades))
    with col3:
        st.metric("SELL Trades", len(sell_trades))
    with col4:
        st.metric("Total Value", f"${total_value:,.2f}")

    # Trades table
    df = pd.DataFrame([
        {
            "Symbol": t["symbol"],
            "Direction": t["direction"],
            "Qty": t["filled_qty"],
            "Price": t["fill_price"],
            "Value": t["trade_value"],
            "Timestamp": t["fill_timestamp"][:19],  # Trim to YYYY-MM-DD HH:MM:SS
            "Strategies": ", ".join(t["strategy_names"][:2]) + ("..." if len(t["strategy_names"]) > 2 else ""),
        }
        for t in trades
    ])

    st.dataframe(
        df.style.format({
            "Price": "${:.2f}",
            "Value": "${:,.2f}",
            "Qty": "{:.4f}",
        }),
        width="stretch",
        hide_index=True,
    )


def show() -> None:
    """Display the last run analysis page."""
    st.title("🎯 Last Run Analysis")
    st.caption("Detailed view of the most recent workflow execution")

    # Load recent sessions
    sessions = get_recent_sessions(limit=20)

    if not sessions:
        st.warning("No recent workflow runs found")
        return

    # Session selector
    session_options = [
        f"{s['correlation_id'][:30]} - {s['status']} - {s['created_at'][:19]}"
        for s in sessions
    ]
    selected_index = st.selectbox("Select Workflow Run", range(len(session_options)), format_func=lambda i: session_options[i])

    selected_session = sessions[selected_index]
    correlation_id = selected_session["correlation_id"]

    st.divider()

    # Session info
    st.subheader("📋 Workflow Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", selected_session["status"])
    with col2:
        st.metric("Strategies", f"{selected_session['completed_strategies']}/{selected_session['total_strategies']}")
    with col3:
        st.metric("Created At", selected_session["created_at"][:19])
    with col4:
        st.metric("Correlation ID", correlation_id[:12] + "...")

    st.divider()

    # Show signal
    if selected_session.get("merged_signal"):
        show_signal_analysis(selected_session["merged_signal"])
        st.divider()

    # Show rebalance plan
    plan = get_rebalance_plan(correlation_id)
    if plan:
        show_rebalance_plan_analysis(plan)
        st.divider()

    # Show trades
    trades = get_trades_for_correlation(correlation_id)
    show_trades_analysis(trades)

    st.divider()

    # Raw data expanders
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("📄 Raw Signal Data"):
            st.json(selected_session.get("merged_signal", {}))

    with col2:
        with st.expander("📄 Raw Plan Data"):
            if plan:
                st.json(plan)
            else:
                st.info("No rebalance plan found")
