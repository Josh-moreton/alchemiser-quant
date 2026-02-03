#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Last Run Analysis page showing the most recent workflow execution details.

Uses CloudWatch Logs to find workflows (like fetch_workflow_logs.py CLI),
then enriches with DynamoDB data for signals/plans/trades.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import _setup_imports  # noqa: F401
import boto3
import pandas as pd
import streamlit as st
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from dashboard_settings import debug_secrets_info, get_dashboard_settings

from .components import (
    alert_box,
    direction_styled_dataframe,
    hero_metric,
    metric_card,
    metric_row,
    pipeline_status,
    section_header,
    styled_dataframe,
)
from .styles import format_currency, get_colors, inject_styles

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Lambda function names (without stage prefix) - same as CLI script
LAMBDA_FUNCTIONS = [
    "strategy-orchestrator",
    "strategy-worker",
    "signal-aggregator",
    "portfolio",
    "execution",
    "trade-aggregator",
    "notifications",
    "metrics",
    "data",
]

# Log levels considered errors
ERROR_LEVELS = {"error", "warning", "critical", "fatal"}


# =============================================================================
# CloudWatch Logs Functions
# =============================================================================


@st.cache_data(ttl=120, show_spinner="Finding recent workflows in CloudWatch...")
def find_recent_workflows(
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    stage: str = "prod",
    hours_back: int = 72,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], str | None]:
    """Find recent workflow runs from CloudWatch Logs.
    
    Scans the strategy-orchestrator log group for correlation_ids.
    Returns (workflows, error_message).
    """
    kwargs: dict[str, Any] = {"region_name": aws_region}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    
    try:
        logs_client = boto3.client("logs", **kwargs)
        orchestrator_log_group = f"/aws/lambda/alchemiser-{stage}-strategy-orchestrator"
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        workflows: dict[str, dict[str, Any]] = {}
        
        # Search for logs with correlation_id
        filter_patterns = [
            '{ $.extra.correlation_id = * }',
            '{ $.correlation_id = * }',
            '"workflow-"',
            '"schedule-"',
        ]
        
        for filter_pattern in filter_patterns:
            try:
                response = logs_client.filter_log_events(
                    logGroupName=orchestrator_log_group,
                    startTime=start_ms,
                    endTime=end_ms,
                    filterPattern=filter_pattern,
                    limit=500,
                )
                
                for event in response.get("events", []):
                    try:
                        message = json.loads(event["message"])
                        extra = message.get("extra", {})
                        cid = extra.get("correlation_id", "") or message.get("correlation_id", "")
                        
                        if cid and (cid.startswith("workflow-") or cid.startswith("schedule-")):
                            ts = event["timestamp"]
                            if cid not in workflows or ts > workflows[cid]["timestamp_ms"]:
                                workflows[cid] = {
                                    "correlation_id": cid,
                                    "timestamp_ms": ts,
                                    "timestamp": datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
                                }
                    except json.JSONDecodeError:
                        raw = event.get("message", "")
                        match = re.search(r'(?:workflow|schedule)-[a-f0-9-]+', raw)
                        if match:
                            cid = match.group(0)
                            ts = event["timestamp"]
                            if cid not in workflows or ts > workflows[cid]["timestamp_ms"]:
                                workflows[cid] = {
                                    "correlation_id": cid,
                                    "timestamp_ms": ts,
                                    "timestamp": datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
                                }
                
                if workflows:
                    break  # Found workflows, no need to try more patterns
                    
            except ClientError as e:
                if "ResourceNotFoundException" in str(e):
                    return [], f"Log group not found: {orchestrator_log_group}"
                continue
        
        # Sort by timestamp descending and return top N
        sorted_workflows = sorted(
            workflows.values(),
            key=lambda x: x["timestamp_ms"],
            reverse=True,
        )
        return sorted_workflows[:limit], None
        
    except ClientError as e:
        return [], f"CloudWatch Error: {e}"
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"


@st.cache_data(ttl=60, show_spinner="Fetching workflow logs from all Lambdas...")
def fetch_workflow_logs(
    correlation_id: str,
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    stage: str = "prod",
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Fetch all logs for a workflow from all Lambda log groups.
    
    Returns (events, lambda_counts).
    """
    kwargs: dict[str, Any] = {"region_name": aws_region}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    
    logs_client = boto3.client("logs", **kwargs)
    log_groups = [f"/aws/lambda/alchemiser-{stage}-{fn}" for fn in LAMBDA_FUNCTIONS]
    
    # Search last 48 hours
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=48)
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    
    all_events: list[dict[str, Any]] = []
    lambda_counts: dict[str, int] = {}
    
    for log_group in log_groups:
        lambda_name = log_group.split("/")[-1].replace(f"alchemiser-{stage}-", "")
        count = 0
        
        try:
            paginator = logs_client.get_paginator("filter_log_events")
            
            for page in paginator.paginate(
                logGroupName=log_group,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern=f'"{correlation_id}"',
            ):
                for event in page.get("events", []):
                    count += 1
                    try:
                        message = json.loads(event["message"])
                        message["_lambda_name"] = lambda_name
                        message["_timestamp_ms"] = event["timestamp"]
                        message["_timestamp"] = datetime.fromtimestamp(
                            event["timestamp"] / 1000, tz=timezone.utc
                        )
                        message["_is_json"] = True
                        all_events.append(message)
                    except json.JSONDecodeError:
                        all_events.append({
                            "_lambda_name": lambda_name,
                            "_timestamp_ms": event["timestamp"],
                            "_timestamp": datetime.fromtimestamp(
                                event["timestamp"] / 1000, tz=timezone.utc
                            ),
                            "_raw_message": event["message"][:500],
                            "_is_json": False,
                        })
            
            lambda_counts[lambda_name] = count
                        
        except Exception:
            lambda_counts[lambda_name] = 0
            continue  # Skip log groups that don't exist or have errors
    
    # Sort by timestamp
    all_events.sort(key=lambda x: x.get("_timestamp_ms", 0))
    return all_events, lambda_counts


def is_error_event(event: dict[str, Any]) -> bool:
    """Check if an event is an error/warning."""
    level = event.get("level", "").lower()
    if level in ERROR_LEVELS:
        return True
    if event.get("error") or event.get("exception"):
        return True
    return False


# =============================================================================
# DynamoDB Functions (for enrichment)
# =============================================================================


@st.cache_data(ttl=60)
def get_rebalance_plan(
    correlation_id: str,
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    stage: str = "prod",
) -> dict[str, Any] | None:
    """Get rebalance plan for a correlation ID from DynamoDB."""
    kwargs: dict[str, Any] = {"region_name": aws_region}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    
    table_name = f"alchemiser-{stage}-rebalance-plans"
    
    try:
        dynamodb = boto3.client("dynamodb", **kwargs)
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
        plan_data_str = item.get("plan_data", {}).get("S", "{}")
        return json.loads(plan_data_str)

    except Exception:
        return None


@st.cache_data(ttl=60)
def get_trades_for_correlation(
    correlation_id: str,
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    stage: str = "prod",
) -> list[dict[str, Any]]:
    """Get trades for a correlation ID from DynamoDB."""
    kwargs: dict[str, Any] = {"region_name": aws_region}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    
    table_name = f"alchemiser-{stage}-trade-ledger"
    
    try:
        dynamodb = boto3.client("dynamodb", **kwargs)
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

            trades.append({
                "order_id": item.get("order_id", {}).get("S", ""),
                "symbol": item.get("symbol", {}).get("S", ""),
                "direction": item.get("direction", {}).get("S", ""),
                "filled_qty": float(item.get("filled_qty", {}).get("S", "0")),
                "fill_price": float(item.get("fill_price", {}).get("S", "0")),
                "fill_timestamp": item.get("fill_timestamp", {}).get("S", ""),
            })

        trades.sort(key=lambda x: x["fill_timestamp"])
        return trades

    except Exception:
        return []


@st.cache_data(ttl=60)
def get_aggregated_signal(
    correlation_id: str,
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    stage: str = "prod",
) -> dict[str, Any] | None:
    """Get aggregated signal from DynamoDB."""
    kwargs: dict[str, Any] = {"region_name": aws_region}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    
    table_name = f"alchemiser-{stage}-aggregation-sessions"
    
    try:
        dynamodb = boto3.client("dynamodb", **kwargs)
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"SESSION#{correlation_id}"}},
            Limit=1,
        )

        if not response.get("Items"):
            return None

        item = response["Items"][0]
        merged_signal_str = item.get("merged_signal", {}).get("S")
        if merged_signal_str:
            return json.loads(merged_signal_str)

        return None

    except Exception:
        return None


# =============================================================================
# Display Functions
# =============================================================================


def show_workflow_summary(events: list[dict[str, Any]], lambda_counts: dict[str, int]) -> None:
    """Display workflow execution summary with pipeline visualization."""
    if not events:
        return

    # Calculate metrics
    first_ts = events[0]["_timestamp"]
    last_ts = events[-1]["_timestamp"]
    duration = last_ts - first_ts

    error_count = sum(1 for e in events if is_error_event(e))

    # Level breakdown
    level_counts: dict[str, int] = {}
    for event in events:
        level = event.get("level", "unknown").lower()
        level_counts[level] = level_counts.get(level, 0) + 1

    # Build pipeline steps from lambda counts
    pipeline_steps = []
    expected_order = [
        "strategy-orchestrator",
        "strategy-worker",
        "signal-aggregator",
        "portfolio",
        "execution",
        "trade-aggregator",
        "notifications",
    ]

    for lambda_name in expected_order:
        count = lambda_counts.get(lambda_name, 0)
        if count > 0:
            # Check if there were errors in this lambda
            lambda_errors = sum(
                1 for e in events
                if e.get("_lambda_name") == lambda_name and is_error_event(e)
            )
            status = "error" if lambda_errors > 0 else "complete"
        else:
            status = "pending"

        pipeline_steps.append({"name": lambda_name.replace("-", " ").title(), "status": status})

    section_header("Pipeline Status")
    pipeline_status(pipeline_steps)

    # Summary metrics row
    metric_row([
        {"label": "Total Events", "value": f"{len(events):,}"},
        {"label": "Duration", "value": f"{duration.total_seconds():.1f}s"},
        {
            "label": "Errors/Warnings",
            "value": str(error_count),
            "delta_positive": error_count == 0,
        },
        {"label": "Lambdas Active", "value": str(sum(1 for c in lambda_counts.values() if c > 0))},
    ])


def show_logs_timeline(events: list[dict[str, Any]], show_all: bool = False) -> None:
    """Display logs timeline."""
    st.subheader("Logs Timeline")
    
    if show_all:
        display_events = events
    else:
        display_events = [e for e in events if is_error_event(e)]
        if not display_events:
            st.success("No errors or warnings in this workflow run!")
            with st.expander("Show all logs"):
                show_logs_timeline(events, show_all=True)
            return
    
    # Convert to DataFrame for display
    rows = []
    for event in display_events[-100:]:  # Limit to last 100
        ts = event["_timestamp"]
        level = event.get("level", "?").upper()
        lambda_name = event.get("_lambda_name", "?")
        
        if event.get("_is_json", True):
            message = event.get("event", "")[:200]
            module = event.get("module", "")
        else:
            message = event.get("_raw_message", "")[:200]
            module = ""
        
        rows.append({
            "Time": ts.strftime("%H:%M:%S.%f")[:-3],
            "Lambda": lambda_name,
            "Level": level,
            "Module": module,
            "Message": message,
        })
    
    df = pd.DataFrame(rows)
    
    # Style based on level
    def style_level(val: str) -> str:
        if val in ("ERROR", "CRITICAL", "FATAL"):
            return "color: red; font-weight: bold"
        elif val == "WARNING":
            return "color: orange"
        elif val == "INFO":
            return "color: green"
        return "color: gray"
    
    styled_df = df.style.map(style_level, subset=["Level"])
    st.dataframe(styled_df, width="stretch", hide_index=True, height=400)
    
    if len(events) > 100:
        st.caption(f"Showing last 100 of {len(display_events)} events")


def show_signal_analysis(signal: dict[str, Any]) -> None:
    """Display signal analysis with bar chart for allocation."""
    allocations = signal.get("allocations") or signal.get("target_allocations") or {}

    if not allocations:
        alert_box("No allocations found in signal", alert_type="warning")
        return

    df = pd.DataFrame([
        {"Symbol": symbol, "Weight": float(weight) * 100}
        for symbol, weight in allocations.items()
    ]).sort_values("Weight", ascending=False)

    total_weight = sum(float(v) for v in allocations.values()) * 100

    # Summary metrics
    metric_row([
        {"label": "Total Symbols", "value": str(len(allocations))},
        {"label": "Total Weight", "value": f"{total_weight:.1f}%"},
        {
            "label": "Status",
            "value": "Balanced" if 99 <= total_weight <= 101 else (
                "Over-allocated" if total_weight > 101 else "Under-allocated"
            ),
            "delta_positive": 99 <= total_weight <= 101,
        },
    ])

    # Allocation bar chart
    st.subheader("Target Allocations")
    st.bar_chart(df.set_index("Symbol")["Weight"], width="stretch", height=300)

    # Allocation table
    with st.expander("Allocation Details"):
        styled_dataframe(
            df,
            formats={"Weight": "{:.2f}%"},
        )


def show_rebalance_plan_analysis(plan: dict[str, Any]) -> None:
    """Display rebalance plan analysis."""
    metadata = plan.get("metadata", {})
    portfolio_value = metadata.get("portfolio_value", plan.get("total_portfolio_value", 0))
    cash_balance = metadata.get("cash_balance", 0)

    items = plan.get("items", [])
    buys = [i for i in items if i.get("action") == "BUY"]
    sells = [i for i in items if i.get("action") == "SELL"]
    holds = [i for i in items if i.get("action") == "HOLD"]

    total_buy = sum(Decimal(str(i.get("trade_amount", 0))) for i in buys)
    total_sell = sum(abs(Decimal(str(i.get("trade_amount", 0)))) for i in sells)

    # Summary metrics
    metric_row([
        {"label": "Portfolio Value", "value": format_currency(float(portfolio_value))},
        {"label": "Cash Balance", "value": format_currency(float(cash_balance))},
        {"label": "BUY Orders", "value": str(len(buys)), "delta": format_currency(float(total_buy)), "delta_positive": True},
        {"label": "SELL Orders", "value": str(len(sells)), "delta": format_currency(float(total_sell)), "delta_positive": False},
    ])

    # Plan details table
    if items:
        st.subheader("Plan Items")
        plan_df = pd.DataFrame([
            {
                "Symbol": i.get("symbol", ""),
                "Action": i.get("action", ""),
                "Current %": float(i.get("current_weight", 0)) * 100,
                "Target %": float(i.get("target_weight", 0)) * 100,
                "Trade Amount": float(i.get("trade_amount", 0)),
            }
            for i in items
            if i.get("action") != "HOLD"  # Only show actionable items
        ])

        if not plan_df.empty:
            direction_styled_dataframe(
                plan_df,
                direction_col="Action",
                formats={
                    "Current %": "{:.2f}%",
                    "Target %": "{:.2f}%",
                    "Trade Amount": "${:+,.2f}",
                },
            )


def show_trades_analysis(trades: list[dict[str, Any]]) -> None:
    """Display trades analysis."""
    buy_trades = [t for t in trades if t["direction"] == "BUY"]
    sell_trades = [t for t in trades if t["direction"] == "SELL"]
    total_value = sum(t["filled_qty"] * t["fill_price"] for t in trades)

    # Summary metrics
    metric_row([
        {"label": "Total Trades", "value": str(len(trades))},
        {"label": "BUY / SELL", "value": f"{len(buy_trades)} / {len(sell_trades)}"},
        {"label": "Total Value", "value": format_currency(total_value)},
    ])

    # Trades table
    df = pd.DataFrame([
        {
            "Symbol": t["symbol"],
            "Direction": t["direction"],
            "Qty": t["filled_qty"],
            "Price": t["fill_price"],
            "Value": t["filled_qty"] * t["fill_price"],
            "Time": t["fill_timestamp"][:19],
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


# =============================================================================
# Main Page
# =============================================================================


def show() -> None:
    """Display the last run analysis page."""
    # Inject styles
    inject_styles()

    st.title("Last Run Analysis")
    st.caption("Detailed view of the most recent workflow execution from CloudWatch Logs")

    settings = get_dashboard_settings()

    # Debug expander (collapsed by default at bottom)
    # Check credentials
    if not settings.has_aws_credentials():
        alert_box(
            "AWS credentials not configured. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in Streamlit secrets.",
            alert_type="error",
            icon="🔐",
        )
        return

    # Find recent workflows from CloudWatch
    workflows, error = find_recent_workflows(
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        stage=settings.stage,
        hours_back=72,
        limit=20,
    )

    if error:
        alert_box(f"Error finding workflows: {error}", alert_type="error")
        return

    if not workflows:
        alert_box(
            f"No workflow runs found in the last 72 hours for stage '{settings.stage}'. "
            "Check that workflows have run and logs exist in CloudWatch.",
            alert_type="warning",
            icon="⚠️",
        )
        return

    # =========================================================================
    # WORKFLOW SELECTOR
    # =========================================================================
    col_select, col_info = st.columns([3, 1])

    with col_select:
        workflow_options = [
            f"{w['correlation_id'][:30]}... - {w['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} UTC"
            for w in workflows
        ]
        selected_idx = st.selectbox(
            "Select Workflow Run",
            range(len(workflow_options)),
            format_func=lambda i: workflow_options[i],
        )

    selected_workflow = workflows[selected_idx]
    correlation_id = selected_workflow["correlation_id"]

    with col_info:
        st.caption(f"Found {len(workflows)} runs")

    # =========================================================================
    # WORKFLOW HERO
    # =========================================================================
    hero_metric(
        label="Correlation ID",
        value=correlation_id[:25] + "...",
        subtitle=f"Started: {selected_workflow['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}",
    )

    # =========================================================================
    # FETCH DATA
    # =========================================================================
    events, lambda_counts = fetch_workflow_logs(
        correlation_id=correlation_id,
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        stage=settings.stage,
    )

    signal = get_aggregated_signal(
        correlation_id=correlation_id,
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        stage=settings.stage,
    )

    plan = get_rebalance_plan(
        correlation_id=correlation_id,
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        stage=settings.stage,
    )

    trades = get_trades_for_correlation(
        correlation_id=correlation_id,
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        stage=settings.stage,
    )

    # =========================================================================
    # PIPELINE STATUS VISUALIZATION
    # =========================================================================
    if events:
        show_workflow_summary(events, lambda_counts)

    # =========================================================================
    # TABBED INTERFACE: Logs | Signal | Plan | Trades
    # =========================================================================
    tab_logs, tab_signal, tab_plan, tab_trades, tab_raw = st.tabs([
        "📋 Logs",
        "📊 Signal",
        "📝 Plan",
        "💰 Trades",
        "🔧 Raw Data",
    ])

    with tab_logs:
        if events:
            show_all = st.checkbox("Show all logs (not just errors/warnings)", value=False)
            show_logs_timeline(events, show_all=show_all)
        else:
            st.info("No log events found for this workflow")

    with tab_signal:
        if signal:
            show_signal_analysis(signal)
        else:
            st.info("No aggregated signal found in DynamoDB")

    with tab_plan:
        if plan:
            show_rebalance_plan_analysis(plan)
        else:
            st.info("No rebalance plan found in DynamoDB")

    with tab_trades:
        if trades:
            show_trades_analysis(trades)
        else:
            st.info("No trades found for this run")

    with tab_raw:
        st.subheader("Raw Signal Data")
        st.json(signal or {})

        st.subheader("Raw Plan Data")
        st.json(plan or {})

        st.subheader("Sample Log Events")
        st.json([e for e in events[:10]] if events else [])

    # Debug config collapsed at bottom
    with st.expander("Debug: Configuration", expanded=False):
        debug_info = debug_secrets_info()
        st.text(f"Stage: {settings.stage}")
        st.text(f"AWS Region: {settings.aws_region}")
        st.text(f"Has credentials: {settings.has_aws_credentials()}")
        if settings.aws_access_key_id:
            st.text(f"Access key (first 4 chars): {settings.aws_access_key_id[:4]}...")
        for key, value in debug_info.items():
            st.text(f"  {key}: {value}")
