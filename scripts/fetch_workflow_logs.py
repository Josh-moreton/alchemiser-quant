#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Fetch CloudWatch logs and workflow data for a complete workflow run.

This script queries all Lambda log groups for a given workflow run, filters for
errors/warnings/failures, presents a chronological timeline of events, and also
fetches the aggregated signal and per-strategy rebalance plans from DynamoDB
for analysis.

Usage:
    # Auto-detect most recent workflow run
    python scripts/fetch_workflow_logs.py

    # Most recent run from production
    python scripts/fetch_workflow_logs.py --stage prod

    # Fetch errors/warnings for a specific workflow run
    python scripts/fetch_workflow_logs.py --correlation-id workflow-abc123

    # Show all logs (not just errors)
    python scripts/fetch_workflow_logs.py --correlation-id workflow-abc123 --all

    # Include raw/debug logs
    python scripts/fetch_workflow_logs.py --correlation-id workflow-abc123 --all --verbose

    # Skip fetching workflow data from DynamoDB (logs only)
    python scripts/fetch_workflow_logs.py --no-data

    # Use session-id alias
    python scripts/fetch_workflow_logs.py --session-id workflow-abc123

    # Output to JSON file
    python scripts/fetch_workflow_logs.py --correlation-id workflow-abc123 --output logs.json

    # Query production environment
    python scripts/fetch_workflow_logs.py --correlation-id workflow-abc123 --stage prod
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# AWS configuration
REGION = "us-east-1"

# Lambda function names (without stage prefix)
LAMBDA_FUNCTIONS = [
    # Core workflow
    "strategy-orchestrator",
    "strategy-worker",
    "execution",
    "trade-aggregator",
    "notifications",
    # Hedge functions
    "hedge-evaluator",
    "hedge-executor",
    "hedge-roll-manager",
    # Data & utility functions
    "data",
    "schedule-manager",
    "account-data",
    "strategy-performance",
]

# Log levels to include when filtering for issues
ERROR_LEVELS = {"error", "warning", "critical", "fatal"}

# Patterns that indicate errors even if level isn't set (word boundaries reduce false positives)
# Note: We use word boundaries (\b) to avoid matching words as substrings (e.g., "0 failures" won't
# match "failure" with boundaries). This is intentional to trust explicit log levels and reduce noise
# from operational logs that contain these words incidentally.
ERROR_PATTERNS = [
    r"\btraceback\b",
    r"\bexception\b",
    r"\berror\b",
    r"\bfailed\b",
    r"\bfailure\b",
    r"\btimeout\b",
    r"\btimed out\b",
]

# ANSI colour codes for terminal output
COLOURS = {
    "reset": "\033[0m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "grey": "\033[90m",
    "bold": "\033[1m",
}


def get_log_groups(stage: str) -> list[str]:
    """Get CloudWatch log group names for the given stage."""
    return [f"/aws/lambda/alch-{stage}-{fn}" for fn in LAMBDA_FUNCTIONS]


def colour(text: str, colour_name: str) -> str:
    """Apply ANSI colour to text."""
    return f"{COLOURS.get(colour_name, '')}{text}{COLOURS['reset']}"


def find_most_recent_workflow(
    logs_client: Any,
    stage: str,
    hours_back: int = 48,
) -> tuple[str, datetime] | None:
    """Find the most recent workflow run from the strategy orchestrator.

    Args:
        logs_client: boto3 CloudWatch Logs client
        stage: Environment stage (dev or prod)
        hours_back: Maximum hours to search back

    Returns:
        Tuple of (correlation_id, timestamp) of the most recent workflow, or None if not found

    """
    orchestrator_log_group = f"/aws/lambda/alch-{stage}-strategy-orchestrator"

    end_time = datetime.now(UTC)
    # Start with a narrow window (last 2 hours) to find recent workflows faster
    # CloudWatch returns events oldest-first, so we search in reverse time order
    search_windows = [
        timedelta(hours=2),
        timedelta(hours=6),
        timedelta(hours=24),
        timedelta(hours=hours_back),
    ]

    print(f"   Searching in {colour(stage.upper(), 'cyan')} environment...")

    for window in search_windows:
        search_start = end_time - window
        start_ms = int(search_start.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        try:
            # Search for any logs with a correlation_id field
            # Try nested path first (structlog format: extra.correlation_id)
            # then fallback to root level and raw string match
            filter_patterns = [
                '{ $.extra.correlation_id = * }',
                '{ $.correlation_id = * }',
                '"workflow-"',  # Fallback: raw string match
                '"schedule-"',  # Fallback: scheduled runs
            ]

            events = []
            for filter_pattern in filter_patterns:
                try:
                    response = logs_client.filter_log_events(
                        logGroupName=orchestrator_log_group,
                        startTime=start_ms,
                        endTime=end_ms,
                        filterPattern=filter_pattern,
                        limit=500,  # Higher limit to ensure we capture recent events
                    )
                    events = response.get("events", [])
                    if events:
                        break  # Found events, no need to try more patterns
                except ClientError:
                    continue  # Try next filter pattern

            if not events:
                # No events in this window, try a larger window
                continue

            # Parse events and find unique correlation_ids, taking the most recent
            correlation_ids: dict[str, int] = {}  # correlation_id -> timestamp
            for event in events:
                try:
                    message = json.loads(event["message"])
                    # Check nested extra field first (structlog format), then root level
                    extra = message.get("extra", {})
                    cid = extra.get("correlation_id", "") or message.get("correlation_id", "")
                    if cid and (cid.startswith("workflow-") or cid.startswith("schedule-")):
                        ts = event["timestamp"]
                        if cid not in correlation_ids or ts > correlation_ids[cid]:
                            correlation_ids[cid] = ts
                except json.JSONDecodeError:
                    # Try to extract from raw message
                    raw = event.get("message", "")
                    match = re.search(r'(?:workflow|schedule)-[a-f0-9-]+', raw)
                    if match:
                        cid = match.group(0)
                        ts = event["timestamp"]
                        if cid not in correlation_ids or ts > correlation_ids[cid]:
                            correlation_ids[cid] = ts

            if correlation_ids:
                # Return the most recent one (correlation_id, timestamp)
                most_recent = max(correlation_ids.items(), key=lambda x: x[1])
                workflow_ts = datetime.fromtimestamp(most_recent[1] / 1000, tz=UTC)
                return (most_recent[0], workflow_ts)

        except logs_client.exceptions.ResourceNotFoundException:
            print(f"   {colour('⚠️  Orchestrator log group not found', 'yellow')}")
            return None
        except ClientError as e:
            print(f"   {colour(f'❌ Error searching logs: {e}', 'red')}")
            return None

    # No workflows found in any window
    return None


def detect_workflow_time_range(
    logs_client: Any,
    correlation_id: str,
    stage: str,
    hours_back: int = 48,
) -> tuple[datetime, datetime]:
    """Detect the time range of a workflow by finding orchestrator start time.

    Args:
        logs_client: boto3 CloudWatch Logs client
        correlation_id: The workflow correlation ID
        stage: Environment stage (dev or prod)
        hours_back: Maximum hours to search back

    Returns:
        Tuple of (start_time, end_time) for the workflow

    """
    orchestrator_log_group = f"/aws/lambda/alch-{stage}-strategy-orchestrator"

    end_time = datetime.now(UTC)
    search_start = end_time - timedelta(hours=hours_back)

    start_ms = int(search_start.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    try:
        # Search for the first log entry with this correlation_id
        # Try nested path first (structlog format: extra.correlation_id)
        filter_patterns = [
            f'{{ $.extra.correlation_id = "{correlation_id}" }}',
            f'{{ $.correlation_id = "{correlation_id}" }}',
            f'"{correlation_id}"',  # Fallback: raw string match
        ]

        for filter_pattern in filter_patterns:
            response = logs_client.filter_log_events(
                logGroupName=orchestrator_log_group,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern=filter_pattern,
                limit=1,
            )

            events = response.get("events", [])
            if events:
                # Found the workflow start
                workflow_start_ms = events[0]["timestamp"]
                workflow_start = datetime.fromtimestamp(workflow_start_ms / 1000, tz=UTC)

                # Add buffer: 1 minute before, 30 minutes after (workflow should complete)
                return (
                    workflow_start - timedelta(minutes=1),
                    workflow_start + timedelta(minutes=30),
                )

    except ClientError as e:
        print(
            f"{colour('⚠️', 'yellow')} Could not auto-detect time range: {e}",
            file=sys.stderr,
        )

    # Fallback: use provided hours_back
    return (search_start, end_time)


def fetch_logs_by_correlation_id(
    correlation_id: str,
    stage: str = "dev",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    include_raw: bool = False,
    auto_detect_range: bool = True,
) -> list[dict[str, Any]]:
    """Fetch logs from all Lambda log groups by correlation_id.

    Args:
        correlation_id: The workflow correlation ID to search for
        stage: Environment stage (dev or prod)
        start_time: Optional start time
        end_time: Optional end time
        include_raw: Whether to include non-JSON log messages
        auto_detect_range: Whether to auto-detect time range from orchestrator

    Returns:
        List of log events sorted by timestamp

    """
    logs_client = boto3.client("logs", region_name=REGION)
    log_groups = get_log_groups(stage)

    # Auto-detect time range if not provided
    if auto_detect_range and (start_time is None or end_time is None):
        print(f"{colour('🔎', 'cyan')} Auto-detecting workflow time range...")
        detected_start, detected_end = detect_workflow_time_range(
            logs_client, correlation_id, stage
        )
        start_time = start_time or detected_start
        end_time = end_time or detected_end
        print(
            f"   Found range: {start_time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"to {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

    # Fallback defaults
    if not end_time:
        end_time = datetime.now(UTC)
    if not start_time:
        start_time = end_time - timedelta(hours=24)

    # Convert to milliseconds epoch
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    all_events: list[dict[str, Any]] = []

    for log_group in log_groups:
        lambda_name = log_group.split("/")[-1]
        print(f"   Querying {colour(lambda_name, 'blue')}...", end="", flush=True)

        try:
            # Use simple string filter to catch ALL logs containing the correlation_id
            # This is more permissive than JSON path filters and catches logs regardless
            # of where the correlation_id appears (extra.correlation_id, correlation_id, or raw text)
            paginator = logs_client.get_paginator("filter_log_events")

            event_count = 0
            for page in paginator.paginate(
                logGroupName=log_group,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern=f'"{correlation_id}"',  # Simple string match - catches everything
            ):
                for event in page.get("events", []):
                    event_count += 1
                    try:
                        # Parse JSON log message
                        message = json.loads(event["message"])
                        message["_log_group"] = log_group
                        message["_lambda_name"] = lambda_name
                        message["_timestamp_ms"] = event["timestamp"]
                        message["_is_json"] = True
                        all_events.append(message)
                    except json.JSONDecodeError:
                        # Include non-JSON logs (boto3 debug, Lambda START/END, etc.)
                        if include_raw:
                            all_events.append(
                                {
                                    "_log_group": log_group,
                                    "_lambda_name": lambda_name,
                                    "_timestamp_ms": event["timestamp"],
                                    "_raw_message": event["message"],
                                    "_is_json": False,
                                }
                            )

            print(f" {colour(str(event_count), 'green')} events")

        except logs_client.exceptions.ResourceNotFoundException:
            print(f" {colour('⚠️  Log group not found', 'yellow')}")
        except ClientError as e:
            print(f" {colour(f'❌ Error: {e}', 'red')}")

    # Sort by timestamp
    all_events.sort(key=lambda x: x.get("_timestamp_ms", 0))

    return all_events


def is_error_event(event: dict[str, Any]) -> bool:
    """Check if an event represents an error, warning, or failure.

    Args:
        event: The log event dictionary

    Returns:
        True if the event should be highlighted as an issue

    """
    # Check log level
    level = event.get("level", "").lower()
    
    # If we have an explicit level, trust it
    if level:
        if level in ERROR_LEVELS:
            return True
        # If it's debug/info, it's not an error unless it has an explicit error field
        if level in {"debug", "info"}:
            return bool(event.get("error") or event.get("exception") or event.get("error_id"))
        
    # Check for error patterns in the message (primarily for raw logs or fallback)
    message_text = event.get("event", "") + " " + event.get("_raw_message", "")
    message_lower = message_text.lower()

    for pattern in ERROR_PATTERNS:
        if re.search(pattern, message_lower):
            return True

    # Check if there's an error field (safety net)
    if event.get("error") or event.get("exception") or event.get("error_id"):
        return True

    return False


def format_event(event: dict[str, Any], show_extra: bool = True) -> str:
    """Format a log event for human-readable output.

    Args:
        event: The log event dictionary
        show_extra: Whether to show extra fields

    Returns:
        Formatted string for display

    """
    ts = datetime.fromtimestamp(event.get("_timestamp_ms", 0) / 1000, tz=UTC)
    lambda_name = event.get("_lambda_name", "unknown")
    level = event.get("level", "?").upper()

    # Determine colour based on level
    if level in ("ERROR", "CRITICAL", "FATAL"):
        level_colour = "red"
    elif level == "WARNING":
        level_colour = "yellow"
    elif level == "INFO":
        level_colour = "green"
    else:
        level_colour = "grey"

    # Get message
    if event.get("_is_json", True):
        msg = event.get("event", "")
        module = event.get("module", "")
    else:
        msg = event.get("_raw_message", "")[:200]
        module = ""

    # Format timestamp
    ts_str = ts.strftime("%H:%M:%S.%f")[:-3]

    # Build output
    parts = [
        colour(f"[{ts_str}]", "grey"),
        colour(f"[{lambda_name.replace('alch-dev-', '')}]", "cyan"),
        colour(f"[{level:7}]", level_colour),
    ]

    if module:
        parts.append(colour(f"[{module}]", "blue"))

    parts.append(msg)

    output = " ".join(parts)

    # Add extra fields for errors
    if show_extra and is_error_event(event):
        extra = event.get("extra", {})
        if extra:
            extra_str = json.dumps(extra, default=str)
            output += f"\n         {colour('Extra:', 'grey')} {extra_str}"

        # Show error details if present
        if event.get("error"):
            output += f"\n         {colour('Error:', 'red')} {event['error']}"

    return output


def print_summary(events: list[dict[str, Any]]) -> None:
    """Print a summary of the workflow events.

    Args:
        events: List of log events

    """
    if not events:
        print(f"\n{colour('📊 Summary:', 'bold')} No events found")
        return

    # Count by level
    level_counts: dict[str, int] = {}
    for event in events:
        level = event.get("level", "unknown").lower()
        level_counts[level] = level_counts.get(level, 0) + 1

    # Count by lambda
    lambda_counts: dict[str, int] = {}
    for event in events:
        lambda_name = event.get("_lambda_name", "unknown")
        # Shorten name for display
        short_name = lambda_name.replace("alch-dev-", "").replace(
            "alch-prod-", ""
        )
        lambda_counts[short_name] = lambda_counts.get(short_name, 0) + 1

    # Time span (all events)
    first_ts = datetime.fromtimestamp(events[0]["_timestamp_ms"] / 1000, tz=UTC)
    last_ts = datetime.fromtimestamp(events[-1]["_timestamp_ms"] / 1000, tz=UTC)
    duration = last_ts - first_ts

    # Workflow execution time (orchestrator start to last log)
    orchestrator_start = None
    for event in events:
        if "orchestrator" in event.get("_lambda_name", "").lower():
            orchestrator_start = datetime.fromtimestamp(event["_timestamp_ms"] / 1000, tz=UTC)
            break

    print(f"\n{colour('📊 Summary:', 'bold')}")
    print(f"   Total events: {len(events)}")
    print(f"   Time span: {duration.total_seconds():.1f}s")
    print(f"   Start: {first_ts.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"   End:   {last_ts.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    if orchestrator_start:
        workflow_duration = last_ts - orchestrator_start
        minutes = int(workflow_duration.total_seconds() // 60)
        seconds = workflow_duration.total_seconds() % 60
        duration_str = f"{minutes}m {seconds:.1f}s" if minutes > 0 else f"{seconds:.1f}s"
        print(f"\n   {colour('⏱️  Workflow Execution Time:', 'bold')} {colour(duration_str, 'green')}")
        print(f"   (From orchestrator start to last log)")

    # Levels
    print(f"\n   {colour('By Level:', 'bold')}")
    for level, count in sorted(level_counts.items(), key=lambda x: -x[1]):
        level_colour = "red" if level in ERROR_LEVELS else "green"
        level_padded = f"{level:10}"
        print(f"      {colour(level_padded, level_colour)}: {count}")

    # Lambdas
    print(f"\n   {colour('By Lambda:', 'bold')}")
    for lambda_name, count in sorted(lambda_counts.items(), key=lambda x: -x[1]):
        name_padded = f"{lambda_name:25}"
        print(f"      {colour(name_padded, 'cyan')}: {count}")


# ============================================================================
# DynamoDB Workflow Data Functions
# ============================================================================


def format_money(value: str | Decimal | float) -> str:
    """Format a decimal value as money for display."""
    try:
        d = Decimal(str(value))
        return f"${float(d):,.2f}"
    except Exception:
        return str(value)


def format_percentage(value: str | Decimal | float) -> str:
    """Format a decimal as percentage for display."""
    try:
        d = Decimal(str(value))
        return f"{float(d) * 100:.2f}%"
    except Exception:
        return str(value)


def get_rebalance_plans(
    dynamodb: Any,
    correlation_id: str,
    stage: str = "dev",
) -> list[dict[str, Any]]:
    """Query all rebalance plans for a workflow from DynamoDB.

    In the per-strategy architecture, each strategy worker produces its own
    rebalance plan, so there may be multiple plans per workflow run.

    Args:
        dynamodb: boto3 DynamoDB client
        correlation_id: The workflow correlation ID
        stage: Environment stage (dev or prod)

    Returns:
        List of rebalance plan dicts (one per strategy), sorted by strategy_id

    """
    table_name = f"alchemiser-{stage}-rebalance-plans"

    try:
        response = dynamodb.query(
            TableName=table_name,
            IndexName="GSI1-CorrelationIndex",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"CORR#{correlation_id}"}},
            ScanIndexForward=False,
        )

        plans = []
        for item in response.get("Items", []):
            plan_data_str = item.get("plan_data", {}).get("S", "{}")
            plans.append(dict(json.loads(plan_data_str)))

        # Sort by strategy_id for consistent display
        plans.sort(key=lambda p: p.get("strategy_id") or p.get("plan_id", ""))
        return plans

    except ClientError:
        return []


def get_aggregated_signal(
    dynamodb: Any,
    correlation_id: str,
    stage: str = "dev",
) -> dict[str, Any] | None:
    """Query aggregated signal from DynamoDB.

    Args:
        dynamodb: boto3 DynamoDB client
        correlation_id: The workflow correlation ID
        stage: Environment stage (dev or prod)

    Returns:
        Aggregated signal data or None if not found

    """
    table_name = f"alchemiser-{stage}-aggregation-sessions"

    try:
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
            return dict(json.loads(merged_signal_str))

        return dict(item)

    except ClientError:
        return None


def get_partial_signals(
    dynamodb: Any,
    correlation_id: str,
    stage: str = "dev",
) -> list[dict[str, Any]]:
    """Query per-strategy partial signals from the aggregation sessions table.

    Each partial signal contains the raw (un-weighted) portfolio for a single
    strategy, where allocations sum to ~100%.

    Args:
        dynamodb: boto3 DynamoDB client
        correlation_id: The workflow correlation ID
        stage: Environment stage (dev or prod)

    Returns:
        List of partial signal dicts with dsl_file, allocation weight, and
        consolidated_portfolio.

    """
    table_name = f"alchemiser-{stage}-aggregation-sessions"

    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"SESSION#{correlation_id}"},
                ":sk_prefix": {"S": "STRATEGY#"},
            },
        )

        signals = []
        for item in response.get("Items", []):
            portfolio_str = item.get("consolidated_portfolio", {}).get("S", "{}")
            signals.append(
                {
                    "dsl_file": item.get("dsl_file", {}).get("S", ""),
                    "allocation": Decimal(item.get("allocation", {}).get("N", "0")),
                    "signal_count": int(item.get("signal_count", {}).get("N", "0")),
                    "consolidated_portfolio": json.loads(portfolio_str),
                    "success": item.get("success", {}).get("BOOL", True),
                    "error_message": item.get("error_message", {}).get("S", "") or None,
                }
            )

        return signals

    except ClientError:
        return []


def print_signal_analysis(
    signal: dict[str, Any],
    partial_signals: list[dict[str, Any]] | None = None,
) -> None:
    """Print aggregated signal analysis with per-strategy breakdowns.

    Shows each strategy's raw portfolio (allocations summing to ~100%) followed
    by the combined weighted allocations across the whole portfolio.

    Args:
        signal: The aggregated signal data (merged signal).
        partial_signals: Optional list of per-strategy partial signals from DynamoDB.

    """
    print(f"\n{colour('AGGREGATED SIGNAL', 'bold')}")
    print("=" * 110)

    allocations = signal.get("allocations") or signal.get("target_allocations") or {}
    source_strategies: list[str] = signal.get("source_strategies", [])
    strategy_count = signal.get("strategy_count", len(source_strategies))
    is_partial = signal.get("is_partial", False)

    if not allocations:
        print("   No allocations found in signal")
        return

    # Summary header
    print(f"   Total symbols: {len(allocations)}")
    print(f"   Strategies merged: {strategy_count}")
    if source_strategies:
        print(f"   Source strategies: {', '.join(source_strategies)}")
    if is_partial:
        print(f"   {colour('WARNING: Partial signal (some strategies failed)', 'yellow')}")

    total_weight = sum(Decimal(str(v)) for v in allocations.values())
    print(f"   Total weight: {format_percentage(total_weight)}")

    if total_weight > Decimal("1.0"):
        print(f"   {colour('WARNING: Signal weights sum to > 100%!', 'yellow')}")

    # --- Per-strategy raw portfolios (each sums to ~100%) ---
    if partial_signals:
        print(f"\n   {colour('PER-STRATEGY PORTFOLIOS (raw allocations, each sums to ~100%):', 'bold')}")
        print(f"   {'-' * 106}")

        for ps in sorted(partial_signals, key=lambda x: x["dsl_file"]):
            dsl_file = ps["dsl_file"]
            portfolio_weight = ps["allocation"]
            success = ps.get("success", True)
            portfolio_data = ps["consolidated_portfolio"]
            signal_count = ps.get("signal_count", 0)

            # Extract raw target_allocations from the partial portfolio
            raw_allocs: dict[str, str] = {}
            if isinstance(portfolio_data, dict):
                raw_allocs = portfolio_data.get("target_allocations", {})
                if not raw_allocs:
                    # Fallback: filter out metadata keys from the dict itself
                    metadata_keys = {
                        "correlation_id", "timestamp", "strategy_count",
                        "source_strategies", "schema_version",
                        "strategy_contributions",
                    }
                    raw_allocs = {
                        k: v for k, v in portfolio_data.items()
                        if k not in metadata_keys
                    }

            status = colour("OK", "green") if success else colour("FAILED", "red")
            error_msg = ps.get("error_message", "")

            strat_total = sum(Decimal(str(v)) for v in raw_allocs.values()) if raw_allocs else Decimal("0")
            print(
                f"\n   {colour(dsl_file, 'cyan')}  "
                f"[portfolio weight: {format_percentage(portfolio_weight)}, "
                f"signals: {signal_count}, status: {status}]"
            )

            if error_msg:
                print(f"      {colour(f'Error: {error_msg}', 'red')}")

            if not raw_allocs:
                print("      (no allocations)")
                continue

            # Normalize to raw strategy output (each strategy sums to ~100%)
            # The stored values are already scaled by portfolio weight, so divide back out
            strat_total = sum(Decimal(str(v)) for v in raw_allocs.values())
            if strat_total > 0:
                normalised_allocs = {
                    sym: Decimal(str(w)) / strat_total
                    for sym, w in raw_allocs.items()
                }
            else:
                normalised_allocs = {sym: Decimal("0") for sym in raw_allocs}

            print(f"      {'Symbol':<10} {'Raw Weight':>10}  {'Weighted':>10}")
            print(f"      {'-' * 34}")

            sorted_raw = sorted(
                normalised_allocs.items(), key=lambda x: x[1], reverse=True,
            )
            for symbol, norm_weight in sorted_raw:
                if norm_weight > 0:
                    orig_weight = Decimal(str(raw_allocs[symbol]))
                    print(
                        f"      {symbol:<10} "
                        f"{format_percentage(norm_weight):>10}  "
                        f"{format_percentage(orig_weight):>10}"
                    )

        print(f"\n   {'-' * 106}")


def query_executed_trades(
    dynamodb: Any,
    correlation_id: str,
    stage: str = "dev",
) -> dict[str, dict[str, Any]]:
    """Query executed trades from Trade Ledger DynamoDB by correlation_id.

    Returns a dict keyed by ``strategy_id::symbol`` (primary) and ``symbol``
    (fallback for pre-migration trades without strategy_id).  When multiple
    per-strategy plans share a symbol, the strategy-qualified key prevents
    one plan's execution status from leaking into another.

    Args:
        dynamodb: boto3 DynamoDB client
        correlation_id: The workflow correlation ID
        stage: Environment stage (dev or prod)

    Returns:
        Dict mapping key -> trade data.  Keys are both
        ``strategy_id::symbol`` and plain ``symbol`` (last-write wins
        for plain symbol, kept as backward-compat fallback).

    """
    table_name = f"alchemiser-{stage}-trade-ledger"

    try:
        response = dynamodb.query(
            TableName=table_name,
            IndexName="GSI1-CorrelationIndex",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"CORR#{correlation_id}"}},
        )

        trades_by_key: dict[str, dict[str, Any]] = {}
        for item in response.get("Items", []):
            symbol = item.get("symbol", {}).get("S", "")
            if symbol:
                strategy_id = item.get("strategy_id", {}).get("S", "")
                trade_data = {
                    "symbol": symbol,
                    "strategy_id": strategy_id,
                    "direction": item.get("direction", {}).get("S", ""),
                    "filled_qty": item.get("filled_qty", {}).get("S", "0"),
                    "fill_price": item.get("fill_price", {}).get("S", "0"),
                    "order_id": item.get("order_id", {}).get("S", ""),
                    "fill_timestamp": item.get("fill_timestamp", {}).get("S", ""),
                    "success": True,  # If it's in the ledger, it was executed
                }
                # Strategy-qualified key (primary lookup for per-strategy plans)
                if strategy_id:
                    trades_by_key[f"{strategy_id}::{symbol}"] = trade_data
                # Plain symbol key (backward-compat fallback)
                trades_by_key[symbol] = trade_data

        return trades_by_key

    except ClientError as e:
        logger.error(
            "Failed to query trades from ledger",
            correlation_id=correlation_id,
            error=str(e),
        )
        return {}


def print_single_plan_summary(
    plan: dict[str, Any],
    executed_by_symbol: dict[str, dict[str, Any]],
    plan_index: int,
    total_plans: int,
) -> None:
    """Print a single rebalance plan with execution status.

    Args:
        plan: The rebalance plan data
        executed_by_symbol: Dict of symbol -> trade data from Trade Ledger
        plan_index: 1-based index of this plan
        total_plans: Total number of plans in this workflow

    """
    metadata = plan.get("metadata", {}) or {}
    portfolio_value = metadata.get("portfolio_value", plan.get("total_portfolio_value", "N/A"))
    cash_balance = metadata.get("cash_balance", "N/A")
    strategy_id = plan.get("strategy_id") or "unknown"

    print(f"\n   {colour(f'--- Strategy {plan_index}/{total_plans}: {strategy_id} ---', 'bold')}")
    print(f"   Portfolio Value: {format_money(portfolio_value)}")
    print(f"   Cash Balance: {format_money(cash_balance)}")
    print(f"   Plan ID: {plan.get('plan_id', 'N/A')}")

    items = plan.get("items", [])

    # Print header
    print(f"\n   {colour('PLANNED TRADES:', 'bold')}")
    print(f"   {'-' * 106}")
    print(f"   {'Act':<4} {'Symbol':<8} {'Qty':<12} {'Amount':<15} {'Status':<65}")
    print(f"   {'-' * 106}")

    # Print each planned trade with execution status
    for item in items:
        symbol = item.get("symbol", "?")
        action = item.get("action", "?")
        target_qty = item.get("target_quantity", 0)
        trade_amt = item.get("trade_amount", 0)

        # Display action as 3 chars for formatting
        action_short = action[0:3] if len(action) >= 3 else action

        # Check if this trade was executed (present in Trade Ledger)
        # Use strategy-qualified key first, fall back to plain symbol
        executed = (
            executed_by_symbol.get(f"{strategy_id}::{symbol}")
            or executed_by_symbol.get(symbol)
        )

        if action == "HOLD":
            status = colour("-- HOLD", "cyan")
        elif executed:
            filled_qty = executed.get("filled_qty", "0")
            fill_price = executed.get("fill_price", "0")
            status = colour(f"OK EXECUTED (qty: {filled_qty}, price: ${fill_price})", "green")
        else:
            status = colour("-- NOT EXECUTED", "grey")

        print(f"   {action_short:<4} {symbol:<8} {str(target_qty):<12} {format_money(trade_amt):<15} {status}")

    print(f"   {'-' * 106}")

    # Summary stats
    buys = [i for i in items if i.get("action") == "BUY"]
    sells = [i for i in items if i.get("action") == "SELL"]
    holds = [i for i in items if i.get("action") == "HOLD"]

    total_buy = sum(Decimal(str(i.get("trade_amount", 0))) for i in buys)
    total_sell = sum(abs(Decimal(str(i.get("trade_amount", 0)))) for i in sells)

    # Count execution results from Trade Ledger for symbols in this plan
    plan_symbols = {i.get("symbol") for i in items if i.get("action") in ("BUY", "SELL")}
    executed_count = sum(
        1 for s in plan_symbols
        if executed_by_symbol.get(f"{strategy_id}::{s}") or executed_by_symbol.get(s)
    )
    planned_trades = len(buys) + len(sells)
    not_executed = planned_trades - executed_count

    print(f"\n   {colour('PLAN SUMMARY:', 'bold')}")
    print(f"      BUY orders:  {len(buys):3d} totaling {format_money(total_buy)}")
    print(f"      SELL orders: {len(sells):3d} totaling {format_money(total_sell)}")
    print(f"      HOLD:        {len(holds):3d}")

    if executed_count > 0 or planned_trades > 0:
        print(f"\n   {colour('EXECUTION RESULTS:', 'bold')}")
        print(f"      Executed:     {colour(str(executed_count), 'green')} / {planned_trades}")
        if not_executed > 0:
            print(f"      Not executed: {colour(str(not_executed), 'yellow')}")

    # Deployment check
    try:
        total_target_value = sum(Decimal(str(i.get("target_value", 0))) for i in items)
        pv = Decimal(str(portfolio_value))
        if pv > 0:
            deployment_pct = (total_target_value / pv) * 100
            deployment_str = f"{float(deployment_pct):.1f}%"
            print(f"\n   {colour('DEPLOYMENT RATIO:', 'bold')} {deployment_str}")
            if deployment_pct > 100:
                print(f"   {colour('WARNING: Deployment exceeds 100%!', 'yellow')}")
    except (InvalidOperation, ValueError, TypeError):
        pass


def print_trades_execution_summary(
    plans: list[dict[str, Any]],
    dynamodb: Any,
    correlation_id: str,
    stage: str = "dev",
) -> None:
    """Print trade summary showing all rebalance plans with execution status.

    In the per-strategy architecture, each strategy produces its own plan.
    This displays each plan separately for clarity.

    Args:
        plans: List of rebalance plan dicts (one per strategy)
        dynamodb: boto3 DynamoDB client
        correlation_id: The workflow correlation ID
        stage: Environment stage (dev or prod)

    """
    print(f"\n{colour('REBALANCE PLANS & EXECUTION SUMMARY', 'bold')}")
    print("=" * 110)
    print(f"   {colour(f'Found {len(plans)} strategy rebalance plan(s)', 'cyan')}")

    executed_by_symbol = query_executed_trades(dynamodb, correlation_id, stage)

    all_buys = 0
    all_sells = 0
    all_holds = 0
    all_executed = 0
    all_planned = 0

    for idx, plan in enumerate(plans, 1):
        print_single_plan_summary(plan, executed_by_symbol, idx, len(plans))

        items = plan.get("items", [])
        buys = [i for i in items if i.get("action") == "BUY"]
        sells = [i for i in items if i.get("action") == "SELL"]
        holds = [i for i in items if i.get("action") == "HOLD"]
        plan_strategy_id = plan.get("strategy_id") or "unknown"
        plan_symbols = {i.get("symbol") for i in items if i.get("action") in ("BUY", "SELL")}

        all_buys += len(buys)
        all_sells += len(sells)
        all_holds += len(holds)
        all_planned += len(buys) + len(sells)
        all_executed += sum(
            1 for s in plan_symbols
            if executed_by_symbol.get(f"{plan_strategy_id}::{s}") or executed_by_symbol.get(s)
        )

    # Cross-strategy totals
    if len(plans) > 1:
        print(f"\n{'=' * 110}")
        print(f"   {colour('CROSS-STRATEGY TOTALS:', 'bold')}")
        print(f"      Total BUY orders:  {all_buys}")
        print(f"      Total SELL orders: {all_sells}")
        print(f"      Total HOLD:        {all_holds}")
        print(f"      Executed: {colour(str(all_executed), 'green')} / {all_planned}")
        if all_planned > all_executed:
            print(f"      Not executed: {colour(str(all_planned - all_executed), 'yellow')}")


def print_workflow_data(correlation_id: str, stage: str, events: list[dict[str, Any]]) -> None:
    """Fetch and print workflow data from DynamoDB.

    Args:
        correlation_id: The workflow correlation ID
        stage: Environment stage (dev or prod)
        events: List of log events (unused, kept for compatibility)

    """
    print(f"\n{colour('📦 Fetching workflow data from DynamoDB...', 'cyan')}")

    dynamodb = boto3.client("dynamodb", region_name=REGION)

    # Get aggregated signal and per-strategy partial signals
    signal = get_aggregated_signal(dynamodb, correlation_id, stage)
    partial_signals = get_partial_signals(dynamodb, correlation_id, stage)
    if signal:
        print_signal_analysis(signal, partial_signals=partial_signals or None)
    else:
        print(f"   {colour('No aggregated signal found in DynamoDB', 'yellow')}")

    # Get all rebalance plans (one per strategy) and execution status
    plans = get_rebalance_plans(dynamodb, correlation_id, stage)
    if plans:
        print_trades_execution_summary(plans, dynamodb, correlation_id, stage)
    else:
        print(f"   {colour('No rebalance plans found in DynamoDB', 'yellow')}")

    if not signal and not plans:
        print("   (Workflow data may have expired or workflow did not reach those stages)")



def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch CloudWatch logs for a workflow run by correlation_id",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                       # Most recent workflow in dev
  %(prog)s --stage prod                          # Most recent workflow in prod
  %(prog)s --correlation-id workflow-abc123      # Specific workflow
  %(prog)s --session-id workflow-abc123 --all    # All logs for specific workflow
  %(prog)s --stage prod --output logs.json       # Save to file
        """,
    )

    # Correlation ID - support both names, now optional
    id_group = parser.add_mutually_exclusive_group(required=False)
    id_group.add_argument(
        "--correlation-id",
        type=str,
        help="Correlation ID to search for (default: auto-detect most recent)",
    )
    id_group.add_argument(
        "--session-id",
        type=str,
        help="Session ID to search for (alias for correlation-id)",
    )

    parser.add_argument(
        "--stage",
        type=str,
        default="dev",
        choices=["dev", "prod"],
        help="Environment stage (default: dev)",
    )

    parser.add_argument(
        "--hours-back",
        type=int,
        default=48,
        help="Maximum hours to search back for auto-detection (default: 48)",
    )

    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Show all logs, not just errors/warnings",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Include raw/debug (non-JSON) log messages",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output JSON file (default: print to stdout)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted text",
    )

    parser.add_argument(
        "--no-colour",
        "--no-color",
        action="store_true",
        help="Disable coloured output",
    )

    parser.add_argument(
        "--no-data",
        action="store_true",
        help="Skip fetching workflow data (signal/rebalance plan) from DynamoDB",
    )

    args = parser.parse_args()

    # Disable colours if requested
    if args.no_colour:
        for key in COLOURS:
            COLOURS[key] = ""

    # Get correlation ID (from either argument, or auto-detect)
    correlation_id = args.correlation_id or args.session_id

    if not correlation_id:
        # Auto-detect most recent workflow
        print(f"\n{colour('🔍 Finding most recent workflow run...', 'bold')}")
        logs_client = boto3.client("logs", region_name=REGION)
        result = find_most_recent_workflow(
            logs_client,
            args.stage,
            hours_back=args.hours_back,
        )

        if not result:
            print(f"\n{colour('❌', 'red')} No recent workflow runs found in {args.stage}")
            print("   Tips:")
            print("   - Try a different --stage (dev or prod)")
            print("   - Increase --hours-back to search further")
            print("   - Provide a specific --correlation-id")
            return 1

        correlation_id, workflow_ts = result
        ts_str = workflow_ts.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"   {colour('✓', 'green')} Found: {colour(correlation_id, 'cyan')}")
        print(f"   {colour('📅', 'cyan')} Timestamp: {colour(ts_str, 'green')}")

    print(f"\n{colour('🔍 Fetching logs for workflow:', 'bold')}")
    print(f"   Correlation ID: {colour(correlation_id, 'cyan')}")
    print(f"   Stage: {args.stage}")
    print()

    # Fetch all logs
    events = fetch_logs_by_correlation_id(
        correlation_id=correlation_id,
        stage=args.stage,
        include_raw=args.verbose,
        auto_detect_range=True,
    )

    print(f"\n{colour('📥', 'green')} Found {len(events)} total log events")

    if not events:
        print(f"\n{colour('❌', 'red')} No logs found for this correlation_id")
        print("   Tips:")
        print("   - Check the correlation_id is correct")
        print("   - Try increasing --hours-back")
        print("   - Verify the workflow ran in the specified --stage")
        return 1

    # Filter for errors/warnings unless --all is specified
    if args.all:
        filtered_events = events
    else:
        filtered_events = [e for e in events if is_error_event(e)]
        print(
            f"{colour('⚠️', 'yellow')} Filtered to {len(filtered_events)} "
            f"errors/warnings (use --all to see all logs)"
        )

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(events, f, indent=2, default=str)
        print(f"\n{colour('📁', 'green')} Saved {len(events)} events to: {args.output}")

    elif args.json:
        print(json.dumps(filtered_events, indent=2, default=str))

    else:
        # Print summary first
        print_summary(events)

        # Print timeline
        if filtered_events:
            print(f"\n{'=' * 100}")
            if args.all:
                print(colour("WORKFLOW LOGS (chronological)", "bold"))
            else:
                print(colour("ERRORS & WARNINGS (chronological)", "bold"))
            print("=" * 100)

            for event in filtered_events:
                print(format_event(event, show_extra=True))

            print("=" * 100)
        else:
            print(f"\n{colour('✅', 'green')} No errors or warnings found!")

        # Print workflow data from DynamoDB (signal and rebalance plan)
        if not args.no_data:
            print_workflow_data(correlation_id, args.stage, events)

    return 0


if __name__ == "__main__":
    sys.exit(main())
