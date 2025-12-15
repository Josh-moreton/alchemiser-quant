#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Fetch CloudWatch logs for a complete workflow run by correlation_id or session_id.

This script queries all Lambda log groups for a given workflow run, filters for
errors/warnings/failures, and presents a chronological timeline of events.

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
from typing import Any

import boto3
from botocore.exceptions import ClientError

# AWS configuration
REGION = "us-east-1"

# Lambda function names (without stage prefix)
LAMBDA_FUNCTIONS = [
    "strategy-orchestrator",
    "strategy-worker",
    "signal-aggregator",
    "portfolio",
    "execution",
    "notifications",
    "metrics",
    "data",
]

# Log levels to include when filtering for issues
ERROR_LEVELS = {"error", "warning", "critical", "fatal"}

# Patterns that indicate errors even if level isn't set
ERROR_PATTERNS = [
    r"traceback",
    r"exception",
    r"error",
    r"failed",
    r"failure",
    r"timeout",
    r"timed out",
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
    return [f"/aws/lambda/alchemiser-{stage}-{fn}" for fn in LAMBDA_FUNCTIONS]


def colour(text: str, colour_name: str) -> str:
    """Apply ANSI colour to text."""
    return f"{COLOURS.get(colour_name, '')}{text}{COLOURS['reset']}"


def find_most_recent_workflow(
    logs_client: Any,
    stage: str,
    hours_back: int = 48,
) -> str | None:
    """Find the most recent workflow run from the strategy orchestrator.

    Args:
        logs_client: boto3 CloudWatch Logs client
        stage: Environment stage (dev or prod)
        hours_back: Maximum hours to search back

    Returns:
        The correlation_id of the most recent workflow, or None if not found

    """
    orchestrator_log_group = f"/aws/lambda/alchemiser-{stage}-strategy-orchestrator"

    end_time = datetime.now(UTC)
    search_start = end_time - timedelta(hours=hours_back)

    start_ms = int(search_start.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    print(f"   Searching last {hours_back} hours in {colour(stage.upper(), 'cyan')} environment...")

    try:
        # Search for any logs with a correlation_id field
        # CloudWatch filter patterns don't support wildcards, so we just filter
        # for existence of the correlation_id field
        response = logs_client.filter_log_events(
            logGroupName=orchestrator_log_group,
            startTime=start_ms,
            endTime=end_ms,
            filterPattern='{ $.correlation_id = * }',
            limit=200,  # Get recent events
        )

        events = response.get("events", [])
        if not events:
            # Try alternative: look for "workflow" in the message as fallback
            response = logs_client.filter_log_events(
                logGroupName=orchestrator_log_group,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern='"workflow-"',
                limit=200,
            )
            events = response.get("events", [])

        if not events:
            return None

        # Parse events and find unique correlation_ids, taking the most recent
        correlation_ids: dict[str, int] = {}  # correlation_id -> timestamp
        for event in events:
            try:
                message = json.loads(event["message"])
                cid = message.get("correlation_id", "")
                if cid and cid.startswith("workflow-"):
                    ts = event["timestamp"]
                    if cid not in correlation_ids or ts > correlation_ids[cid]:
                        correlation_ids[cid] = ts
            except json.JSONDecodeError:
                # Try to extract from raw message
                raw = event.get("message", "")
                match = re.search(r'workflow-[a-f0-9-]+', raw)
                if match:
                    cid = match.group(0)
                    ts = event["timestamp"]
                    if cid not in correlation_ids or ts > correlation_ids[cid]:
                        correlation_ids[cid] = ts

        if not correlation_ids:
            return None

        # Return the most recent one
        most_recent = max(correlation_ids.items(), key=lambda x: x[1])
        return most_recent[0]

    except logs_client.exceptions.ResourceNotFoundException:
        print(f"   {colour('⚠️  Orchestrator log group not found', 'yellow')}")
        return None
    except ClientError as e:
        print(f"   {colour(f'❌ Error searching logs: {e}', 'red')}")
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
    orchestrator_log_group = f"/aws/lambda/alchemiser-{stage}-strategy-orchestrator"

    end_time = datetime.now(UTC)
    search_start = end_time - timedelta(hours=hours_back)

    start_ms = int(search_start.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    try:
        # Search for the first log entry with this correlation_id
        response = logs_client.filter_log_events(
            logGroupName=orchestrator_log_group,
            startTime=start_ms,
            endTime=end_ms,
            filterPattern=f'{{ $.correlation_id = "{correlation_id}" }}',
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
        print(f"   Querying {colour(lambda_name, 'blue')}...")

        try:
            # Use filter_log_events to search for correlation_id in JSON logs
            paginator = logs_client.get_paginator("filter_log_events")

            for page in paginator.paginate(
                logGroupName=log_group,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern=f'{{ $.correlation_id = "{correlation_id}" }}',
            ):
                for event in page.get("events", []):
                    try:
                        # Parse JSON log message
                        message = json.loads(event["message"])
                        message["_log_group"] = log_group
                        message["_lambda_name"] = lambda_name
                        message["_timestamp_ms"] = event["timestamp"]
                        message["_is_json"] = True
                        all_events.append(message)
                    except json.JSONDecodeError:
                        # Include non-JSON logs only if requested
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

        except logs_client.exceptions.ResourceNotFoundException:
            print(f"      {colour('⚠️  Log group not found', 'yellow')}")
        except ClientError as e:
            print(f"      {colour(f'❌ Error: {e}', 'red')}")

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
    if level in ERROR_LEVELS:
        return True

    # Check for error patterns in the message
    message_text = event.get("event", "") + " " + event.get("_raw_message", "")
    message_lower = message_text.lower()

    for pattern in ERROR_PATTERNS:
        if re.search(pattern, message_lower):
            return True

    # Check if there's an error field
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
        colour(f"[{lambda_name.replace('alchemiser-dev-', '')}]", "cyan"),
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
        short_name = lambda_name.replace("alchemiser-dev-", "").replace(
            "alchemiser-prod-", ""
        )
        lambda_counts[short_name] = lambda_counts.get(short_name, 0) + 1

    # Time span
    first_ts = datetime.fromtimestamp(events[0]["_timestamp_ms"] / 1000, tz=UTC)
    last_ts = datetime.fromtimestamp(events[-1]["_timestamp_ms"] / 1000, tz=UTC)
    duration = last_ts - first_ts

    print(f"\n{colour('📊 Summary:', 'bold')}")
    print(f"   Total events: {len(events)}")
    print(f"   Time span: {duration.total_seconds():.1f}s")
    print(f"   Start: {first_ts.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"   End:   {last_ts.strftime('%Y-%m-%d %H:%M:%S')} UTC")

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
        correlation_id = find_most_recent_workflow(
            logs_client,
            args.stage,
            hours_back=args.hours_back,
        )

        if not correlation_id:
            print(f"\n{colour('❌', 'red')} No recent workflow runs found in {args.stage}")
            print("   Tips:")
            print("   - Try a different --stage (dev or prod)")
            print("   - Increase --hours-back to search further")
            print("   - Provide a specific --correlation-id")
            return 1

        print(f"   {colour('✓', 'green')} Found: {colour(correlation_id, 'cyan')}")

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

    return 0


if __name__ == "__main__":
    sys.exit(main())
