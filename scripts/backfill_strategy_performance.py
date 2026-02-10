#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Backfill strategy performance metrics from TradeLedger to StrategyPerformanceTable.

Manually triggers the same write_strategy_metrics() logic that the
StrategyPerformanceFunction Lambda uses, but from a local script.

Useful when:
- No TradeExecuted events have fired since deployment
- Need to populate data for the first time after migration

Usage:
    python scripts/backfill_strategy_performance.py --stage prod --dry-run
    python scripts/backfill_strategy_performance.py --stage prod
"""

from __future__ import annotations

import argparse
import sys
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

from the_alchemiser.shared.metrics.dynamodb_metrics_publisher import DynamoDBMetricsPublisher
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)

REGION = "us-east-1"

# ANSI colour codes
COLOURS = {
    "reset": "\033[0m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "green": "\033[92m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
}

_use_colour = True


def colour(text: str, colour_name: str) -> str:
    """Apply ANSI colour to text."""
    if not _use_colour:
        return str(text)
    return f"{COLOURS.get(colour_name, '')}{text}{COLOURS['reset']}"


def run_backfill(stage: str, dry_run: bool) -> int:
    """Execute the backfill."""
    trade_ledger_table = f"alchemiser-{stage}-trade-ledger"
    strategy_performance_table = f"alchemiser-{stage}-strategy-performance"
    correlation_id = f"backfill-{uuid.uuid4()}"

    # Preview: read summaries from TradeLedger
    print(f"\n   Reading from {trade_ledger_table}...")
    repo = DynamoDBTradeLedgerRepository(trade_ledger_table)
    summaries = repo.get_all_strategy_summaries()

    if not summaries:
        print(f"   {colour('No strategy summaries found in TradeLedger.', 'yellow')}")
        print("   Nothing to backfill. Ensure strategy metadata is synced and lots exist.")
        return 1

    print(f"   Found {len(summaries)} strategies:\n")
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

    if dry_run:
        print(f"\n   {colour('DRY RUN', 'yellow')} -- No data written.")
        print(f"   Would write to: {strategy_performance_table}")
        return 0

    # Execute write using the same publisher the Lambda uses
    print(f"\n   Writing to {strategy_performance_table}...")
    publisher = DynamoDBMetricsPublisher(
        trade_ledger_table_name=trade_ledger_table,
        strategy_performance_table_name=strategy_performance_table,
    )
    publisher.write_strategy_metrics(correlation_id)

    # Verify
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(strategy_performance_table)
    response = table.query(
        KeyConditionExpression=(Key("PK").eq("LATEST") & Key("SK").begins_with("STRATEGY#")),
    )
    written_count = len(response.get("Items", []))

    print(f"\n   {colour('DONE', 'green')} -- {written_count} LATEST strategy items in table.")
    print(f"   Correlation ID: {correlation_id}")
    return 0


def main() -> int:
    """Parse arguments and run backfill."""
    parser = argparse.ArgumentParser(
        description="Backfill strategy performance metrics from TradeLedger",
    )
    parser.add_argument("--stage", choices=["dev", "prod"], default="dev")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--no-colour", "--no-color", action="store_true")

    args = parser.parse_args()

    global _use_colour
    _use_colour = not args.no_colour

    mode = "DRY RUN" if args.dry_run else colour("LIVE WRITE", "red")

    print(f"\n{colour('STRATEGY PERFORMANCE BACKFILL', 'bold')}")
    print(f"Stage: {colour(args.stage.upper(), 'cyan')}")
    print(f"Mode:  {mode}")
    print("=" * 70)

    return run_backfill(args.stage, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
