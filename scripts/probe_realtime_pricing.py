#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Realtime pricing probe for Alpaca WebSocket (diagnostic utility).

This script starts the `RealTimePricingService`, subscribes to a symbol
(default: BTAL), and prints any quote and trade-derived price updates
observed within a short window. It helps verify connectivity, subscription,
and data flow when trading runs report missing quote data.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from typing import Literal

from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.types.market_data import PriceDataModel, QuoteModel


def _fmt_quote(quote: QuoteModel) -> dict[str, object]:
    return {
        "symbol": getattr(quote, "symbol", None),
        "bid_price": getattr(quote, "bid_price", None),
        "ask_price": getattr(quote, "ask_price", None),
        "bid_size": getattr(quote, "bid_size", None),
        "ask_size": getattr(quote, "ask_size", None),
        "timestamp": getattr(quote, "timestamp", None),
    }


def _fmt_price(price: PriceDataModel) -> dict[str, object]:
    return {
        "symbol": getattr(price, "symbol", None),
        "price": getattr(price, "price", None),
        "bid": getattr(price, "bid", None),
        "ask": getattr(price, "ask", None),
        "volume": getattr(price, "volume", None),
        "timestamp": getattr(price, "timestamp", None),
    }


def probe(symbol: str, seconds: float, environment: Literal["paper", "live"]) -> int:
    """Run a short realtime pricing probe.

    Args:
        symbol: Symbol to subscribe to (e.g., "BTAL").
        seconds: How long to observe the stream.
        environment: "paper" or "live" environment selection.

    Returns:
        Process exit code: 0 on success, non-zero on failure.

    """
    # Configure logging: service at DEBUG, others at INFO
    root_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, root_level, logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logging.getLogger("the_alchemiser.shared.services.real_time_pricing").setLevel(logging.DEBUG)

    logger = logging.getLogger("probe")

    # Show env presence (keys masked)
    has_key = bool(os.getenv("ALPACA_KEY"))
    has_secret = bool(os.getenv("ALPACA_SECRET"))
    logger.info(
        "Env credentials present: ALPACA_KEY=%s, ALPACA_SECRET=%s",
        "yes" if has_key else "no",
        "yes" if has_secret else "no",
    )

    paper = environment == "paper"
    service = RealTimePricingService(api_key=None, secret_key=None, paper_trading=paper)

    logger.info("Starting realtime pricing service (paper=%s)", paper)
    if not service.start():
        logger.error("Failed to start realtime pricing service")
        return 2

    logger.info("Subscribing symbol %s for order placement (high priority)", symbol)
    service.subscribe_for_order_placement(symbol)

    start = time.time()
    last_print = 0.0

    try:
        while (time.time() - start) < seconds:
            now = time.time()
            if now - last_print >= 0.5:
                last_print = now

                connected = service.is_connected()
                q = service.get_quote_data(symbol)
                p = service.get_price_data(symbol)
                price = service.get_real_time_price(symbol)
                spread: tuple[float, float] | None = service.get_bid_ask_spread(symbol)

                logger.info(
                    "connected=%s symbol=%s price=%s spread=%s",
                    connected,
                    symbol,
                    f"{price:.4f}" if price is not None else None,
                    spread,
                )
                if q is not None:
                    logger.info("quote=%s", _fmt_quote(q))
                else:
                    logger.info("quote=None")
                if p is not None:
                    logger.info("price_data=%s", _fmt_price(p))
                else:
                    logger.info("price_data=None")

            time.sleep(0.05)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Final summary
        stats = service.get_stats()
        subs = service.get_subscribed_symbols()
        logger.info("Final stats: %s", stats)
        logger.info("Subscribed symbols: %s", sorted(subs))

        # Peek at raw latest quote payload if available (diagnostic)
        try:
            raw = getattr(service, "_latest_quotes", {}).get(symbol)
            if raw is not None:
                logger.info("raw_quote_payload(type=%s)=%s", type(raw).__name__, raw)
            else:
                logger.info("raw_quote_payload=None")
        except Exception as exc:  # pragma: no cover (best-effort diagnostic)
            logger.warning("Could not access raw payload: %s", exc)

        logger.info("Stopping realtime pricing service")
        service.stop()

    return 0


def main(argv: list[str]) -> int:
    """CLI entrypoint for the realtime pricing probe.

    Parses arguments and launches the probe routine.
    """
    parser = argparse.ArgumentParser(description="Probe realtime pricing stream for a symbol")
    parser.add_argument("--symbol", default="BTAL", help="Symbol to subscribe to")
    parser.add_argument(
        "--seconds",
        type=float,
        default=10.0,
        help="How long to observe the stream",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live environment (default: paper)",
    )

    args = parser.parse_args(argv)
    environment: Literal["paper", "live"] = "live" if args.live else "paper"
    return probe(args.symbol.upper(), args.seconds, environment)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
