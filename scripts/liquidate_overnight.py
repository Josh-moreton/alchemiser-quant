#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Overnight Liquidation Script
=============================
Liquidates all open positions using Alpaca's 24/5 overnight trading session.

During overnight hours (8:00 PM - 4:00 AM ET), only LIMIT orders with
time_in_force=DAY and extended_hours=True are accepted. This script:

1. Fetches all open positions
2. Cancels any existing open orders
3. Gets latest overnight quotes for each position
4. Submits aggressive LIMIT orders to close each position
5. Monitors fill progress until all orders are filled or timeout

Usage:
    # Dry run (shows what would happen, no orders placed):
    python scripts/liquidate_overnight.py --dry-run

    # Live liquidation:
    python scripts/liquidate_overnight.py

    # Custom limit price aggressiveness (default: 3% discount/premium):
    python scripts/liquidate_overnight.py --slippage 0.05

    # Skip confirmation prompt:
    python scripts/liquidate_overnight.py --yes

    # Custom poll timeout (seconds, default: 300):
    python scripts/liquidate_overnight.py --timeout 600

Requirements:
    - Alpaca 24/5 overnight session must be active (8:00 PM - 4:00 AM ET)
    - .env file in project root with ALPACA_KEY, ALPACA_SECRET, ALPACA_ENDPOINT
    - Assets must have overnight_tradable attribute

Ref: https://alpaca.markets/learn/how-to-trade-us-stocks-24_5-overnight-with-python-and-alpaca
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE any shared imports that might read env vars
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

# Setup shared layer imports
import _setup_imports  # noqa: F401, E402

from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys  # noqa: E402

from alpaca.trading.client import TradingClient  # noqa: E402
from alpaca.trading.requests import (  # noqa: E402
    GetOrdersRequest,
    LimitOrderRequest,
)
from alpaca.trading.enums import (  # noqa: E402
    OrderSide,
    QueryOrderStatus,
    TimeInForce,
)
from alpaca.data.historical.stock import StockHistoricalDataClient  # noqa: E402
from alpaca.data.requests import StockLatestQuoteRequest  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SLIPPAGE = Decimal("0.03")  # 3% price discount/premium for aggressive fills
DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes polling timeout
POLL_INTERVAL_SECONDS = 5
PRICE_PRECISION = Decimal("0.01")  # Round prices to cents


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Liquidate all positions via Alpaca 24/5 overnight LIMIT orders.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would happen without placing any orders.",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        default=False,
        help="Skip confirmation prompt.",
    )
    parser.add_argument(
        "--slippage",
        type=Decimal,
        default=DEFAULT_SLIPPAGE,
        help=f"Limit price aggressiveness as a decimal fraction (default: {DEFAULT_SLIPPAGE})."
        " For sells: price = bid * (1 - slippage). For buys: price = ask * (1 + slippage).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Max seconds to poll for order fills (default: {DEFAULT_TIMEOUT_SECONDS}).",
    )
    return parser.parse_args()


def _build_clients() -> tuple[TradingClient, StockHistoricalDataClient]:
    """Build Alpaca trading and data clients from .env credentials."""
    api_key, secret_key, endpoint = get_alpaca_keys()
    paper = "paper" in (endpoint or "paper").lower()

    print(f"  Endpoint : {endpoint or '(default paper)'}")
    print(f"  Mode     : {'PAPER' if paper else 'LIVE'}")

    trade_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
    data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
    return trade_client, data_client


def _get_positions(trade_client: TradingClient) -> list[object]:
    """Fetch all open positions."""
    positions = trade_client.get_all_positions()
    return list(positions)


def _print_positions_table(positions: list[object]) -> None:
    """Print a formatted table of open positions."""
    if not positions:
        print("\n  No open positions found. Nothing to liquidate.")
        return

    header = f"  {'Symbol':<10} {'Side':<6} {'Qty':>12} {'Avg Entry':>12} {'Current':>12} {'Mkt Value':>14} {'P&L':>12}"
    print(f"\n{header}")
    print(f"  {'-' * len(header.strip())}")

    for pos in positions:
        symbol = getattr(pos, "symbol", "???")
        qty = getattr(pos, "qty", "0")
        side = getattr(pos, "side", "long")
        avg_entry = getattr(pos, "avg_entry_price", "0")
        current_price = getattr(pos, "current_price", "0")
        market_value = getattr(pos, "market_value", "0")
        unrealized_pl = getattr(pos, "unrealized_pl", "0")

        side_str = str(side).split(".")[-1].upper() if "." in str(side) else str(side).upper()

        print(
            f"  {symbol:<10} {side_str:<6} {str(qty):>12} "
            f"${str(avg_entry):>10} ${str(current_price):>10} "
            f"${str(market_value):>12} ${str(unrealized_pl):>10}"
        )


def _check_overnight_tradable(trade_client: TradingClient, symbol: str) -> bool:
    """Check if an asset is eligible for overnight trading."""
    try:
        asset = trade_client.get_asset(symbol)
        attributes = getattr(asset, "attributes", []) or []
        return "overnight_tradable" in attributes
    except Exception as exc:
        print(f"  [WARN] Could not check overnight eligibility for {symbol}: {exc}")
        return False


def _get_latest_quote(
    data_client: StockHistoricalDataClient,
    symbol: str,
) -> tuple[Decimal | None, Decimal | None]:
    """Fetch the latest bid/ask prices for a symbol.

    Tries the overnight feed first, falls back to IEX if unavailable.

    Returns:
        (bid_price, ask_price) as Decimals, or (None, None) on failure.
    """
    for feed_name in ("overnight", "iex"):
        try:
            # Build request params -- use string feed to avoid enum issues
            # across alpaca-py versions
            request_params = StockLatestQuoteRequest(
                symbol_or_symbols=[symbol],
                feed=feed_name,
            )
            quotes = data_client.get_stock_latest_quote(request_params)
            quote = quotes.get(symbol)
            if quote is None:
                continue
            bid = Decimal(str(quote.bid_price)) if quote.bid_price else None
            ask = Decimal(str(quote.ask_price)) if quote.ask_price else None
            if bid and ask and bid > 0 and ask > 0:
                return bid, ask
        except Exception:
            continue

    return None, None


def _calculate_limit_price(
    side: OrderSide,
    bid: Decimal,
    ask: Decimal,
    slippage: Decimal,
) -> Decimal:
    """Calculate an aggressive limit price for overnight fills.

    For SELL orders (liquidating longs): price below the bid to ensure fill.
    For BUY orders (covering shorts): price above the ask to ensure fill.
    """
    if side == OrderSide.SELL:
        price = bid * (Decimal("1") - slippage)
        return price.quantize(PRICE_PRECISION, rounding=ROUND_DOWN)
    else:
        price = ask * (Decimal("1") + slippage)
        return price.quantize(PRICE_PRECISION, rounding=ROUND_UP)


def _submit_liquidation_orders(
    trade_client: TradingClient,
    data_client: StockHistoricalDataClient,
    positions: list[object],
    slippage: Decimal,
    dry_run: bool,
) -> list[dict[str, str]]:
    """Submit limit orders to liquidate all positions.

    Returns:
        List of dicts with keys: symbol, order_id, side, qty, limit_price, status
    """
    results: list[dict[str, str]] = []

    for pos in positions:
        symbol = str(getattr(pos, "symbol", "???"))
        qty_raw = getattr(pos, "qty", "0")
        qty = str(qty_raw).lstrip("-")  # Ensure positive qty
        side_raw = str(getattr(pos, "side", "long"))

        # Determine liquidation side (opposite of position side)
        if "short" in side_raw.lower():
            order_side = OrderSide.BUY
        else:
            order_side = OrderSide.SELL

        # Check overnight eligibility
        overnight_ok = _check_overnight_tradable(trade_client, symbol)
        if not overnight_ok:
            print(f"  [SKIP] {symbol} -- not eligible for overnight trading")
            results.append({
                "symbol": symbol,
                "order_id": "N/A",
                "side": order_side.value,
                "qty": qty,
                "limit_price": "N/A",
                "status": "SKIPPED (not overnight_tradable)",
            })
            continue

        # Get latest quote
        bid, ask = _get_latest_quote(data_client, symbol)
        if bid is None or ask is None:
            print(f"  [SKIP] {symbol} -- could not get bid/ask quote")
            results.append({
                "symbol": symbol,
                "order_id": "N/A",
                "side": order_side.value,
                "qty": qty,
                "limit_price": "N/A",
                "status": "SKIPPED (no quote data)",
            })
            continue

        limit_price = _calculate_limit_price(order_side, bid, ask, slippage)

        if dry_run:
            print(
                f"  [DRY-RUN] {symbol}: {order_side.value.upper()} {qty} "
                f"@ limit ${limit_price}  (bid=${bid}, ask=${ask})"
            )
            results.append({
                "symbol": symbol,
                "order_id": "DRY-RUN",
                "side": order_side.value,
                "qty": qty,
                "limit_price": str(limit_price),
                "status": "DRY-RUN",
            })
            continue

        # Submit the order
        try:
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=float(qty),
                side=order_side,
                time_in_force=TimeInForce.DAY,
                limit_price=float(limit_price),
                extended_hours=True,
            )
            order = trade_client.submit_order(order_request)
            order_id = str(getattr(order, "id", "unknown"))
            order_status = str(getattr(order, "status", "unknown"))
            print(
                f"  [OK] {symbol}: {order_side.value.upper()} {qty} "
                f"@ limit ${limit_price}  (order_id={order_id}, status={order_status})"
            )
            results.append({
                "symbol": symbol,
                "order_id": order_id,
                "side": order_side.value,
                "qty": qty,
                "limit_price": str(limit_price),
                "status": order_status,
            })
        except Exception as exc:
            print(f"  [FAIL] {symbol}: {exc}")
            results.append({
                "symbol": symbol,
                "order_id": "N/A",
                "side": order_side.value,
                "qty": qty,
                "limit_price": str(limit_price),
                "status": f"FAILED ({exc})",
            })

    return results


def _poll_order_status(
    trade_client: TradingClient,
    results: list[dict[str, str]],
    timeout: int,
) -> None:
    """Poll order statuses until all are filled, cancelled, or timeout."""
    order_ids = [
        r["order_id"]
        for r in results
        if r["order_id"] not in ("N/A", "DRY-RUN", "unknown")
    ]
    if not order_ids:
        return

    print(f"\n--- Monitoring {len(order_ids)} orders (timeout: {timeout}s) ---\n")
    start = time.monotonic()

    while time.monotonic() - start < timeout:
        try:
            open_orders_req = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
            )
            open_orders = trade_client.get_orders(open_orders_req)
            our_open = [o for o in open_orders if str(getattr(o, "id", "")) in order_ids]

            if not our_open:
                print("  All liquidation orders have been resolved.")
                break

            elapsed = int(time.monotonic() - start)
            symbols_pending = [str(getattr(o, "symbol", "?")) for o in our_open]
            print(
                f"  [{elapsed}s] Still open: {len(our_open)} orders -- "
                f"{', '.join(symbols_pending)}"
            )
        except Exception as exc:
            print(f"  [WARN] Poll error: {exc}")

        time.sleep(POLL_INTERVAL_SECONDS)
    else:
        print(f"\n  Timeout reached ({timeout}s). Some orders may still be open.")
        print("  Check the Alpaca dashboard for remaining order statuses.")

    # Final status
    print("\n--- Final Order Summary ---\n")
    for result in results:
        symbol = result["symbol"]
        oid = result["order_id"]
        if oid in ("N/A", "DRY-RUN", "unknown"):
            print(f"  {symbol:<10}  {result['status']}")
            continue
        try:
            order = trade_client.get_order_by_id(oid)
            status = str(getattr(order, "status", "unknown"))
            filled_qty = getattr(order, "filled_qty", "0")
            filled_avg = getattr(order, "filled_avg_price", "N/A")
            print(f"  {symbol:<10}  status={status}  filled={filled_qty}  avg_price=${filled_avg}")
        except Exception:
            print(f"  {symbol:<10}  order_id={oid}  (could not fetch status)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for overnight liquidation."""
    args = _parse_args()

    print("\n=== Alchemiser Overnight Liquidation ===\n")

    if args.dry_run:
        print("  *** DRY-RUN MODE -- no orders will be placed ***\n")

    # Connect
    print("Connecting to Alpaca...")
    trade_client, data_client = _build_clients()

    # Verify account
    try:
        account = trade_client.get_account()
        print(f"  Account : {getattr(account, 'account_number', 'N/A')}")
        print(f"  Equity  : ${getattr(account, 'equity', 'N/A')}")
        print(f"  Cash    : ${getattr(account, 'cash', 'N/A')}")
        status = getattr(account, "status", "unknown")
        status_name = status.value if hasattr(status, "value") else str(status)
        if status_name.upper() not in ("ACTIVE",):
            print(f"\n  [ERROR] Account status is '{status_name}', expected ACTIVE. Aborting.")
            sys.exit(1)
    except Exception as exc:
        print(f"\n  [ERROR] Failed to connect to Alpaca: {exc}")
        sys.exit(1)

    # Fetch positions
    print("\nFetching open positions...")
    positions = _get_positions(trade_client)
    _print_positions_table(positions)

    if not positions:
        print("\nDone -- nothing to liquidate.")
        return

    # Confirmation gate
    print(f"\n  Positions to liquidate : {len(positions)}")
    print(f"  Slippage tolerance     : {args.slippage * 100}%")
    print(f"  Mode                   : {'DRY-RUN' if args.dry_run else 'LIVE'}")

    if not args.dry_run and not args.yes:
        confirm = input("\n  Type 'LIQUIDATE' to proceed: ").strip()
        if confirm != "LIQUIDATE":
            print("  Aborted.")
            sys.exit(0)

    # Cancel existing open orders (live mode only)
    if not args.dry_run:
        print("\nCancelling existing open orders...")
        try:
            trade_client.cancel_orders()
            print("  All open orders cancelled.")
        except Exception as exc:
            print(f"  [WARN] Failed to cancel orders: {exc}")

    # Submit liquidation orders
    print("\nSubmitting overnight LIMIT orders...\n")
    results = _submit_liquidation_orders(
        trade_client, data_client, positions, args.slippage, args.dry_run,
    )

    # Monitor fills
    if not args.dry_run:
        _poll_order_status(trade_client, results, args.timeout)
    else:
        print("\n--- Dry-Run Summary ---\n")
        submitted = [r for r in results if r["status"] == "DRY-RUN"]
        skipped = [r for r in results if r["status"].startswith("SKIPPED")]
        print(f"  Would submit : {len(submitted)} orders")
        print(f"  Skipped      : {len(skipped)} positions")

    print("\nDone.")


if __name__ == "__main__":
    main()
