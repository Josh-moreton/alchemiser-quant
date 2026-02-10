#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Diagnose why the Strategy Performance dashboard shows no data.

Checks each layer of the pipeline:
  1. StrategyPerformanceTable: Are there any LATEST items?
  2. TradeLedgerTable: Are there strategy metadata records? Lots?
  3. StrategyPerformanceFunction: Is the Lambda deployed? Env vars correct?
  4. CloudWatch Logs: Any errors in the strategy-performance Lambda?
  5. Simulated write: What would write_strategy_metrics() produce?

Usage:
    python scripts/diagnose_strategy_performance.py --stage prod
    python scripts/diagnose_strategy_performance.py --stage dev --verbose
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

REGION = "us-east-1"

# ANSI colour codes
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

_use_colour = True


def colour(text: str, colour_name: str) -> str:
    """Apply ANSI colour to text."""
    if not _use_colour:
        return str(text)
    return f"{COLOURS.get(colour_name, '')}{text}{COLOURS['reset']}"


def pass_fail(ok: bool) -> str:
    """Return coloured PASS or FAIL indicator."""
    if ok:
        return colour("PASS", "green")
    return colour("FAIL", "red")


def warn(text: str) -> str:
    """Return coloured warning text."""
    return colour(text, "yellow")


# ---------------------------------------------------------------------------
# Check 1: StrategyPerformanceTable
# ---------------------------------------------------------------------------


def check_performance_table(stage: str, verbose: bool) -> bool:
    """Check if the StrategyPerformanceTable has any LATEST strategy items."""
    table_name = f"alchemiser-{stage}-strategy-performance"
    dynamodb = boto3.resource("dynamodb", region_name=REGION)

    # Check table exists
    try:
        table = dynamodb.Table(table_name)
        table.load()
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"   {pass_fail(False)} Table {table_name} does NOT exist")
            return False
        raise

    print(f"   Table: {table_name}")
    print(f"   {pass_fail(True)} Table exists (item count ~{table.item_count})")

    # Query LATEST strategy items
    response = table.query(
        KeyConditionExpression=(Key("PK").eq("LATEST") & Key("SK").begins_with("STRATEGY#")),
    )
    items = response.get("Items", [])

    if not items:
        print(f"   {pass_fail(False)} No LATEST strategy items found")
        # Check if there are ANY items at all
        scan_resp = table.scan(Limit=5, ProjectionExpression="PK, SK")
        scan_items = scan_resp.get("Items", [])
        if scan_items:
            print(f"   {warn('Table has items but no LATEST strategies:')}")
            for item in scan_items:
                print(f"      PK={item.get('PK')}  SK={item.get('SK')}")
        else:
            print(f"   {warn('Table is completely empty')}")
        return False

    print(f"   {pass_fail(True)} Found {len(items)} LATEST strategy snapshots")
    if verbose:
        for item in items:
            name = item.get("strategy_name", "?")
            pnl = item.get("realized_pnl", "?")
            ts = item.get("snapshot_timestamp", "?")
            print(f"      {name}: P&L=${pnl}, snapshot={ts}")

    # Check capital deployed
    cap_resp = table.get_item(Key={"PK": "LATEST", "SK": "CAPITAL_DEPLOYED"})
    cap_item = cap_resp.get("Item")
    if cap_item:
        print(f"   {pass_fail(True)} Capital deployed: {cap_item.get('capital_deployed_pct')}%")
    else:
        print(f"   {warn('No CAPITAL_DEPLOYED item')}")

    return True


# ---------------------------------------------------------------------------
# Check 2: TradeLedger Data
# ---------------------------------------------------------------------------


def check_trade_ledger(stage: str, verbose: bool) -> dict[str, Any]:
    """Check TradeLedger for strategy metadata and lots."""
    table_name = f"alchemiser-{stage}-trade-ledger"
    dynamodb = boto3.resource("dynamodb", region_name=REGION)

    result: dict[str, Any] = {
        "metadata_count": 0,
        "strategy_names": set(),
        "open_lot_count": 0,
        "closed_lot_count": 0,
        "has_data": False,
    }

    try:
        table = dynamodb.Table(table_name)
        table.load()
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"   {pass_fail(False)} Table {table_name} does NOT exist")
            return result
        raise

    print(f"   Table: {table_name}")

    # 1. Strategy metadata via GSI3
    try:
        metadata_resp = table.query(
            IndexName="GSI3-StrategyIndex",
            KeyConditionExpression=Key("GSI3PK").eq("STRATEGIES"),
        )
        metadata_items = metadata_resp.get("Items", [])
        while "LastEvaluatedKey" in metadata_resp:
            metadata_resp = table.query(
                IndexName="GSI3-StrategyIndex",
                KeyConditionExpression=Key("GSI3PK").eq("STRATEGIES"),
                ExclusiveStartKey=metadata_resp["LastEvaluatedKey"],
            )
            metadata_items.extend(metadata_resp.get("Items", []))

        result["metadata_count"] = len(metadata_items)
        for item in metadata_items:
            name = item.get("strategy_name")
            if name:
                result["strategy_names"].add(name)

        if metadata_items:
            print(f"   {pass_fail(True)} Found {len(metadata_items)} strategy metadata records")
            if verbose:
                for item in metadata_items:
                    print(f"      {item.get('strategy_name', '?')}")
        else:
            print(f"   {pass_fail(False)} No strategy metadata found (GSI3PK=STRATEGIES)")
    except ClientError as e:
        print(f"   {warn(f'Error querying metadata: {e}')}")

    # 2. Scan for lots (count only)
    lot_strategies: set[str] = set()
    for is_open, label in [(True, "open"), (False, "closed")]:
        try:
            count = 0
            scan_kwargs: dict[str, Any] = {
                "FilterExpression": Attr("EntityType").eq("LOT") & Attr("is_open").eq(is_open),
                "ProjectionExpression": "strategy_name",
            }
            resp = table.scan(**scan_kwargs)
            for item in resp.get("Items", []):
                count += 1
                name = item.get("strategy_name")
                if name:
                    lot_strategies.add(name)
            while "LastEvaluatedKey" in resp:
                resp = table.scan(**scan_kwargs, ExclusiveStartKey=resp["LastEvaluatedKey"])
                for item in resp.get("Items", []):
                    count += 1
                    name = item.get("strategy_name")
                    if name:
                        lot_strategies.add(name)

            result[f"{label}_lot_count"] = count
            ok = count > 0
            print(f"   {pass_fail(ok)} {count} {label} lots")
        except ClientError as e:
            print(f"   {warn(f'Error scanning {label} lots: {e}')}")

    result["strategy_names"] |= lot_strategies
    all_names = sorted(result["strategy_names"])
    result["has_data"] = bool(all_names)

    if all_names:
        print(f"   Strategies found: {', '.join(all_names)}")
    else:
        print(f"   {warn('No strategy names found anywhere in TradeLedger')}")

    return result


# ---------------------------------------------------------------------------
# Check 3: Lambda Status
# ---------------------------------------------------------------------------


def check_lambda_status(stage: str) -> bool:
    """Check if the StrategyPerformanceFunction Lambda is deployed."""
    lambda_client = boto3.client("lambda", region_name=REGION)
    function_name = f"alchemiser-{stage}-strategy-performance"

    try:
        config = lambda_client.get_function_configuration(FunctionName=function_name)
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"   {pass_fail(False)} Lambda {function_name} does NOT exist")
            return False
        raise

    print(f"   {pass_fail(True)} Lambda exists: {function_name}")
    print(f"   Last modified: {config.get('LastModified', '?')}")
    print(f"   Memory: {config.get('MemorySize')}MB  Timeout: {config.get('Timeout')}s")

    env_vars = config.get("Environment", {}).get("Variables", {})
    ledger_table = env_vars.get("TRADE_LEDGER__TABLE_NAME", "")
    perf_table = env_vars.get("STRATEGY_PERFORMANCE_TABLE", "")

    has_ledger = bool(ledger_table)
    has_perf = bool(perf_table)

    print(f"   {pass_fail(has_ledger)} TRADE_LEDGER__TABLE_NAME = {ledger_table or '(not set)'}")
    print(f"   {pass_fail(has_perf)} STRATEGY_PERFORMANCE_TABLE = {perf_table or '(not set)'}")

    return has_ledger and has_perf


# ---------------------------------------------------------------------------
# Check 4: CloudWatch Logs
# ---------------------------------------------------------------------------


def check_cloudwatch_logs(stage: str) -> dict[str, Any]:
    """Check CloudWatch Logs for recent invocations and errors."""
    logs_client = boto3.client("logs", region_name=REGION)
    log_group = f"/aws/lambda/alchemiser-{stage}-strategy-performance"
    hours_back = 72

    result: dict[str, Any] = {
        "log_group_exists": False,
        "total_events": 0,
        "error_events": 0,
        "last_invocation": None,
        "has_no_summaries_message": False,
    }

    # Check log group exists
    try:
        resp = logs_client.describe_log_groups(logGroupNamePrefix=log_group, limit=1)
        groups = resp.get("logGroups", [])
        if not any(g["logGroupName"] == log_group for g in groups):
            print(f"   {pass_fail(False)} Log group does not exist: {log_group}")
            print(f"   {warn('Lambda has likely never been invoked')}")
            return result
    except ClientError as e:
        print(f"   {warn(f'Cannot check logs: {e}')}")
        return result

    result["log_group_exists"] = True
    print(f"   {pass_fail(True)} Log group exists: {log_group}")

    start_ms = int((datetime.now(UTC) - timedelta(hours=hours_back)).timestamp() * 1000)
    end_ms = int(datetime.now(UTC).timestamp() * 1000)

    # Count recent events
    try:
        event_resp = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            limit=50,
        )
        events = event_resp.get("events", [])
        result["total_events"] = len(events)

        if events:
            last_ts = max(e.get("timestamp", 0) for e in events)
            result["last_invocation"] = datetime.fromtimestamp(last_ts / 1000, tz=UTC)
            print(f"   {pass_fail(True)} {len(events)} log events in last {hours_back}h")
            print(f"   Last activity: {result['last_invocation'].isoformat()}")
        else:
            print(f"   {pass_fail(False)} No log events in last {hours_back}h")
            print(f"   {warn('Lambda has not been invoked recently')}")

        # Check for errors
        for event in events:
            msg = event.get("message", "").lower()
            if "error" in msg or "failed" in msg or "exception" in msg:
                result["error_events"] += 1
            if "no strategy summaries found" in msg:
                result["has_no_summaries_message"] = True

        if result["error_events"] > 0:
            print(f"   {warn(f'{result["error_events"]} events contain errors')}")
        if result["has_no_summaries_message"]:
            print(
                f"   {warn('Found \"No strategy summaries found\" -- '
                     'get_all_strategy_summaries() returned empty')}"
            )

    except ClientError as e:
        print(f"   {warn(f'Error querying logs: {e}')}")

    return result


# ---------------------------------------------------------------------------
# Check 5: Simulated write
# ---------------------------------------------------------------------------


def check_simulated_write(stage: str, verbose: bool) -> bool:
    """Simulate what write_strategy_metrics would produce (read-only)."""
    from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
        DynamoDBTradeLedgerRepository,
    )

    table_name = f"alchemiser-{stage}-trade-ledger"
    try:
        repo = DynamoDBTradeLedgerRepository(table_name)
        summaries = repo.get_all_strategy_summaries()
    except Exception as e:
        print(f"   {pass_fail(False)} get_all_strategy_summaries() raised: {e}")
        return False

    if not summaries:
        print(f"   {pass_fail(False)} get_all_strategy_summaries() returned EMPTY")
        print(f"   {warn('write_strategy_metrics() would skip writing entirely')}")
        return False

    print(f"   {pass_fail(True)} Found {len(summaries)} strategy summaries")
    for s in summaries:
        name = s["strategy_name"]
        pnl = float(s["total_realized_pnl"])
        trades = s["completed_trades"]
        holdings = s["current_holdings"]
        pnl_colour = "green" if pnl >= 0 else "red"
        print(
            f"      {name:30s} "
            f"P&L: {colour(f'${pnl:>10,.2f}', pnl_colour)} | "
            f"Trades: {trades:3d} | "
            f"Holdings: {holdings:3d}"
        )

    return True


# ---------------------------------------------------------------------------
# Diagnosis
# ---------------------------------------------------------------------------


def print_diagnosis(
    perf_ok: bool,
    ledger: dict[str, Any],
    lambda_ok: bool,
    logs: dict[str, Any],
    simulated_ok: bool,
) -> None:
    """Interpret results and print root cause recommendation."""
    if perf_ok:
        print(
            "The StrategyPerformanceTable HAS data. If the dashboard still shows\n"
            "nothing, check that the dashboard is pointing to the correct stage\n"
            "and that AWS credentials are configured."
        )
        return

    # Table is empty -- why?
    if not simulated_ok:
        print(
            "Root cause: get_all_strategy_summaries() returns EMPTY.\n"
            "Even if the Lambda runs, it would not write any data."
        )
        if not ledger["has_data"]:
            print(
                "\nThe TradeLedger has no strategy metadata or lots.\n"
                "Possible fixes:\n"
                "  1. Sync strategy ledger: python scripts/strategy_ledger.py sync --stage "
                + f"{stage}\n"
                "  2. Ensure trades have been executed with strategy attribution"
            )
        else:
            print(
                "\nTradeLedger has strategy data but summaries are empty.\n"
                "This may indicate a query issue in get_all_strategy_summaries()."
            )
        return

    # Summaries exist but table is empty -- Lambda issue
    if not lambda_ok:
        print(
            "Root cause: StrategyPerformanceFunction Lambda is NOT deployed.\n"
            f"Deploy with: make deploy-{stage}"
        )
        return

    if logs.get("has_no_summaries_message"):
        print(
            "Root cause: Lambda ran but get_all_strategy_summaries() returned empty.\n"
            "The TradeLedger may not have had data at the time of the last invocation."
        )
    elif logs.get("error_events", 0) > 0:
        print(
            "Root cause: Lambda has errors. Check CloudWatch Logs:\n"
            f"  Log group: /aws/lambda/alchemiser-{stage}-strategy-performance"
        )
    elif logs.get("total_events", 0) == 0:
        print(
            "Root cause: Lambda has NOT been invoked.\n"
            "No TradeExecuted events have fired since deployment.\n"
            "Fix: Run the backfill script to populate data from existing TradeLedger:\n"
            f"  python scripts/backfill_strategy_performance.py --stage {stage}"
        )
    else:
        print(
            "Lambda was invoked but data is still empty. Run with --verbose\n"
            "and check CloudWatch Logs for details."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all diagnostic checks."""
    parser = argparse.ArgumentParser(
        description="Diagnose empty Strategy Performance dashboard",
    )
    parser.add_argument("--stage", choices=["dev", "prod"], default="dev")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--no-colour", "--no-color", action="store_true")

    args = parser.parse_args()

    global _use_colour, stage
    _use_colour = not args.no_colour
    stage = args.stage

    print(f"\n{colour('STRATEGY PERFORMANCE DIAGNOSTICS', 'bold')}")
    print(f"Stage: {colour(args.stage.upper(), 'cyan')}")
    print("=" * 70)

    print(f"\n{colour('[1/5] StrategyPerformanceTable', 'bold')}")
    perf_ok = check_performance_table(args.stage, args.verbose)

    print(f"\n{colour('[2/5] TradeLedger Data', 'bold')}")
    ledger = check_trade_ledger(args.stage, args.verbose)

    print(f"\n{colour('[3/5] Lambda Deployment', 'bold')}")
    lambda_ok = check_lambda_status(args.stage)

    print(f"\n{colour('[4/5] CloudWatch Logs (last 72h)', 'bold')}")
    logs = check_cloudwatch_logs(args.stage)

    print(f"\n{colour('[5/5] Simulated write_strategy_metrics()', 'bold')}")
    simulated_ok = check_simulated_write(args.stage, args.verbose)

    print(f"\n{'=' * 70}")
    print(f"{colour('DIAGNOSIS', 'bold')}")
    print("=" * 70)

    print_diagnosis(perf_ok, ledger, lambda_ok, logs, simulated_ok)

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
