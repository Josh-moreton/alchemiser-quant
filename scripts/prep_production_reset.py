#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Production Environment Reset
==============================
Prepares the production environment for migration to per-ledger books by:

1. Liquidating ALL open Alpaca positions (market orders during market hours)
2. Cancelling ALL open Alpaca orders
3. Wiping DynamoDB tables: trade ledger, execution runs, rebalance plans, group history
4. Wiping S3 performance reports bucket

This script is DESTRUCTIVE and requires explicit --confirm flag plus
interactive confirmation to proceed. Use --dry-run to preview actions.

Usage:
    # Dry run (preview only, no changes):
    python scripts/prep_production_reset.py --dry-run

    # Target a specific stage (default: prod):
    python scripts/prep_production_reset.py --stage dev --dry-run

    # Live execution (will prompt for confirmation):
    python scripts/prep_production_reset.py --confirm

    # Skip interactive prompt:
    python scripts/prep_production_reset.py --confirm --yes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE any shared imports that might read env vars
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

import _setup_imports  # noqa: F401, E402

import boto3  # noqa: E402
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys  # noqa: E402
from alpaca.trading.client import TradingClient  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGION = "us-east-1"

# DynamoDB table suffixes (combined with alch-{stage}- prefix)
TABLE_SUFFIXES = [
    "trade-ledger",
    "execution-runs",
    "rebalance-plans",
]

# S3 bucket suffix
PERFORMANCE_BUCKET_SUFFIX = "performance-reports"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset production environment for per-ledger book migration.",
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Target stage (default: prod).",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required flag to allow destructive operations.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making any changes.",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip interactive confirmation prompt.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Alpaca: Liquidation
# ---------------------------------------------------------------------------


def _build_trade_client() -> TradingClient:
    api_key, secret_key, endpoint = get_alpaca_keys()
    paper = "paper" in (endpoint or "paper").lower()
    print(f"  Endpoint : {endpoint or '(default paper)'}")
    print(f"  Mode     : {'PAPER' if paper else 'LIVE'}")
    return TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)


def _print_positions(trade_client: TradingClient) -> list[object]:
    positions = list(trade_client.get_all_positions())
    if not positions:
        print("  No open positions.")
        return positions

    header = f"  {'Symbol':<10} {'Side':<6} {'Qty':>10} {'Mkt Value':>14} {'P&L':>12}"
    print(f"\n{header}")
    print(f"  {'-' * (len(header.strip()))}")
    for pos in positions:
        symbol = getattr(pos, "symbol", "???")
        qty = getattr(pos, "qty", "0")
        side = str(getattr(pos, "side", "long")).split(".")[-1].upper()
        mkt_val = getattr(pos, "market_value", "0")
        pnl = getattr(pos, "unrealized_pl", "0")
        print(f"  {symbol:<10} {side:<6} {str(qty):>10} ${str(mkt_val):>12} ${str(pnl):>10}")
    return positions


def liquidate_all_positions(trade_client: TradingClient, *, dry_run: bool) -> None:
    """Cancel all open orders and liquidate all positions via Alpaca."""
    print("\n--- Step 1: Alpaca Positions & Orders ---\n")

    # Show account info
    account = trade_client.get_account()
    print(f"  Account : {getattr(account, 'account_number', 'N/A')}")
    print(f"  Equity  : ${getattr(account, 'equity', 'N/A')}")
    print(f"  Cash    : ${getattr(account, 'cash', 'N/A')}")

    # Show and count positions
    positions = _print_positions(trade_client)

    if dry_run:
        if positions:
            print(f"\n  [DRY-RUN] Would cancel all open orders")
            print(f"  [DRY-RUN] Would liquidate {len(positions)} positions")
        return

    # Cancel all open orders first
    print("\n  Cancelling all open orders...")
    try:
        trade_client.cancel_orders()
        print("  All open orders cancelled.")
    except Exception as exc:
        print(f"  [WARN] Cancel orders failed: {exc}")

    if not positions:
        return

    # Close all positions (Alpaca handles this atomically)
    print(f"  Closing {len(positions)} positions...")
    try:
        trade_client.close_all_positions(cancel_orders=True)
        print("  Close-all-positions request submitted.")
        print("  NOTE: Orders may take time to fill. Check Alpaca dashboard for status.")
    except Exception as exc:
        print(f"  [ERROR] Failed to close positions: {exc}")
        print("  You may need to close positions manually via the Alpaca dashboard.")


# ---------------------------------------------------------------------------
# DynamoDB: Table Clearing
# ---------------------------------------------------------------------------


def _get_key_attr_names(table_resource: object) -> list[str]:
    key_schema = table_resource.key_schema  # type: ignore[attr-defined]
    return [k["AttributeName"] for k in key_schema]


def clear_dynamo_table(table_name: str, *, dry_run: bool) -> int:
    """Delete all items from a DynamoDB table."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(table_name)

    # Check table exists and get item count
    try:
        item_count = table.item_count
    except Exception as exc:
        print(f"  [SKIP] Table {table_name} not accessible: {exc}")
        return 0

    if dry_run:
        print(f"  [DRY-RUN] Would clear ~{item_count} items from {table_name}")
        return 0

    key_attrs = _get_key_attr_names(table)
    projection_expr = ", ".join(key_attrs)

    total = 0
    scan_kwargs: dict[str, object] = {"ProjectionExpression": projection_expr}

    while True:
        resp = table.scan(**scan_kwargs)
        items = resp.get("Items", [])
        if not items:
            break
        with table.batch_writer() as batch:
            for item in items:
                key = {attr: item[attr] for attr in key_attrs if attr in item}
                batch.delete_item(Key=key)
        total += len(items)
        print(f"    Deleted {len(items)} items ({total} total)")
        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    return total


def clear_all_tables(stage: str, *, dry_run: bool) -> None:
    """Clear all DynamoDB tables for the given stage."""
    print("\n--- Step 2: DynamoDB Tables ---\n")

    for suffix in TABLE_SUFFIXES:
        table_name = f"alch-{stage}-{suffix}"
        print(f"  {table_name}:")
        removed = clear_dynamo_table(table_name, dry_run=dry_run)
        if not dry_run:
            print(f"    Done: {removed} items removed")


# ---------------------------------------------------------------------------
# S3: Performance Reports Bucket
# ---------------------------------------------------------------------------


def clear_s3_bucket(stage: str, *, dry_run: bool) -> None:
    """Empty the performance reports S3 bucket."""
    print("\n--- Step 3: S3 Performance Reports ---\n")

    bucket_name = f"alch-{stage}-{PERFORMANCE_BUCKET_SUFFIX}"
    s3 = boto3.client("s3", region_name=REGION)

    # Count objects
    total_objects = 0
    paginator = s3.get_paginator("list_objects_v2")

    try:
        for page in paginator.paginate(Bucket=bucket_name):
            total_objects += page.get("KeyCount", 0)
    except s3.exceptions.NoSuchBucket:
        print(f"  [SKIP] Bucket {bucket_name} does not exist.")
        return
    except Exception as exc:
        print(f"  [SKIP] Cannot access bucket {bucket_name}: {exc}")
        return

    if total_objects == 0:
        print(f"  Bucket {bucket_name} is already empty.")
        return

    if dry_run:
        print(f"  [DRY-RUN] Would delete ~{total_objects} objects from {bucket_name}")
        return

    # Delete all objects in batches of 1000
    deleted = 0
    for page in paginator.paginate(Bucket=bucket_name):
        contents = page.get("Contents", [])
        if not contents:
            break

        objects = [{"Key": obj["Key"]} for obj in contents]
        s3.delete_objects(
            Bucket=bucket_name,
            Delete={"Objects": objects, "Quiet": True},
        )
        deleted += len(objects)
        print(f"    Deleted {len(objects)} objects ({deleted} total)")

    print(f"  Done: {deleted} objects removed from {bucket_name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = _parse_args()
    stage = args.stage

    print(f"\n{'=' * 55}")
    print(f"  PRODUCTION ENVIRONMENT RESET -- stage: {stage.upper()}")
    print(f"{'=' * 55}\n")

    if args.dry_run:
        print("  *** DRY-RUN MODE -- no changes will be made ***\n")

    # Build resource names for summary
    tables = [f"alch-{stage}-{s}" for s in TABLE_SUFFIXES]
    bucket = f"alch-{stage}-{PERFORMANCE_BUCKET_SUFFIX}"

    print("  This script will:")
    print("    1. Cancel all open Alpaca orders")
    print("    2. Liquidate all open Alpaca positions")
    print("    3. Wipe DynamoDB tables:")
    for t in tables:
        print(f"       - {t}")
    print(f"    4. Empty S3 bucket: {bucket}")

    # Safety gate
    if not args.dry_run:
        if not args.confirm:
            print("\n  Re-run with --confirm to allow destructive operations.")
            sys.exit(1)

        if not args.yes:
            print(f"\n  WARNING: This will DESTROY all data for stage '{stage}'.")
            confirm = input("  Type 'RESET' to proceed: ").strip()
            if confirm != "RESET":
                print("  Aborted.")
                sys.exit(0)

    # Execute
    print("\nConnecting to Alpaca...")
    trade_client = _build_trade_client()
    liquidate_all_positions(trade_client, dry_run=args.dry_run)

    clear_all_tables(stage, dry_run=args.dry_run)
    clear_s3_bucket(stage, dry_run=args.dry_run)

    print(f"\n{'=' * 55}")
    if args.dry_run:
        print("  DRY-RUN complete. No changes were made.")
    else:
        print("  RESET complete. Environment is ready for per-ledger migration.")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
