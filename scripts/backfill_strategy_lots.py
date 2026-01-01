#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Backfill Strategy Lots from Alpaca Trade History.

This script fetches historical trades from Alpaca and creates/updates StrategyLot
entries in DynamoDB. Use this to populate lot data for QuantStats reports when:

1. Initial deployment - no lot history exists
2. After fixing the SELL trade attribution bug (lots weren't being closed)
3. To reconcile lot data with actual Alpaca trades

The script:
- Fetches filled orders from Alpaca within a date range
- Parses client_order_id to extract strategy attribution
- Creates lots for BUY trades, matches exits for SELL trades (FIFO)
- Calculates realized P&L for closed lots

Usage:
    # Dry run (default) - shows what would be done
    python scripts/backfill_strategy_lots.py --stage prod --days 90

    # Actually write to DynamoDB
    python scripts/backfill_strategy_lots.py --stage prod --days 90 --execute

    # Specific date range
    python scripts/backfill_strategy_lots.py --stage prod --start 2025-10-01 --end 2025-12-31 --execute

Environment Variables:
    ALPACA_KEY: Alpaca API key (or uses AWS Secrets Manager)
    ALPACA_SECRET: Alpaca API secret
"""

from __future__ import annotations

import argparse
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Add shared layer to path for local execution
sys.path.insert(0, str(__file__.replace("scripts/backfill_strategy_lots.py", "layers/shared")))

from the_alchemiser.shared.utils.order_id_utils import parse_client_order_id

DynamoDBException = (ClientError, BotoCoreError)


@dataclass
class FilledOrder:
    """Parsed filled order from Alpaca."""

    order_id: str
    client_order_id: str | None
    symbol: str
    side: str  # "buy" or "sell"
    filled_qty: Decimal
    filled_avg_price: Decimal
    filled_at: datetime
    strategy_id: str | None = None


@dataclass
class OpenLot:
    """Represents an open position lot for FIFO matching."""

    lot_id: str
    strategy_name: str
    symbol: str
    entry_order_id: str
    entry_price: Decimal
    entry_qty: Decimal
    entry_timestamp: datetime
    remaining_qty: Decimal = field(init=False)

    def __post_init__(self) -> None:
        self.remaining_qty = self.entry_qty


@dataclass
class ClosedLot:
    """Represents a closed (or partially closed) lot."""

    lot_id: str
    strategy_name: str
    symbol: str
    entry_order_id: str
    entry_price: Decimal
    entry_qty: Decimal
    entry_timestamp: datetime
    exit_records: list[dict] = field(default_factory=list)
    is_open: bool = True
    remaining_qty: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    fully_closed_at: datetime | None = None


def get_alpaca_client(paper: bool = True):
    """Get Alpaca trading client.

    Args:
        paper: Whether to use paper trading API (default True for safety)

    """
    import os

    from alpaca.trading.client import TradingClient

    api_key = os.environ.get("ALPACA_KEY")
    secret_key = os.environ.get("ALPACA_SECRET")

    if not api_key or not secret_key:
        # Try AWS Secrets Manager
        try:
            secrets = boto3.client("secretsmanager")
            response = secrets.get_secret_value(SecretId="alchemiser/alpaca/prod")
            import json

            secret = json.loads(response["SecretString"])
            api_key = secret.get("api_key")
            secret_key = secret.get("api_secret")
        except Exception as e:
            print(f"ERROR: Could not get Alpaca credentials: {e}")
            print("Set ALPACA_KEY and ALPACA_SECRET environment variables")
            sys.exit(1)

    return TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)


def fetch_filled_orders(
    client,
    start_date: datetime,
    end_date: datetime,
) -> list[FilledOrder]:
    """Fetch all filled orders from Alpaca.

    Args:
        client: Alpaca TradingClient
        start_date: Start of date range
        end_date: End of date range

    Returns:
        List of FilledOrder objects

    """
    from alpaca.trading.enums import OrderStatus, QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest

    print(f"Fetching orders from {start_date.date()} to {end_date.date()}...")

    request = GetOrdersRequest(
        status=QueryOrderStatus.CLOSED,
        after=start_date,
        until=end_date,
        limit=500,
    )

    orders = client.get_orders(request)
    filled_orders: list[FilledOrder] = []

    for order in orders:
        # Skip non-filled orders
        if order.status != OrderStatus.FILLED:
            continue

        # Skip orders without fill data
        if not order.filled_avg_price or not order.filled_qty:
            continue

        # Parse strategy from client_order_id
        strategy_id = None
        if order.client_order_id:
            parsed = parse_client_order_id(order.client_order_id)
            if parsed:
                strategy_id = parsed.get("strategy_id")
                if strategy_id == "unknown":
                    strategy_id = None

        filled_orders.append(
            FilledOrder(
                order_id=str(order.id),
                client_order_id=order.client_order_id,
                symbol=order.symbol,
                side=order.side.value.lower(),
                filled_qty=Decimal(str(order.filled_qty)),
                filled_avg_price=Decimal(str(order.filled_avg_price)),
                filled_at=order.filled_at or order.submitted_at,
                strategy_id=strategy_id,
            )
        )

    # Sort by filled_at for proper FIFO processing
    filled_orders.sort(key=lambda o: o.filled_at)

    print(f"Found {len(filled_orders)} filled orders")

    # Count by strategy
    strategy_counts: dict[str, int] = defaultdict(int)
    for order in filled_orders:
        strategy_counts[order.strategy_id or "unknown"] += 1

    print("Orders by strategy:")
    for strategy, count in sorted(strategy_counts.items()):
        print(f"  {strategy}: {count}")

    return filled_orders


def process_orders_to_lots(orders: list[FilledOrder]) -> dict[str, list[ClosedLot]]:
    """Process orders into strategy lots using FIFO matching.

    Args:
        orders: List of filled orders sorted by date

    Returns:
        Dict mapping strategy_name to list of ClosedLot objects

    """
    # Track open lots per strategy+symbol
    open_lots: dict[str, dict[str, list[OpenLot]]] = defaultdict(lambda: defaultdict(list))

    # Final lots per strategy
    all_lots: dict[str, list[ClosedLot]] = defaultdict(list)

    for order in orders:
        if not order.strategy_id:
            continue

        strategy = order.strategy_id
        symbol = order.symbol

        if order.side == "buy":
            # Create new lot
            lot = OpenLot(
                lot_id=str(uuid.uuid4()),
                strategy_name=strategy,
                symbol=symbol,
                entry_order_id=order.order_id,
                entry_price=order.filled_avg_price,
                entry_qty=order.filled_qty,
                entry_timestamp=order.filled_at,
            )
            open_lots[strategy][symbol].append(lot)

        elif order.side == "sell":
            # FIFO match against open lots
            remaining_sell_qty = order.filled_qty
            symbol_lots = open_lots[strategy][symbol]

            while remaining_sell_qty > Decimal("0") and symbol_lots:
                lot = symbol_lots[0]

                # How much can we exit from this lot?
                exit_qty = min(remaining_sell_qty, lot.remaining_qty)

                # Calculate P&L for this exit
                entry_cost = lot.entry_price * exit_qty
                exit_proceeds = order.filled_avg_price * exit_qty
                exit_pnl = exit_proceeds - entry_cost

                # Update lot remaining qty
                lot.remaining_qty -= exit_qty
                remaining_sell_qty -= exit_qty

                # Create exit record
                exit_record = {
                    "exit_order_id": order.order_id,
                    "exit_price": str(order.filled_avg_price),
                    "exit_qty": str(exit_qty),
                    "exit_timestamp": order.filled_at.isoformat(),
                    "exit_pnl": str(exit_pnl),
                }

                # Check if lot is fully closed
                if lot.remaining_qty <= Decimal("0.0001"):
                    # Lot is closed - move to closed lots
                    closed = ClosedLot(
                        lot_id=lot.lot_id,
                        strategy_name=lot.strategy_name,
                        symbol=lot.symbol,
                        entry_order_id=lot.entry_order_id,
                        entry_price=lot.entry_price,
                        entry_qty=lot.entry_qty,
                        entry_timestamp=lot.entry_timestamp,
                        exit_records=[exit_record],
                        is_open=False,
                        remaining_qty=Decimal("0"),
                        realized_pnl=exit_pnl,
                        fully_closed_at=order.filled_at,
                    )
                    all_lots[strategy].append(closed)
                    symbol_lots.pop(0)  # Remove from open lots
                else:
                    # Lot still open - record partial exit
                    # (We'll handle partial closes as separate closed entries)
                    pass

            if remaining_sell_qty > Decimal("0.001"):
                print(
                    f"  WARNING: Unmatched SELL qty for {strategy}/{symbol}: "
                    f"{remaining_sell_qty} (pre-existing position?)"
                )

    # Also add any remaining open lots
    for strategy, symbols in open_lots.items():
        for symbol, lots in symbols.items():
            for lot in lots:
                if lot.remaining_qty > Decimal("0.0001"):
                    open_closed = ClosedLot(
                        lot_id=lot.lot_id,
                        strategy_name=lot.strategy_name,
                        symbol=lot.symbol,
                        entry_order_id=lot.entry_order_id,
                        entry_price=lot.entry_price,
                        entry_qty=lot.entry_qty,
                        entry_timestamp=lot.entry_timestamp,
                        is_open=True,
                        remaining_qty=lot.remaining_qty,
                    )
                    all_lots[strategy].append(open_closed)

    return all_lots


def write_lots_to_dynamodb(
    lots: dict[str, list[ClosedLot]],
    table_name: str,
    *,
    dry_run: bool = True,
) -> None:
    """Write lots to DynamoDB.

    Args:
        lots: Dict mapping strategy_name to list of ClosedLot
        table_name: DynamoDB table name
        dry_run: If True, just print what would be done

    """
    if dry_run:
        print("\n=== DRY RUN - No changes will be made ===\n")
    else:
        print("\n=== EXECUTING - Writing to DynamoDB ===\n")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    total_written = 0
    total_closed = 0
    total_open = 0

    for strategy, strategy_lots in sorted(lots.items()):
        closed = [lot for lot in strategy_lots if not lot.is_open]
        open_lots = [lot for lot in strategy_lots if lot.is_open]

        print(f"Strategy: {strategy}")
        print(f"  Closed lots: {len(closed)}")
        print(f"  Open lots: {len(open_lots)}")

        total_pnl = sum(lot.realized_pnl for lot in closed)
        print(f"  Total realized P&L: ${total_pnl:.2f}")

        if closed:
            dates = [lot.fully_closed_at for lot in closed if lot.fully_closed_at]
            if dates:
                print(f"  Date range: {min(dates).date()} to {max(dates).date()}")

        total_closed += len(closed)
        total_open += len(open_lots)

        if not dry_run:
            for lot in strategy_lots:
                item = _lot_to_dynamodb_item(lot)
                try:
                    table.put_item(Item=item)
                    total_written += 1
                except DynamoDBException as e:
                    print(f"  ERROR writing lot {lot.lot_id}: {e}")

    print(f"\n{'Would write' if dry_run else 'Wrote'}: {total_closed} closed + {total_open} open lots")
    if not dry_run:
        print(f"Successfully wrote: {total_written} lots")


def _lot_to_dynamodb_item(lot: ClosedLot) -> dict[str, Any]:
    """Convert ClosedLot to DynamoDB item format."""
    # PK/SK pattern: LOT#{lot_id} / SYMBOL#{symbol}
    pk = f"LOT#{lot.lot_id}"
    sk = f"SYMBOL#{lot.symbol}"

    # GSI5 for strategy queries: STRATEGY_LOTS#{name} / CLOSED#timestamp or OPEN#timestamp
    if lot.is_open:
        gsi5sk = f"OPEN#{lot.entry_timestamp.isoformat()}"
    else:
        gsi5sk = f"CLOSED#{lot.fully_closed_at.isoformat() if lot.fully_closed_at else lot.entry_timestamp.isoformat()}"

    item: dict[str, Any] = {
        "PK": pk,
        "SK": sk,
        "lot_id": lot.lot_id,
        "strategy_name": lot.strategy_name,
        "symbol": lot.symbol,
        "entry_order_id": lot.entry_order_id,
        "entry_price": str(lot.entry_price),
        "entry_qty": str(lot.entry_qty),
        "entry_timestamp": lot.entry_timestamp.isoformat(),
        "remaining_qty": str(lot.remaining_qty),
        "is_open": lot.is_open,
        "realized_pnl": str(lot.realized_pnl),
        "GSI5PK": f"STRATEGY_LOTS#{lot.strategy_name}",
        "GSI5SK": gsi5sk,
        "created_at": datetime.now(UTC).isoformat(),
        "backfill_source": "alpaca_history",
    }

    if lot.exit_records:
        item["exit_records"] = lot.exit_records

    if lot.fully_closed_at:
        item["fully_closed_at"] = lot.fully_closed_at.isoformat()

    return item


def main() -> int:
    """Run the backfill script."""
    parser = argparse.ArgumentParser(
        description="Backfill Strategy Lots from Alpaca Trade History",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--stage",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Deployment stage (default: dev)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Days of history to fetch (default: 90)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD) - overrides --days",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD) - defaults to today",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write to DynamoDB (default is dry run)",
    )

    args = parser.parse_args()

    # Determine date range
    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=UTC)
    else:
        start_date = datetime.now(UTC) - timedelta(days=args.days)

    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=UTC)
    else:
        end_date = datetime.now(UTC)

    table_name = f"alchemiser-{args.stage}-trade-ledger"

    # Determine paper mode based on stage (only prod uses live API)
    paper_mode = args.stage != "prod"

    print("=" * 60)
    print("Strategy Lots Backfill")
    print("=" * 60)
    print(f"Stage: {args.stage}")
    print(f"Table: {table_name}")
    print(f"Alpaca API: {'PAPER' if paper_mode else 'LIVE'}")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print("=" * 60)

    # Get Alpaca client (paper=True for dev/staging, paper=False for prod)
    client = get_alpaca_client(paper=paper_mode)

    # Fetch orders
    orders = fetch_filled_orders(client, start_date, end_date)

    if not orders:
        print("\nNo filled orders found in date range")
        return 0

    # Process to lots
    print("\nProcessing orders into strategy lots...")
    lots = process_orders_to_lots(orders)

    if not lots:
        print("No lots could be created (no strategy attribution in orders)")
        return 0

    # Write to DynamoDB
    write_lots_to_dynamodb(lots, table_name, dry_run=not args.execute)

    if not args.execute:
        print("\nTo actually write to DynamoDB, run with --execute flag")

    return 0


if __name__ == "__main__":
    sys.exit(main())
