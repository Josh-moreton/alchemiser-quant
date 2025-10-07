"""Business Unit: shared | Status: current.

Price storage and retrieval for real-time market data.

This module handles thread-safe storage, retrieval, and cleanup
of real-time price and quote data.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import (
    PriceDataModel,
    QuoteModel,
    RealTimeQuote,
)


class RealTimePriceStore:
    """Thread-safe storage for real-time price and quote data."""

    def __init__(
        self,
        cleanup_interval: int = 60,
        max_quote_age: int = 300,
    ) -> None:
        """Initialize the price store.

        Args:
            cleanup_interval: Seconds between cleanup cycles
            max_quote_age: Maximum age of quotes in seconds before cleanup

        """
        self._cleanup_interval = cleanup_interval
        self._max_quote_age = max_quote_age

        # Data storage
        self._quotes: dict[str, RealTimeQuote] = {}
        self._price_data: dict[str, PriceDataModel] = {}
        self._quote_data: dict[str, QuoteModel] = {}
        self._last_update: dict[str, datetime] = {}

        # Thread safety
        self._quotes_lock = threading.Lock()

        # Cleanup control
        self._should_cleanup = False
        self._cleanup_thread: threading.Thread | None = None

        self.logger = get_logger(__name__)

    def start_cleanup(self, is_connected_callback: Callable[[], bool]) -> None:
        """Start the cleanup thread.

        Args:
            is_connected_callback: Callback to check if connected

        """
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._should_cleanup = True
        self._is_connected = is_connected_callback
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_old_quotes,
            name="QuoteCleanup",
            daemon=True,
        )
        self._cleanup_thread.start()

    def stop_cleanup(self) -> None:
        """Stop the cleanup thread."""
        self._should_cleanup = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2.0)

    def update_quote_data(
        self,
        symbol: str,
        bid_price: float,
        ask_price: float,
        bid_size: float | None,
        ask_size: float | None,
        timestamp: datetime,
    ) -> None:
        """Update quote data with locking.

        Args:
            symbol: Stock symbol
            bid_price: Bid price
            ask_price: Ask price
            bid_size: Bid size (optional)
            ask_size: Ask size (optional)
            timestamp: Quote timestamp

        """
        with self._quotes_lock:
            current_quote = self._quotes.get(symbol)
            last_price = current_quote.last_price if current_quote else 0.0

            # Update legacy RealTimeQuote
            self._quotes[symbol] = RealTimeQuote(
                bid=float(bid_price),
                ask=float(ask_price),
                last_price=last_price,
                timestamp=timestamp,
            )

            # Create new structured QuoteModel
            self._quote_data[symbol] = QuoteModel(
                symbol=symbol,
                bid_price=Decimal(str(bid_price)),
                ask_price=Decimal(str(ask_price)),
                bid_size=(Decimal(str(bid_size)) if bid_size is not None else Decimal("0.0")),
                ask_size=(Decimal(str(ask_size)) if ask_size is not None else Decimal("0.0")),
                timestamp=timestamp,
            )

    def update_trade_data(
        self, symbol: str, price: float, timestamp: datetime, volume: int | float | None
    ) -> None:
        """Update trade data with locking.

        Args:
            symbol: Stock symbol
            price: Trade price
            timestamp: Trade timestamp
            volume: Trade volume (optional)

        """
        with self._quotes_lock:
            current_quote = self._quotes.get(symbol)
            current_quote_data = self._quote_data.get(symbol)

            # Legacy RealTimeQuote storage (for backward compatibility)
            if current_quote:
                # Update existing quote with new trade price
                self._quotes[symbol] = RealTimeQuote(
                    bid=current_quote.bid,
                    ask=current_quote.ask,
                    last_price=float(price or 0),
                    timestamp=timestamp,
                )
            else:
                # Create new quote with trade price only
                self._quotes[symbol] = RealTimeQuote(
                    bid=0.0,
                    ask=0.0,
                    last_price=float(price or 0),
                    timestamp=timestamp,
                )

            # New structured PriceDataModel storage
            bid_price = current_quote_data.bid_price if current_quote_data else None
            ask_price = current_quote_data.ask_price if current_quote_data else None

            self._price_data[symbol] = PriceDataModel(
                symbol=symbol,
                price=Decimal(str(price or 0)),
                timestamp=timestamp,
                bid=bid_price,
                ask=ask_price,
                volume=int(volume or 0) if volume else None,
            )

            self._last_update[symbol] = datetime.now(UTC)

    def get_real_time_quote(self, symbol: str) -> RealTimeQuote | None:
        """Get real-time quote for a symbol (legacy).

        Args:
            symbol: Stock symbol

        Returns:
            RealTimeQuote object or None if not available

        Warning:
            This method is deprecated. Use get_quote_data() for new code.

        """
        import warnings

        warnings.warn(
            "get_real_time_quote() is deprecated. Use get_quote_data() for new code.",
            DeprecationWarning,
            stacklevel=2,
        )
        with self._quotes_lock:
            return self._quotes.get(symbol)

    def get_quote_data(self, symbol: str) -> QuoteModel | None:
        """Get structured quote data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            QuoteModel object with bid/ask prices and sizes, or None if not available

        """
        with self._quotes_lock:
            return self._quote_data.get(symbol)

    def get_price_data(self, symbol: str) -> PriceDataModel | None:
        """Get structured price data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            PriceDataModel object with price, bid/ask, and volume, or None if not available

        """
        with self._quotes_lock:
            return self._price_data.get(symbol)

    def get_real_time_price(self, symbol: str) -> Decimal | float | None:
        """Get the best available real-time price for a symbol.

        Priority: mid-price > last trade > bid > ask

        Args:
            symbol: Stock symbol

        Returns:
            Current price (Decimal from structured data or float from legacy) or None if not available

        """
        # Try structured data first (preferred)
        price_data = self.get_price_data(symbol)
        quote_data = self.get_quote_data(symbol)

        if quote_data and quote_data.bid_price > 0 and quote_data.ask_price > 0:
            return quote_data.mid_price

        if price_data and price_data.price > 0:
            return price_data.price

        if quote_data and quote_data.bid_price > 0:
            return quote_data.bid_price

        if quote_data and quote_data.ask_price > 0:
            return quote_data.ask_price

        # Fallback to legacy quote (for backward compatibility)
        quote = self.get_real_time_quote(symbol)
        if not quote:
            return None

        # Return mid-price if both bid/ask available
        if quote.bid > 0 and quote.ask > 0:
            return quote.mid_price
        # Fallback to last trade price
        if quote.last_price > 0:
            return quote.last_price
        # Final fallback to bid or ask
        if quote.bid > 0:
            return quote.bid
        if quote.ask > 0:
            return quote.ask

        return None

    def get_bid_ask_spread(self, symbol: str) -> tuple[Decimal | float, Decimal | float] | None:
        """Get current bid/ask spread for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) - Decimal from structured data or float from legacy, or None if not available

        """
        # Try structured data first (preferred)
        quote_data = self.get_quote_data(symbol)
        if quote_data and quote_data.bid_price > 0 and quote_data.ask_price > 0:
            # Additional validation: ensure ask > bid for a reasonable spread
            if quote_data.ask_price <= quote_data.bid_price:
                self.logger.warning(
                    f"Invalid spread for {symbol}: bid={quote_data.bid_price}, "
                    f"ask={quote_data.ask_price} (ask <= bid)"
                )
                return None
            return quote_data.bid_price, quote_data.ask_price

        # Fallback to legacy quote
        quote = self.get_real_time_quote(symbol)
        if not quote or quote.bid <= 0 or quote.ask <= 0:
            return None

        # Additional validation: ensure ask > bid for a reasonable spread
        if quote.ask <= quote.bid:
            self.logger.warning(
                f"Invalid spread for {symbol}: bid={quote.bid}, ask={quote.ask} (ask <= bid)"
            )
            return None

        return quote.bid, quote.ask

    def get_optimized_price_for_order(
        self,
        symbol: str,
        subscribe_callback: Callable[[str], None],
        max_wait: float = 0.5,
    ) -> Decimal | float | None:
        """Get the most accurate price for order placement.

        Args:
            symbol: Stock symbol
            subscribe_callback: Callback to subscribe symbol with high priority
            max_wait: Maximum wait time for fresh data

        Returns:
            Current price optimized for order accuracy (Decimal from structured data or float from legacy)

        """
        # Subscribe with highest priority for order placement
        subscribe_callback(symbol)

        # Wait for real-time data with timeout and early exit if data available
        check_interval = 0.05  # Check every 50ms
        elapsed = 0.0

        while elapsed < max_wait:
            # Check if we have recent data for this symbol
            if symbol in self._quotes and symbol in self._last_update:
                # If data is very recent (within 1 second), use it immediately
                time_since_update = (datetime.now(UTC) - self._last_update[symbol]).total_seconds()
                if time_since_update < 1.0:
                    break

            time.sleep(check_interval)
            elapsed += check_interval

        # Get the best available price
        return self.get_real_time_price(symbol)

    def get_stats(self) -> dict[str, int]:
        """Get storage statistics.

        Returns:
            Dictionary of statistics

        """
        with self._quotes_lock:
            return {
                "symbols_tracked": len(self._quotes),
                "symbols_tracked_legacy": len(self._quotes),
                "symbols_tracked_structured_prices": len(self._price_data),
                "symbols_tracked_structured_quotes": len(self._quote_data),
            }

    def has_recent_data(self, symbol: str, max_age_seconds: float = 1.0) -> bool:
        """Check if we have recent data for a symbol.

        Args:
            symbol: Stock symbol
            max_age_seconds: Maximum age in seconds

        Returns:
            True if data is recent

        """
        with self._quotes_lock:
            if symbol not in self._last_update:
                return False
            time_since_update = (datetime.now(UTC) - self._last_update[symbol]).total_seconds()
            return time_since_update < max_age_seconds

    def _cleanup_old_quotes(self) -> None:
        """Cleanup old quotes to prevent memory bloat."""
        while self._should_cleanup:
            try:
                time.sleep(self._cleanup_interval)

                if not self._is_connected():
                    continue

                cutoff_time = datetime.now(UTC) - timedelta(seconds=self._max_quote_age)

                with self._quotes_lock:
                    symbols_to_remove = [
                        symbol
                        for symbol, last_update in self._last_update.items()
                        if last_update < cutoff_time
                    ]

                    for symbol in symbols_to_remove:
                        self._quotes.pop(symbol, None)
                        self._price_data.pop(symbol, None)
                        self._quote_data.pop(symbol, None)
                        self._last_update.pop(symbol, None)

                    if symbols_to_remove:
                        self.logger.info(f"🧹 Cleaned up {len(symbols_to_remove)} old quotes")

            except Exception as e:
                self.logger.error(f"Error during quote cleanup: {e}")
