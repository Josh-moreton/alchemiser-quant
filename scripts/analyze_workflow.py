#!/usr/bin/env python3
"""Analyze workflow logs to identify failure points.

Business Unit: shared | Status: current.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime


def analyze_workflow(log_file: str, detailed: bool = False) -> None:
    """Analyze workflow logs and print key events."""
    with open(log_file) as f:
        logs = json.load(f)

    print(f"=== WORKFLOW ANALYSIS ===")
    print(f"Total logs: {len(logs)}")
    print()

    if detailed:
        analyze_portfolio_in_detail(logs)
        return

    # Group by lambda
    lambdas: dict[str, list] = defaultdict(list)
    for log in logs:
        name = log.get("_lambda_name", "unknown").replace("alchemiser-dev-", "")
        lambdas[name].append(log)

    print("Events by Lambda:")
    for name, events in sorted(lambdas.items(), key=lambda x: -len(x[1])):
        print(f"  {name}: {len(events)}")
    print()

    # Key workflow events
    print("=== KEY WORKFLOW EVENTS ===")
    key_patterns = [
        ("Coordinator invoked", "coordinator lambda invoked"),
        ("Aggregation session created", "created aggregation session"),
        ("Strategy workers invoked", "invoking strategy"),
        ("Strategy execution complete", "strategy execution complete"),
        ("PartialSignal published", "partialandsignal"),
        ("Partial signals stored", "stored partial"),
        ("All strategies complete", "all strategies completed"),
        ("SignalGenerated published", "signalgenerated"),
        ("Portfolio received signal", "portfolio lambda"),
        ("RebalancePlan created", "rebalance"),
        ("Trade messages queued", "queue"),
        ("TradeExecuted", "tradeexecuted"),
        ("Notification sent", "notification"),
        ("WorkflowCompleted", "workflowcompleted"),
        ("WorkflowFailed", "workflowfailed"),
    ]

    for label, pattern in key_patterns:
        matches = []
        for log in logs:
            raw = str(log).lower()
            if pattern.lower() in raw:
                matches.append(log)
        if matches:
            print(f"  ✓ {label}: {len(matches)} events")
        else:
            print(f"  ✗ {label}: NOT FOUND")
    print()

    # Find errors and warnings
    print("=== ERRORS AND WARNINGS ===")
    errors = []
    warnings = []
    for log in logs:
        level = log.get("level", "").upper()
        raw = str(log).lower()
        if level == "ERROR" or "error" in raw:
            errors.append(log)
        elif level == "WARNING" or "warn" in raw:
            warnings.append(log)

    print(f"Errors found: {len(errors)}")
    print(f"Warnings found: {len(warnings)}")

    if errors:
        print()
        print("=== ERROR DETAILS ===")
        for e in errors[:20]:  # Limit to 20
            event = e.get("event", e.get("_raw_message", ""))
            ts = e.get("timestamp", e.get("_timestamp", ""))
            lamb = e.get("_lambda_name", "unknown").replace("alchemiser-dev-", "")
            print(f"  [{ts}] {lamb}: {event[:200]}")
    print()

    # Check Portfolio lambda specifically since Execution has 0 events
    print("=== PORTFOLIO LAMBDA ANALYSIS ===")
    portfolio_logs = lambdas.get("PortfolioFunction", [])
    print(f"Portfolio events: {len(portfolio_logs)}")

    if portfolio_logs:
        # Sort by timestamp
        def get_ts(log: dict) -> str:
            return log.get("timestamp", log.get("_timestamp", ""))

        sorted_logs = sorted(portfolio_logs, key=get_ts)

        print("\nFirst 5 Portfolio events:")
        for log in sorted_logs[:5]:
            event = log.get("event", log.get("_raw_message", ""))
            ts = get_ts(log)
            print(f"  [{ts}] {event[:150]}")

        print("\nLast 5 Portfolio events:")
        for log in sorted_logs[-5:]:
            event = log.get("event", log.get("_raw_message", ""))
            ts = get_ts(log)
            print(f"  [{ts}] {event[:150]}")
    print()

    # Check Aggregator lambda - did it emit SignalGenerated?
    print("=== SIGNAL AGGREGATOR ANALYSIS ===")
    agg_logs = lambdas.get("StrategyAggregatorFunction", [])
    print(f"Aggregator events: {len(agg_logs)}")

    for log in agg_logs:
        raw = str(log).lower()
        if "signalgenerated" in raw or "publish" in raw or "complete" in raw:
            event = log.get("event", log.get("_raw_message", ""))
            ts = log.get("timestamp", log.get("_timestamp", ""))
            print(f"  [{ts}] {event[:200]}")


def analyze_portfolio_in_detail(logs: list) -> None:
    """Analyze portfolio logs in detail to find why execution wasnt triggered."""
    print("=== DETAILED PORTFOLIO ANALYSIS ===")
    print()

    # Find portfolio-related logs
    portfolio_logs = [
        log
        for log in logs
        if "portfolio" in log.get("_lambda_name", "").lower()
    ]
    print(f"Portfolio lambda logs: {len(portfolio_logs)}")

    # Sort by timestamp
    def get_ts(log: dict) -> str:
        return log.get("timestamp", log.get("_timestamp", ""))

    portfolio_logs = sorted(portfolio_logs, key=get_ts)

    print()
    print("=== PORTFOLIO WORKFLOW SEQUENCE ===")
    for log in portfolio_logs:
        event = log.get("event", "")
        ts = get_ts(log)
        level = log.get("level", "INFO")

        # Skip low-level boto3 logs
        if "Making request for" in str(log.get("_raw_message", "")):
            continue
        if "botocore" in str(log.get("_lambda_name", "")):
            continue

        # Print meaningful events
        if event:
            extra_info = ""
            if "trades" in log:
                extra_info = f" | trades={log.get('trades')}"
            if "sell_count" in log:
                extra_info += f" | sells={log.get('sell_count')}, buys={log.get('buy_count')}"
            if "trade_count" in log:
                extra_info += f" | trade_count={log.get('trade_count')}"
            print(f"[{ts}] [{level}] {event}{extra_info}")

    print()
    print("=== QUEUE / SQS OPERATIONS ===")
    queue_logs = [
        log
        for log in logs
        if any(
            x in str(log).lower()
            for x in ["queue", "sqs", "sendmessage", "enqueue"]
        )
    ]
    for log in queue_logs:
        event = log.get("event", log.get("_raw_message", ""))
        print(f"  - {event[:300]}")

    print()
    print("=== EVENTBRIDGE PUTS (RebalancePlanned) ===")
    eb_logs = [
        log
        for log in logs
        if "putevents" in str(log).lower() and "portfolio" in log.get("_lambda_name", "").lower()
    ]
    print(f"EventBridge PutEvents from Portfolio: {len(eb_logs)}")

    print()
    print("=== ALL ERRORS IN WORKFLOW ===")
    error_logs = [
        log
        for log in logs
        if log.get("level", "").upper() == "ERROR"
    ]
    for log in error_logs:
        event = log.get("event", "")
        lamb = log.get("_lambda_name", "").replace("alchemiser-dev-", "")
        print(f"  [{lamb}] {event}")


if __name__ == "__main__":
    log_file = "/tmp/workflow_logs_full.json"
    detailed = False

    for arg in sys.argv[1:]:
        if arg in ("--detailed", "-d"):
            detailed = True
        elif not arg.startswith("-"):
            log_file = arg

    analyze_workflow(log_file, detailed)
