#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Backfill historical trades from Alpaca to the Trade Ledger DynamoDB table.

This script fetches all closed/filled orders from Alpaca and writes them to the
Trade Ledger for portfolio-wide quantstats reporting. Historical trades cannot
be attributed to specific strategies, so strategy_names will be empty.

Usage:
    # Preview what will be written (recommended first run)
    python scripts/backfill_alpaca_trades.py --dry-run

    # Backfill to dev table (default)
    python scripts/backfill_alpaca_trades.py --stage dev

    # Backfill to prod table
    python scripts/backfill_alpaca_trades.py --stage prod

    # Use live account instead of paper
    python scripts/backfill_alpaca_trades.py --live

    # Filter by date range
    python scripts/backfill_alpaca_trades.py --start-date 2024-01-01 --end-date 2024-12-31

Environment Variables:
    ALPACA_KEY or ALPACA__KEY: Alpaca API key
    ALPACA_SECRET or ALPACA__SECRET: Alpaca API secret
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

# Get project root for .env file loading
project_root = _setup_imports.PROJECT_ROOT

# Load .env file automatically (same pattern as check_fractionable_assets.py)
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    if key not in os.environ:
                        os.environ[key] = value

import logging

# Suppress verbose logging from boto3, botocore, urllib3, and alpaca
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("alpaca").setLevel(logging.WARNING)

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)
from the_alchemiser.shared.schemas.trade_ledger import TradeLedgerEntry

# Configure logging - suppress debug output for cleaner CLI experience
configure_application_logging()
logger = get_logger(__name__)

# Also suppress structlog output to WARNING for this script
logging.getLogger("the_alchemiser").setLevel(logging.WARNING)


def get_credentials() -> tuple[str, str]:
    """Load Alpaca credentials from environment variables.

    Returns:
        Tuple of (api_key, secret_key)

    Raises:
        SystemExit: If credentials are missing
    """
    api_key = os.environ.get("ALPACA__KEY") or os.environ.get("ALPACA_KEY")
    secret_key = os.environ.get("ALPACA__SECRET") or os.environ.get("ALPACA_SECRET")

    missing = []
    if not api_key:
        missing.append("ALPACA_KEY or ALPACA__KEY")
    if not secret_key:
        missing.append("ALPACA_SECRET or ALPACA__SECRET")

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Set these in your .env file or environment.")
        sys.exit(1)

    return api_key, secret_key


def map_order_type(alpaca_type: str) -> str:
    """Map Alpaca order type to TradeLedgerEntry order_type.

    Args:
        alpaca_type: Alpaca order type string (e.g., 'market', 'limit')

    Returns:
        Uppercase order type for TradeLedgerEntry
    """
    type_map = {
        "market": "MARKET",
        "limit": "LIMIT",
        "stop": "STOP",
        "stop_limit": "STOP_LIMIT",
    }
    return type_map.get(alpaca_type.lower(), "MARKET")


def format_trade(order: Any) -> str:
    """Format a trade for display.

    Args:
        order: Alpaca Order object

    Returns:
        Formatted string for display
    """
    filled_at = order.filled_at
    if filled_at:
        ts = filled_at.strftime("%Y-%m-%d %H:%M:%S")
    else:
        ts = "N/A"

    side = str(order.side.name).upper() if hasattr(order.side, "name") else str(order.side).upper()
    symbol = order.symbol
    qty = float(order.filled_qty) if order.filled_qty else 0.0
    price = float(order.filled_avg_price) if order.filled_avg_price else 0.0

    return f"  {ts} | {side:4s} | {symbol:5s} | {qty:>8.2f} @ ${price:>10.2f}"


def fetch_filled_orders(
    manager: AlpacaManager,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[Any]:
    """Fetch filled orders from Alpaca.

    Args:
        manager: AlpacaManager instance
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)

    Returns:
        List of filled Order objects
    """
    print("Fetching closed orders from Alpaca...")
    orders = manager.get_orders(status="closed")

    # Filter to filled orders only
    filled_orders = []
    for order in orders:
        status = str(order.status.name).lower() if hasattr(order.status, "name") else str(order.status).lower()
        if status == "filled":
            # Apply date filters if provided
            if order.filled_at:
                if start_date and order.filled_at.date().isoformat() < start_date:
                    continue
                if end_date and order.filled_at.date().isoformat() > end_date:
                    continue
            filled_orders.append(order)

    return filled_orders


def check_existing_trades(
    repository: DynamoDBTradeLedgerRepository,
    orders: list[Any],
) -> tuple[list[Any], int]:
    """Check which orders already exist in the ledger.

    Args:
        repository: DynamoDB repository
        orders: List of orders to check

    Returns:
        Tuple of (new_orders, existing_count)
    """
    print("Checking for existing trades in ledger...")
    new_orders = []
    existing_count = 0

    for order in orders:
        order_id = str(order.id)
        existing = repository.get_trade(order_id)
        if existing:
            existing_count += 1
        else:
            new_orders.append(order)

    return new_orders, existing_count


def create_ledger_entry(order: Any, correlation_id: str) -> TradeLedgerEntry | None:
    """Create a TradeLedgerEntry from an Alpaca order.

    Args:
        order: Alpaca Order object
        correlation_id: Correlation ID for this backfill session

    Returns:
        TradeLedgerEntry or None if order is invalid
    """
    # Validate required fields - convert to Decimal first since Alpaca returns strings
    try:
        filled_qty = Decimal(str(order.filled_qty)) if order.filled_qty else Decimal("0")
        fill_price = Decimal(str(order.filled_avg_price)) if order.filled_avg_price else Decimal("0")
    except Exception as e:
        logger.warning(f"Skipping order {order.id}: invalid qty/price - {e}")
        return None

    if filled_qty <= 0:
        logger.warning(f"Skipping order {order.id}: missing or zero filled_qty")
        return None
    if fill_price <= 0:
        logger.warning(f"Skipping order {order.id}: missing or zero filled_avg_price")
        return None
    if not order.filled_at:
        logger.warning(f"Skipping order {order.id}: missing filled_at timestamp")
        return None

    # Map side to direction
    side = str(order.side.name).upper() if hasattr(order.side, "name") else str(order.side).upper()
    if side not in ("BUY", "SELL"):
        logger.warning(f"Skipping order {order.id}: invalid side {side}")
        return None

    # Map order type
    order_type_str = str(order.type.name).lower() if hasattr(order.type, "name") else str(order.type).lower()
    order_type = map_order_type(order_type_str)

    return TradeLedgerEntry(
        order_id=str(order.id),
        correlation_id=correlation_id,
        symbol=order.symbol,
        direction=side,
        filled_qty=filled_qty,
        fill_price=fill_price,
        fill_timestamp=order.filled_at,
        order_type=order_type,
        strategy_names=[],  # Cannot attribute historical trades
        strategy_weights=None,
    )


def backfill_trades(
    repository: DynamoDBTradeLedgerRepository,
    orders: list[Any],
    correlation_id: str,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Backfill trades to DynamoDB.

    Args:
        repository: DynamoDB repository
        orders: List of orders to backfill
        correlation_id: Correlation ID for this session
        dry_run: If True, don't actually write

    Returns:
        Tuple of (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    total = len(orders)

    for i, order in enumerate(orders, 1):
        entry = create_ledger_entry(order, correlation_id)
        if entry is None:
            error_count += 1
            continue

        if dry_run:
            success_count += 1
            continue

        try:
            repository.put_trade(entry, ledger_id="backfill")
            success_count += 1

            # Progress indicator
            if i % 10 == 0 or i == total:
                pct = int(i / total * 100)
                bar_width = 30
                filled = int(bar_width * i / total)
                bar = "=" * filled + " " * (bar_width - filled)
                print(f"\rProgress: [{bar}] {i}/{total} ({pct}%)", end="", flush=True)

        except Exception as e:
            logger.error(f"Failed to write trade {order.id}: {e}")
            error_count += 1

    if not dry_run and total > 0:
        print()  # Newline after progress bar

    return success_count, error_count


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill historical trades from Alpaca to Trade Ledger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--stage",
        choices=["dev", "prod"],
        default="dev",
        help="Target DynamoDB table stage (default: dev)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what will be written without actually writing",
    )
    parser.add_argument(
        "--paper",
        action="store_true",
        default=True,
        help="Use paper trading account (default)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live trading account",
    )
    parser.add_argument(
        "--start-date",
        help="Filter orders filled on or after this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        help="Filter orders filled on or before this date (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    # Determine paper vs live
    use_paper = not args.live

    # Get table name
    table_name = f"alchemiser-{args.stage}-trade-ledger"
    print(f"Target table: {table_name}")
    print(f"Account type: {'paper' if use_paper else 'LIVE'}")
    if args.dry_run:
        print("Mode: DRY RUN (no writes)")
    print()

    # Get credentials
    api_key, secret_key = get_credentials()

    # Create Alpaca manager
    try:
        manager = AlpacaManager(api_key=api_key, secret_key=secret_key, paper=use_paper)
    except Exception as e:
        print(f"ERROR: Failed to create Alpaca client: {e}")
        return 1

    # Fetch filled orders
    try:
        orders = fetch_filled_orders(manager, args.start_date, args.end_date)
    except Exception as e:
        print(f"ERROR: Failed to fetch orders: {e}")
        return 1

    print(f"Found {len(orders)} filled orders from Alpaca")

    if not orders:
        print("No orders to backfill.")
        return 0

    # Create repository and check for existing trades
    try:
        repository = DynamoDBTradeLedgerRepository(table_name)
    except Exception as e:
        print(f"ERROR: Failed to connect to DynamoDB: {e}")
        return 1

    new_orders, existing_count = check_existing_trades(repository, orders)

    print(f"Existing in ledger: {existing_count} (will skip)")
    print(f"New trades to write: {len(new_orders)}")
    print()

    if not new_orders:
        print("All trades already exist in ledger. Nothing to do.")
        return 0

    # Generate correlation ID for this backfill session
    correlation_id = f"backfill-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

    # Show sample trades
    print("Sample trades:")
    sample_size = min(5, len(new_orders))
    for order in new_orders[:sample_size]:
        print(format_trade(order))
    if len(new_orders) > sample_size:
        print(f"  ... and {len(new_orders) - sample_size} more")
    print()

    if args.dry_run:
        print(f"Run without --dry-run to write to {table_name}")
        return 0

    # Perform backfill
    print(f"Backfilling {len(new_orders)} trades to {table_name}...")
    success_count, error_count = backfill_trades(
        repository, new_orders, correlation_id, dry_run=False
    )

    print()
    print(f"Done! Wrote {success_count} trades.")
    if error_count > 0:
        print(f"Errors: {error_count} trades failed to write.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
