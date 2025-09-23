#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Real-time WebSocket Price Streaming for Alpaca Trading with Structured Data Types.

This module provides real-time stock price updates via Alpaca's WebSocket streams
to ensure accurate limit order pricing. It maintains current bid/ask quotes and
last trade prices for symbols used in trading strategies using structured data types.

DESIGN PHILOSOPHY:
=================
- Real-time pricing for accurate limit orders
- Minimal latency for high-frequency quote updates
- Thread-safe quote storage with automatic cleanup
- Graceful fallback to REST API when needed
- Subscribe only to symbols being actively traded
- Rich market data capture with volume and market depth

KEY FEATURES:
============
1. Real-time quote updates with market depth (bid/ask sizes)
2. Enhanced trade data with volume information
3. Structured data types (QuoteModel, PriceDataModel)
4. Backward compatibility with legacy RealTimeQuote
5. Automatic symbol subscription management
6. Thread-safe price storage
7. Connection health monitoring
8. Smart reconnection logic
9. Memory-efficient quote caching

MIGRATION NOTES:
===============
- New code should use get_quote_data() and get_price_data()
- Legacy get_real_time_quote() still supported with deprecation warnings
- Enhanced data capture includes bid_size, ask_size, and volume
- Structured types provide better type safety and richer market data
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from the_alchemiser.shared.brokers.alpaca_utils import (
    create_stock_data_stream,
)
from the_alchemiser.shared.types.market_data import PriceDataModel, QuoteModel

if TYPE_CHECKING:
    from alpaca.data.live import StockDataStream
    from alpaca.data.models import Quote, Trade

    # Type aliases for static type checking - can be either dict or Alpaca objects
    AlpacaQuoteData = dict[str, str | float | int] | Quote
    AlpacaTradeData = dict[str, str | float | int] | Trade
else:
    # Runtime type aliases - no forward references, use object for flexibility
    AlpacaQuoteData = dict[str, str | float | int] | object
    AlpacaTradeData = dict[str, str | float | int] | object

# Phase 11 - Migration to structured pricing data in progress
# Both RealTimeQuote (legacy) and structured types (PriceDataModel, QuoteModel) are available
# New implementation uses structured types with backward compatibility for RealTimeQuote


@dataclass
class RealTimeQuote:
    """Real-time quote data structure."""

    bid: float
    ask: float
    last_price: float
    timestamp: datetime

    @property
    def mid_price(self) -> float:
        """Calculate mid-point between bid and ask."""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        if self.bid > 0:
            return self.bid
        if self.ask > 0:
            return self.ask
        return self.last_price


@dataclass
class _SubscriptionPlan:
    """Internal helper class for bulk subscription planning."""

    results: dict[str, bool]
    symbols_to_add: list[str]
    symbols_to_replace: list[str]
    available_slots: int
    successfully_added: int = 0


class RealTimePricingService:
    """Real-time pricing service using Alpaca's WebSocket data streams.

    Provides up-to-date bid/ask quotes and last trade prices for accurate
    limit order placement. Automatically manages subscriptions based on
    active trading symbols.
    """

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        paper_trading: bool = True,
        max_symbols: int = 30,
    ) -> None:
        """Initialize real-time pricing service with WebSocket streaming.

        Args:
            api_key: Alpaca API key (reads from env if not provided)
            secret_key: Alpaca secret key (reads from env if not provided)
            paper_trading: Whether to use paper trading endpoints
            max_symbols: Maximum number of symbols to subscribe to concurrently

        """
        # Load credentials from environment if not provided
        if not api_key or not secret_key:
            import os

            from dotenv import load_dotenv

            load_dotenv()
            api_key = api_key or os.getenv("ALPACA_KEY")
            secret_key = secret_key or os.getenv("ALPACA_SECRET")

        if not api_key or not secret_key:
            logging.error("❌ Alpaca credentials not provided or found in environment")
            raise ValueError("Alpaca API credentials required")

        self._api_key = api_key
        self._secret_key = secret_key
        self._paper_trading = paper_trading
        self._max_symbols = max_symbols

        # Initialize streaming state
        self._stream_thread: threading.Thread | None = None
        self._stream: StockDataStream | None = None
        self._should_reconnect = False
        self._connected = False

        # Initialize data storage
        self._quotes: dict[str, RealTimeQuote] = {}
        self._price_data: dict[str, PriceDataModel] = {}
        self._quote_data: dict[str, QuoteModel] = {}
        self._subscribed_symbols: set[str] = set()
        self._data_lock = threading.Lock()
        self._subscription_lock = threading.Lock()
        self._quotes_lock = threading.Lock()

        # Initialize cleanup settings
        self._cleanup_interval = 60  # seconds between cleanup cycles
        self._max_quote_age = 300  # maximum age of quotes in seconds

        # Initialize missing attributes for smart execution
        self._subscription_priority: dict[str, float] = {}
        self._latest_quotes: dict[str, AlpacaQuoteData] = {}
        self._stats: dict[str, int] = {
            "quotes_received": 0,
            "total_subscriptions": 0,
            "trades_received": 0,
            "subscription_limit_hits": 0,
        }
        self._datetime_stats: dict[str, datetime] = {}
        self._latest_bid: dict[str, float] = {}
        self._latest_ask: dict[str, float] = {}
        self._last_quote_time: dict[str, datetime] = {}
        self._last_update: dict[str, datetime] = {}

        # Initialize logger for this instance
        self.logger = logging.getLogger(__name__)

        logging.info(
            f"📡 Real-time pricing service initialized ({'paper' if paper_trading else 'live'})"
        )

    @property
    def api_key(self) -> str:
        """Get API key."""
        return self._api_key

    @property
    def secret_key(self) -> str:
        """Get secret key."""
        return self._secret_key

    @property
    def paper_trading(self) -> bool:
        """Get paper trading flag."""
        return self._paper_trading

    def start(self) -> bool:
        """Start the real-time pricing service.

        Returns:
            True if started successfully, False otherwise

        """
        try:
            if self._stream_thread and self._stream_thread.is_alive():
                logging.warning("Real-time pricing service already running")
                return True

            # Initialize the data stream
            # NOTE: Using IEX feed for both paper and live trading until SIP subscription is available
            # SIP feed requires a paid subscription, IEX is free but has some limitations
            self._stream = create_stock_data_stream(
                api_key=self.api_key,
                secret_key=self.secret_key,
                feed=self._get_feed(),
            )

            # Set up the async event handlers BEFORE starting the stream
            # This is critical - handlers must be registered before run() is called
            logging.info("📡 Real-time pricing service initialized with async handlers")

            # NOTE: Do NOT subscribe to wildcard "*" - it hits subscription limits immediately
            # We'll subscribe to specific symbols only when needed via subscribe_for_order_placement()

            # Start the stream in a background thread with proper async handling
            self._should_reconnect = True
            self._stream_thread = threading.Thread(
                target=self._run_stream_with_event_loop,
                name="RealTimePricing",
                daemon=True,
            )
            self._stream_thread.start()

            # Wait a moment for connection with exponential backoff
            max_wait_time = 5.0  # 5 second timeout
            check_interval = 0.05  # Start with 50ms
            max_interval = 0.5  # Cap at 500ms
            elapsed_time = 0.0

            while elapsed_time < max_wait_time:
                if self._connected:
                    break
                time.sleep(check_interval)
                elapsed_time += check_interval
                # Exponential backoff for less aggressive polling
                check_interval = min(check_interval * 1.2, max_interval)

            if self._connected:
                logging.info("✅ Real-time pricing service started successfully")

                # Start cleanup thread
                cleanup_thread = threading.Thread(
                    target=self._cleanup_old_quotes, name="QuoteCleanup", daemon=True
                )
                cleanup_thread.start()

                return True
            logging.error("❌ Failed to establish real-time pricing connection")
            return False

        except Exception as e:
            logging.error(f"Error starting real-time pricing service: {e}")
            return False

    def stop(self) -> None:
        """Stop the real-time pricing service."""
        try:
            self._should_reconnect = False

            if self._stream:
                self._stream.stop()

            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=5)

            self._connected = False
            logging.info("🛑 Real-time pricing service stopped")

        except Exception as e:
            logging.error(f"Error stopping real-time pricing service: {e}")

    def _run_stream_with_event_loop(self) -> None:
        """Run the WebSocket stream in a new event loop.

        This method creates a new event loop in the current thread and runs
        the async stream within it. This is necessary because the Alpaca SDK
        requires async handlers to run in the same event loop as the stream.
        """
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run the async stream method
            loop.run_until_complete(self._run_stream_async())
        except Exception as e:
            logging.error(f"Error in stream event loop: {e}")
        finally:
            # Clean up the event loop
            try:
                # Cancel any remaining tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()

                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                loop.close()
            except Exception as e:
                logging.error(f"Error cleaning up event loop: {e}")

    async def _run_stream_async(self) -> None:
        """Async method to run the WebSocket stream.

        This method handles the actual stream execution and reconnection logic
        within an async context where the handlers can operate properly.
        """
        retry_count = 0
        max_retries = 5
        base_delay = 1.0

        while self._should_reconnect and retry_count < max_retries:
            try:
                logging.info(
                    f"🔄 Attempting to start real-time data stream (attempt {retry_count + 1})"
                )

                # Get current subscription list in a thread-safe way
                with self._subscription_lock:
                    symbols_to_subscribe = list(self._subscribed_symbols)

                if symbols_to_subscribe:
                    logging.info(
                        f"📡 Setting up subscriptions for {len(symbols_to_subscribe)} symbols: {sorted(symbols_to_subscribe)}"
                    )

                    # Create a fresh stream instance for each attempt
                    # This is necessary because streams are not reusable after they fail or close
                    self._stream = create_stock_data_stream(
                        api_key=self.api_key,
                        secret_key=self.secret_key,
                        feed=self._get_feed(),
                    )

                    # Subscribe to quotes and trades for all symbols at once
                    # This must be done BEFORE calling stream.run()
                    self._stream.subscribe_quotes(self._on_quote, *symbols_to_subscribe)
                    self._stream.subscribe_trades(self._on_trade, *symbols_to_subscribe)

                    logging.info("✅ All subscriptions set up successfully")

                    # Mark as connected before starting the stream
                    self._connected = True

                    # Run the stream's internal async method directly
                    # NOTE: We use _run_forever() instead of run() because run()
                    # calls asyncio.run() internally, which would conflict with our event loop
                    await self._stream._run_forever()

                    # If we get here, the stream closed normally
                    logging.info("📡 Real-time data stream closed normally")
                    break  # No symbols to subscribe to - wait for symbols to be added
                logging.info("📡 No symbols to subscribe to, waiting for subscription requests...")
                self._connected = True  # Mark as ready to receive subscriptions

                # Wait for subscriptions to be added
                while self._should_reconnect and not symbols_to_subscribe:
                    await asyncio.sleep(1.0)  # Check every second
                    with self._subscription_lock:
                        symbols_to_subscribe = list(self._subscribed_symbols)

                # If symbols were added, restart the loop to set up subscriptions
                if symbols_to_subscribe:
                    logging.info(f"📡 New subscriptions detected: {sorted(symbols_to_subscribe)}")
                    # Reset connection state to force re-setup
                    self._connected = False
                    continue

                # Should not reconnect anymore
                logging.info("📡 Shutting down stream - no reconnection requested")
                break

            except Exception as e:
                retry_count += 1
                delay = min(base_delay * (2 ** (retry_count - 1)), 30.0)  # Cap at 30 seconds

                logging.error(f"❌ Real-time data stream error (attempt {retry_count}): {e}")

                if retry_count < max_retries and self._should_reconnect:
                    logging.info(f"⏱️ Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error("🚨 Max retries exceeded, stopping real-time pricing service")
                    break
            finally:
                self._connected = False

        logging.info("📡 Real-time pricing stream thread exiting")

    async def _on_quote(self, data: AlpacaQuoteData) -> None:
        """Handle incoming quote data.

        Args:
            data: Quote data from Alpaca WebSocket

        """
        try:
            # Extract symbol from data and ensure it's a string
            if hasattr(data, "symbol"):
                symbol = str(data.symbol)
            else:
                symbol = str(data.get("S", "")) if isinstance(data, dict) else ""

            if not symbol:
                self.logger.warning("Received quote with no symbol")
                return

            # Extract bid/ask data with explicit branching to avoid precedence bugs
            if isinstance(data, dict):
                bid_price = data.get("bp")
                ask_price = data.get("ap")
                bid_size = data.get("bs")
                ask_size = data.get("as")
                timestamp_raw = data.get("t")
            else:
                bid_price = getattr(data, "bid_price", None)
                ask_price = getattr(data, "ask_price", None)
                bid_size = getattr(data, "bid_size", None)
                ask_size = getattr(data, "ask_size", None)
                timestamp_raw = getattr(data, "timestamp", None)

            # Ensure timestamp is a datetime
            timestamp = timestamp_raw if isinstance(timestamp_raw, datetime) else datetime.now(UTC)

            # Log for debugging
            self.logger.debug(f"📊 Quote received for {symbol}: bid={bid_price}, ask={ask_price}")

            # Store complete quote data
            self._latest_quotes[symbol] = data

            # Update bid/ask tracking
            if bid_price is not None and ask_price is not None:
                self._latest_bid[symbol] = float(bid_price)
                self._latest_ask[symbol] = float(ask_price)

                # Create structured QuoteModel object
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
                        bid_price=float(bid_price),
                        ask_price=float(ask_price),
                        bid_size=float(bid_size) if bid_size is not None else 0.0,
                        ask_size=float(ask_size) if ask_size is not None else 0.0,
                        timestamp=timestamp,
                    )

            # Update statistics
            self._stats["quotes_received"] += 1
            self._last_quote_time[symbol] = datetime.now(UTC)

        except Exception as e:
            self.logger.error(f"Error processing quote: {e}", exc_info=True)

    async def _on_trade(self, trade: AlpacaTradeData) -> None:
        """Handle incoming trade updates from Alpaca stream."""
        try:
            # Handle both Trade objects and dictionary format
            if isinstance(trade, dict):
                symbol_raw = trade.get("symbol")
                price = trade.get("price", 0)
                size = trade.get("size", 0)
                volume = trade.get("volume", size)  # New field for structured types
                timestamp_raw = trade.get("timestamp", datetime.now(UTC))
            else:
                symbol_raw = trade.symbol
                price = trade.price
                size = trade.size
                volume = getattr(trade, "volume", size)  # New field for structured types
                timestamp_raw = trade.timestamp

            # Ensure symbol is a string
            if not symbol_raw:
                return
            symbol = str(symbol_raw)

            # Ensure timestamp is a datetime
            timestamp = timestamp_raw if isinstance(timestamp_raw, datetime) else datetime.now(UTC)

            # Update last trade price with both legacy and structured storage
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
                    price=float(price or 0),
                    timestamp=timestamp,
                    bid=bid_price,
                    ask=ask_price,
                    volume=int(volume or 0) if volume else None,
                )

                self._last_update[symbol] = datetime.now(UTC)
                self._stats["trades_received"] += 1

            # Update heartbeat
            self._datetime_stats["last_heartbeat"] = datetime.now(UTC)

            logging.debug(f"💰 Trade: {symbol} ${float(price or 0):.2f} x {size}")

        except Exception as e:
            symbol_str = str(
                trade.get("symbol", "unknown")
                if isinstance(trade, dict)
                else getattr(trade, "symbol", "unknown")
            )
            logging.error(f"Error processing trade for {symbol_str}: {e}")

    def _cleanup_old_quotes(self) -> None:
        """Cleanup old quotes to prevent memory bloat."""
        while self._should_reconnect:
            try:
                time.sleep(self._cleanup_interval)

                if not self._connected:
                    continue

                cutoff_time = datetime.now(UTC) - timedelta(seconds=self._max_quote_age)

                with self._quotes_lock:
                    symbols_to_remove = [
                        symbol
                        for symbol, last_update in self._last_update.items()
                        if last_update < cutoff_time
                    ]

                    for symbol in symbols_to_remove:
                        self._quotes.pop(symbol, None)  # Legacy storage
                        self._price_data.pop(symbol, None)  # New price storage
                        self._quote_data.pop(symbol, None)  # New quote storage
                        self._last_update.pop(symbol, None)

                    if symbols_to_remove:
                        logging.info(f"🧹 Cleaned up {len(symbols_to_remove)} old quotes")

            except Exception as e:
                logging.error(f"Error during quote cleanup: {e}")

    def get_real_time_quote(self, symbol: str) -> RealTimeQuote | None:
        """Get real-time quote for a symbol.

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

    def get_real_time_price(self, symbol: str) -> float | None:
        """Get the best available real-time price for a symbol.

        Priority: mid-price > last trade > bid > ask

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if not available

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

    def get_bid_ask_spread(self, symbol: str) -> tuple[float, float] | None:
        """Get current bid/ask spread for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) or None if not available

        """
        # Try structured data first (preferred)
        quote_data = self.get_quote_data(symbol)
        if quote_data and quote_data.bid_price > 0 and quote_data.ask_price > 0:
            # Additional validation: ensure ask > bid for a reasonable spread
            if quote_data.ask_price <= quote_data.bid_price:
                logging.warning(
                    f"Invalid spread for {symbol}: bid={quote_data.bid_price}, ask={quote_data.ask_price} (ask <= bid)"
                )
                return None
            return quote_data.bid_price, quote_data.ask_price

        # Fallback to legacy quote
        quote = self.get_real_time_quote(symbol)
        if not quote or quote.bid <= 0 or quote.ask <= 0:
            return None

        # Additional validation: ensure ask > bid for a reasonable spread
        if quote.ask <= quote.bid:
            logging.warning(
                f"Invalid spread for {symbol}: bid={quote.bid}, ask={quote.ask} (ask <= bid)"
            )
            return None

        return quote.bid, quote.ask

    def is_connected(self) -> bool:
        """Check if the real-time service is connected."""
        return self._connected

    def get_stats(self) -> dict[str, str | int | float | datetime | bool]:
        """Get service statistics."""
        last_hb = self._datetime_stats.get("last_heartbeat")  # May be absent until first trade
        uptime = (
            (datetime.now(UTC) - last_hb).total_seconds() if isinstance(last_hb, datetime) else 0
        )
        return {
            **self._stats,
            **self._datetime_stats,
            "connected": self._connected,
            "symbols_tracked": len(self._quotes),
            "symbols_tracked_legacy": len(self._quotes),
            "symbols_tracked_structured_prices": len(self._price_data),
            "symbols_tracked_structured_quotes": len(self._quote_data),
            "uptime_seconds": uptime,
        }

    def _get_feed(self) -> str:
        """Resolve the Alpaca data feed to use.

        Allows overriding via env vars `ALPACA_FEED` or `ALPACA_DATA_FEED`.
        Defaults to "iex". Use "sip" if you have the required subscription.
        """
        import os

        feed = (os.getenv("ALPACA_FEED") or os.getenv("ALPACA_DATA_FEED") or "iex").lower()
        if feed not in {"iex", "sip"}:
            self.logger.warning(f"Unknown ALPACA_FEED '{feed}', defaulting to 'iex'")
            return "iex"
        return feed

    def subscribe_symbols_bulk(
        self, symbols: list[str], priority: float | None = None
    ) -> dict[str, bool]:
        """Subscribe to real-time data for multiple symbols efficiently.

        Args:
            symbols: List of symbols to subscribe to
            priority: Subscription priority for all symbols (higher = more important)

        Returns:
            Dictionary mapping symbol to subscription success status

        """
        if priority is None:
            priority = time.time()  # Use current timestamp as default priority

        normalized_symbols = self._normalize_symbols(symbols)
        if not normalized_symbols:
            return {}

        logging.info(
            f"📡 Bulk subscribing to {len(normalized_symbols)} symbols with priority {priority:.1f}"
        )

        with self._subscription_lock:
            subscription_plan = self._plan_bulk_subscription(normalized_symbols, priority)
            self._execute_subscription_plan(subscription_plan, priority)

        self._restart_stream_if_needed(subscription_plan.successfully_added)
        
        logging.info(
            f"✅ Bulk subscription complete: {subscription_plan.successfully_added}/"
            f"{len(subscription_plan.symbols_to_add)} new symbols subscribed"
        )
        return subscription_plan.results

    def _normalize_symbols(self, symbols: list[str]) -> list[str]:
        """Normalize symbol list by cleaning and filtering."""
        return [symbol.upper().strip() for symbol in symbols if symbol.strip()]

    def _plan_bulk_subscription(self, symbols: list[str], priority: float) -> _SubscriptionPlan:
        """Plan bulk subscription operations."""
        results: dict[str, bool] = {}
        symbols_to_add = []
        
        # Handle existing symbols
        for symbol in symbols:
            if symbol in self._subscribed_symbols:
                self._subscription_priority[symbol] = max(
                    self._subscription_priority.get(symbol, 0), priority
                )
                results[symbol] = True
                logging.debug(
                    f"Already subscribed to {symbol}, updated priority to "
                    f"{self._subscription_priority[symbol]:.1f}"
                )
            else:
                symbols_to_add.append(symbol)

        # Calculate capacity and replacements
        available_slots = self._max_symbols - len(self._subscribed_symbols)
        symbols_to_replace = self._find_symbols_to_replace(symbols_to_add, available_slots, priority)
        
        return _SubscriptionPlan(
            results=results,
            symbols_to_add=symbols_to_add,
            symbols_to_replace=symbols_to_replace,
            available_slots=available_slots + len(symbols_to_replace),
            successfully_added=0
        )

    def _find_symbols_to_replace(
        self, symbols_to_add: list[str], available_slots: int, priority: float
    ) -> list[str]:
        """Find existing symbols that can be replaced with higher priority ones."""
        if len(symbols_to_add) <= available_slots:
            return []

        existing_symbols = sorted(
            self._subscription_priority.keys(),
            key=lambda x: self._subscription_priority.get(x, 0),
        )

        symbols_to_replace = []
        symbols_needed = len(symbols_to_add) - available_slots
        
        for symbol in existing_symbols:
            if len(symbols_to_replace) >= symbols_needed:
                break
            if self._subscription_priority.get(symbol, 0) < priority:
                symbols_to_replace.append(symbol)

        return symbols_to_replace

    def _execute_subscription_plan(self, plan: _SubscriptionPlan, priority: float) -> None:
        """Execute the planned subscription operations."""
        # Remove symbols to be replaced
        for symbol_to_remove in plan.symbols_to_replace:
            self._subscribed_symbols.discard(symbol_to_remove)
            self._subscription_priority.pop(symbol_to_remove, None)
            self._stats["subscription_limit_hits"] += 1
            logging.info(f"📊 Replaced {symbol_to_remove} for higher priority symbols")

        # Add new symbols
        for symbol in plan.symbols_to_add[:plan.available_slots]:
            self._subscribed_symbols.add(symbol)
            self._subscription_priority[symbol] = priority
            plan.results[symbol] = True
            plan.successfully_added += 1
            self._stats["total_subscriptions"] += 1

        # Mark symbols we couldn't subscribe to due to limits
        for symbol in plan.symbols_to_add[plan.available_slots:]:
            plan.results[symbol] = False
            logging.warning(f"⚠️ Cannot subscribe to {symbol} - subscription limit reached")

    def _restart_stream_if_needed(self, successfully_added: int) -> None:
        """Restart stream if new symbols were added and we're connected."""
        if successfully_added > 0 and self._connected:
            logging.info(f"🔄 Restarting stream to add {successfully_added} new subscriptions")
            self._restart_stream_for_new_subscription()

    def subscribe_symbol(self, symbol: str, priority: float | None = None) -> None:
        """Subscribe to real-time updates for a specific symbol with smart limit management.

        Args:
            symbol: Stock symbol to subscribe to
            priority: Priority score (higher = more important). Defaults to timestamp.

        """
        if priority is None:
            priority = time.time()  # Use current timestamp as default priority

        needs_restart = False
        with self._subscription_lock:
            # Check if we need to manage subscription limits
            if (
                symbol not in self._subscribed_symbols
                and len(self._subscribed_symbols) >= self._max_symbols
            ):
                # Find lowest priority symbol to unsubscribe
                lowest_priority_symbol = min(
                    self._subscribed_symbols,
                    key=lambda s: self._subscription_priority.get(s, 0),
                )
                lowest_priority = self._subscription_priority.get(lowest_priority_symbol, 0)

                if priority > lowest_priority:
                    # Unsubscribe lowest priority symbol
                    logging.info(
                        f"📊 Subscription limit reached. Replacing {lowest_priority_symbol} (priority: {lowest_priority:.1f}) with {symbol} (priority: {priority:.1f})"
                    )
                    self._subscribed_symbols.remove(lowest_priority_symbol)
                    self._subscription_priority.pop(lowest_priority_symbol, None)
                    self._stats["subscription_limit_hits"] += 1
                    needs_restart = True
                else:
                    logging.warning(
                        f"⚠️ Cannot subscribe to {symbol} - priority {priority:.1f} too low (limit: {self._max_symbols} symbols)"
                    )
                    return

            if symbol not in self._subscribed_symbols:
                self._subscribed_symbols.add(symbol)
                self._subscription_priority[symbol] = priority
                needs_restart = self._connected  # Only restart if already connected

                logging.info(f"📡 Added {symbol} to subscription list (priority: {priority:.1f})")
                logging.debug(f"📊 Current subscriptions: {sorted(self._subscribed_symbols)}")
                self._stats["total_subscriptions"] += 1
            else:
                # Update priority for existing subscription
                self._subscription_priority[symbol] = max(
                    self._subscription_priority.get(symbol, 0), priority
                )

        # Restart stream if needed (outside the lock to avoid deadlock)
        if needs_restart and self._connected:
            logging.info(f"🔄 Restarting stream to add subscription for {symbol}")
            self._restart_stream_for_new_subscription()

    def _restart_stream_for_new_subscription(self) -> None:
        """Restart the stream to pick up new subscriptions.

        This is necessary because Alpaca SDK doesn't allow adding subscriptions
        to a running stream - they must be set up before stream.run().
        """
        try:
            # Signal the current stream to stop
            self._should_reconnect = False
            if self._stream:
                try:
                    self._stream.stop()
                except Exception as e:
                    logging.debug(f"Error stopping stream for restart: {e}")

            # Wait for the stream thread to finish
            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=2.0)

            # Restart with new subscriptions
            self._should_reconnect = True
            self._connected = False
            self._stream_thread = threading.Thread(
                target=self._run_stream_with_event_loop,
                name="RealTimePricing",
                daemon=True,
            )
            self._stream_thread.start()

            # Wait for reconnection
            start_time = time.time()
            while time.time() - start_time < 5.0:
                if self._connected:
                    logging.info("✅ Stream restarted successfully with new subscriptions")
                    break
                time.sleep(0.1)

        except Exception as e:
            logging.error(f"Error restarting stream for new subscription: {e}")
            self._connected = False

    def unsubscribe_symbol(self, symbol: str) -> None:
        """Unsubscribe from real-time updates for a specific symbol.

        Args:
            symbol: Stock symbol to unsubscribe from

        """
        with self._subscription_lock:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
                self._subscription_priority.pop(symbol, None)

                # Remove quote data from both legacy and structured storage
                with self._quotes_lock:
                    self._quotes.pop(symbol, None)  # Legacy storage
                    self._price_data.pop(symbol, None)  # New price storage
                    self._quote_data.pop(symbol, None)  # New quote storage
                    self._last_update.pop(symbol, None)

                logging.info(f"📴 Unsubscribed from real-time data for {symbol}")

    def subscribe_for_trading(self, symbol: str) -> None:
        """Subscribe to real-time data for a symbol that will be traded.

        Args:
            symbol: Stock symbol to subscribe to

        """
        self.subscribe_symbol(symbol)

    def subscribe_for_order_placement(self, symbol: str) -> None:
        """Subscribe to a symbol specifically for order placement.

        This method ensures the symbol is subscribed with high priority
        for immediate order execution needs.

        Args:
            symbol: The symbol to subscribe to

        """
        # Subscribe with high priority (current timestamp ensures recent priority)
        self.subscribe_symbol(symbol, priority=time.time() + 1000)  # High priority

        # Log for debugging
        self.logger.info(f"📊 Subscribed {symbol} for order placement (high priority)")

    def unsubscribe_after_order(self, symbol: str) -> None:
        """Optionally unsubscribe from a symbol after order placement.

        Args:
            symbol: The symbol to unsubscribe from

        """
        # For now, keep subscriptions active for potential re-pegging
        # Could implement cleanup logic here if needed
        self.logger.debug(f"Keeping {symbol} subscription active for monitoring")

    def get_optimized_price_for_order(self, symbol: str) -> float | None:
        """Get the most accurate price for order placement with temporary subscription.

        Args:
            symbol: Stock symbol

        Returns:
            Current price optimized for order accuracy

        """
        # Subscribe with highest priority for order placement
        self.subscribe_for_order_placement(symbol)

        # Wait for real-time data with timeout and early exit if data available
        import time

        max_wait = 0.5  # Maximum wait time
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

    def get_subscribed_symbols(self) -> set[str]:
        """Get currently subscribed symbols.

        Returns:
            Set of subscribed symbol strings

        """
        with self._subscription_lock:
            return self._subscribed_symbols.copy()


class RealTimePricingManager:
    """Manager class for real-time pricing integration with existing data providers.

    Provides a clean interface for integrating real-time pricing into
    existing trading systems while maintaining backward compatibility.
    """

    def __init__(self, api_key: str, secret_key: str, *, paper_trading: bool = True) -> None:
        """Initialize real-time pricing manager.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading environment

        """
        self.pricing_service = RealTimePricingService(
            api_key, secret_key, paper_trading=paper_trading
        )
        self._fallback_provider: Callable[[str], float | None] | None = None

    def set_fallback_provider(self, provider: Callable[[str], float | None]) -> None:
        """Set fallback price provider for when real-time data is not available.

        Args:
            provider: Callable that takes symbol and returns price

        """
        self._fallback_provider = provider

    def start(self) -> bool:
        """Start the real-time pricing service."""
        return self.pricing_service.start()

    def stop(self) -> None:
        """Stop the real-time pricing service."""
        self.pricing_service.stop()

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price with real-time data priority.

        Args:
            symbol: Stock symbol

        Returns:
            Current price from real-time data or fallback provider

        Uses centralized price discovery utility for consistent fallback logic.

        """
        from the_alchemiser.shared.utils.price_discovery_utils import (
            get_current_price_with_fallback,
        )

        # Create a wrapper for the pricing service to match PriceProvider interface
        primary_provider = type(
            "PriceProvider",
            (),
            {"get_current_price": lambda _, sym: self.pricing_service.get_real_time_price(sym)},
        )()

        # Create fallback provider wrapper if available
        fallback_provider = None
        if self._fallback_provider is not None:
            fallback_provider = type(
                "FallbackProvider",
                (),
                {
                    "get_current_price": lambda _, sym: (
                        self._fallback_provider(sym)
                        if self._fallback_provider is not None
                        else None
                    )
                },
            )()

        return get_current_price_with_fallback(primary_provider, fallback_provider, symbol)

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote with real-time data priority.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) or None

        """
        return self.pricing_service.get_bid_ask_spread(symbol)

    def subscribe_for_trading(self, symbol: str) -> None:
        """Subscribe to real-time data for a symbol that will be traded.

        Args:
            symbol: Stock symbol to subscribe to

        """
        self.pricing_service.subscribe_for_trading(symbol)

    def unsubscribe_after_trading(self, symbol: str) -> None:
        """Unsubscribe from real-time data after trading is complete.

        Args:
            symbol: Stock symbol to unsubscribe from

        """
        self.pricing_service.unsubscribe_after_order(symbol)

    def get_price_for_order_placement(self, symbol: str) -> float | None:
        """Get optimized price for order placement with just-in-time subscription.

        Args:
            symbol: Stock symbol for order placement

        Returns:
            Most accurate price available, or fallback price

        """
        # Try optimized real-time pricing
        price = self.pricing_service.get_optimized_price_for_order(symbol)
        if price is not None:
            return price

        # Fallback to standard real-time or REST
        if self._fallback_provider is not None:
            return self._fallback_provider(symbol)

        return None

    def is_connected(self) -> bool:
        """Check if real-time pricing is available."""
        return self.pricing_service.is_connected()

    def get_stats(self) -> dict[str, str | int | float | datetime | bool]:
        """Get real-time pricing statistics."""
        return self.pricing_service.get_stats()

    def get_subscribed_symbols(self) -> set[str]:
        """Get currently subscribed symbols."""
        return self.pricing_service.get_subscribed_symbols()
