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

REFACTORING NOTE (Phase 11):
============================
This module has been refactored into focused components:
- RealTimeDataProcessor: Data extraction and processing
- SubscriptionManager: Subscription logic and priority management
- RealTimeStreamManager: Stream lifecycle and connection management
- RealTimePriceStore: Price storage and retrieval

This file now serves as the main orchestrator, delegating to these components.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import threading
import time
import uuid
import warnings
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from dotenv import load_dotenv

from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    StreamingError,
    WebSocketError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.real_time_data_processor import (
    RealTimeDataProcessor,
)
from the_alchemiser.shared.services.real_time_price_store import RealTimePriceStore
from the_alchemiser.shared.services.real_time_stream_manager import (
    RealTimeStreamManager,
)
from the_alchemiser.shared.services.subscription_manager import SubscriptionManager
from the_alchemiser.shared.types.market_data import (
    PriceDataModel,
    QuoteModel,
    RealTimeQuote,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
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

# High priority offset for order placement subscriptions
HIGH_PRIORITY_OFFSET = 1000


class RealTimePricingService:
    """Real-time pricing service using Alpaca's WebSocket data streams.

    Provides up-to-date bid/ask quotes and last trade prices for accurate
    limit order placement. Automatically manages subscriptions based on
    active trading symbols.

    This service delegates to specialized components for cleaner separation of concerns:
    - Data processing: RealTimeDataProcessor
    - Subscription management: SubscriptionManager
    - Stream lifecycle: RealTimeStreamManager
    - Price storage: RealTimePriceStore
    """

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        paper_trading: bool = True,
        max_symbols: int = 30,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize real-time pricing service with WebSocket streaming.

        Args:
            api_key: Alpaca API key (reads from env if not provided)
            secret_key: Alpaca secret key (reads from env if not provided)
            paper_trading: Whether to use paper trading endpoints
            max_symbols: Maximum number of symbols to subscribe to concurrently
            correlation_id: Optional correlation ID for traceability

        Raises:
            ConfigurationError: If API credentials are not provided or found in environment
            ValueError: If max_symbols is not positive

        """
        # Validate max_symbols parameter
        if max_symbols <= 0:
            raise ValueError("max_symbols must be positive")

        # Load credentials from environment if not provided
        if not api_key or not secret_key:
            load_dotenv()
            api_key = api_key or os.getenv("ALPACA_KEY")
            secret_key = secret_key or os.getenv("ALPACA_SECRET")

        if not api_key or not secret_key:
            logger.error("❌ Alpaca credentials not provided or found in environment")
            raise ConfigurationError(
                "Alpaca API credentials required", config_key="ALPACA_KEY/ALPACA_SECRET"
            )

        self._api_key = api_key
        self._secret_key = secret_key
        self._paper_trading = paper_trading

        # Correlation ID for traceability
        self._correlation_id = correlation_id or str(uuid.uuid4())

        # Initialize component modules
        self._data_processor = RealTimeDataProcessor()
        self._subscription_manager = SubscriptionManager(max_symbols=max_symbols)
        self._price_store = RealTimePriceStore()

        # Stream manager initialized in start() with callbacks
        self._stream_manager: RealTimeStreamManager | None = None

        # Statistics tracking with thread safety
        self._stats: dict[str, int] = {
            "quotes_received": 0,
            "trades_received": 0,
        }
        self._stats_lock = threading.Lock()
        self._datetime_stats: dict[str, datetime] = {}

        # Task tracking for async operations
        self._background_tasks: set[asyncio.Task[None]] = set()

        # Initialize logger for this instance
        self.logger = get_logger(__name__)

        self.logger.info(
            f"📡 Real-time pricing service initialized ({'paper' if paper_trading else 'live'})",
            extra={"correlation_id": self._correlation_id},
        )

    @property
    def correlation_id(self) -> str:
        """Get correlation ID for this service instance."""
        return self._correlation_id

    @property
    def paper_trading(self) -> bool:
        """Get paper trading flag."""
        return self._paper_trading

    def _get_subscribed_symbols_list(self) -> list[str]:
        """Get list of currently subscribed symbols."""
        return list(self._subscription_manager.get_subscribed_symbols())

    def _is_stream_connected(self) -> bool:
        """Check if stream manager is connected."""
        return self._stream_manager.is_connected() if self._stream_manager else False

    def start(self) -> bool:
        """Start the real-time pricing service.

        Returns:
            True if started successfully, False otherwise

        Raises:
            StreamingError: If stream fails to start
            ConfigurationError: If configuration is invalid
            WebSocketError: If WebSocket connection fails

        """
        try:
            # Initialize stream manager with callbacks
            self._stream_manager = RealTimeStreamManager(
                api_key=self._api_key,
                secret_key=self._secret_key,
                feed=self._get_feed(),
                on_quote=self._on_quote,
                on_trade=self._on_trade,
            )

            # Start the stream
            result = self._stream_manager.start(
                get_symbols_callback=self._get_subscribed_symbols_list
            )

            if result:
                # Start cleanup thread
                self._price_store.start_cleanup(is_connected_callback=self._is_stream_connected)
                self.logger.info(
                    "✅ Real-time pricing service started successfully",
                    extra={"correlation_id": self._correlation_id},
                )
                return True

            self.logger.error(
                "❌ Failed to establish real-time pricing connection",
                extra={"correlation_id": self._correlation_id},
            )
            return False

        except (OSError, WebSocketError) as e:
            # Note: ConnectionError is a subclass of OSError, so we only catch OSError
            self.logger.error(
                "Failed to start real-time pricing service",
                extra={
                    "correlation_id": self._correlation_id,
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                },
            )
            raise StreamingError(f"Failed to start stream: {e}") from e
        except ConfigurationError:
            # Re-raise config errors
            raise
        except Exception as e:
            # Unknown error - log and raise
            self.logger.exception(
                "Unexpected error in start()",
                extra={"correlation_id": self._correlation_id},
            )
            raise StreamingError(f"Unexpected error: {e}") from e

    async def stop(self) -> None:
        """Stop the real-time pricing service.

        Raises:
            StreamingError: If there are errors during shutdown

        """
        try:
            if self._stream_manager:
                self._stream_manager.stop()

            self._price_store.stop_cleanup()

            # Cancel and await background tasks with timeout
            if self._background_tasks:
                for task in self._background_tasks:
                    if not task.done():
                        task.cancel()

                # Wait for all tasks to complete with timeout
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._background_tasks, return_exceptions=True),
                        timeout=5.0,
                    )
                except TimeoutError:
                    self.logger.warning(
                        "Some background tasks did not complete within timeout",
                        extra={"correlation_id": self._correlation_id},
                    )

                self._background_tasks.clear()

            self.logger.info(
                "🛑 Real-time pricing service stopped",
                extra={"correlation_id": self._correlation_id},
            )

        except TimeoutError:
            # Already handled in nested try/except
            pass
        except (StreamingError, WebSocketError) as e:
            self.logger.error(
                "Error stopping real-time pricing service",
                extra={
                    "correlation_id": self._correlation_id,
                    "error_type": type(e).__name__,
                },
            )
            raise
        except Exception as e:
            self.logger.exception(
                "Unexpected error in stop()",
                extra={"correlation_id": self._correlation_id},
            )
            raise StreamingError(f"Failed to stop service: {e}") from e

    async def _on_quote(self, data: AlpacaQuoteData) -> None:
        """Handle incoming quote data with async processing optimizations.

        Args:
            data: Quote data from Alpaca WebSocket

        """
        try:
            symbol = self._data_processor.extract_symbol_from_quote(data)
            if not symbol:
                self.logger.warning(
                    "Received quote with no symbol",
                    extra={"correlation_id": self._correlation_id},
                )
                return

            quote_values = self._data_processor.extract_quote_values(data)
            timestamp = self._data_processor.get_quote_timestamp(quote_values.timestamp_raw)

            try:
                await self._data_processor.log_quote_debug(
                    symbol,
                    quote_values.bid_price,
                    quote_values.ask_price,
                    self._correlation_id,
                )
            except RuntimeError:
                # Event loop executor has shut down - gracefully ignore
                return

            # Handle partial quotes: if one side is None, use the available side for both
            # This matches the REST API fallback behavior in market_data_service.py
            bid_price = quote_values.bid_price
            ask_price = quote_values.ask_price

            if bid_price is not None and ask_price is not None:
                # Both available - use as-is
                pass
            elif bid_price is not None:
                # Only bid available - use bid for both sides
                self.logger.debug(
                    f"Partial quote for {symbol}: only bid available ({bid_price}), using for both sides"
                )
                ask_price = bid_price
            elif ask_price is not None:
                # Only ask available - use ask for both sides
                self.logger.debug(
                    f"Partial quote for {symbol}: only ask available ({ask_price}), using for both sides"
                )
                bid_price = ask_price
            else:
                # Both None - skip update, keep previously stored quote
                self.logger.debug(
                    f"Empty quote for {symbol}: both bid and ask are None, keeping previous quote"
                )
                return

            # Update quote data with validated bid and ask prices
            if bid_price is not None and ask_price is not None:
                try:
                    # Use asyncio.to_thread for potentially blocking lock operations
                    await asyncio.to_thread(
                        self._price_store.update_quote_data,
                        symbol,
                        bid_price,
                        ask_price,
                        quote_values.bid_size,
                        quote_values.ask_size,
                        timestamp,
                    )
                except RuntimeError:
                    # Event loop executor has shut down - gracefully ignore
                    return

            # Update stats with thread safety
            with self._stats_lock:
                self._stats["quotes_received"] += 1

        except RuntimeError:
            # Event loop executor has shut down during error handling - gracefully ignore
            pass
        except (AttributeError, ValueError, TypeError) as e:
            # Data processing errors - non-critical, log and continue
            with contextlib.suppress(RuntimeError):
                await self._data_processor.handle_quote_error(e, self._correlation_id)
        except Exception as e:
            # Unexpected errors during quote processing
            with contextlib.suppress(RuntimeError):
                await self._data_processor.handle_quote_error(e, self._correlation_id)

    async def _on_trade(self, trade: AlpacaTradeData) -> None:
        """Handle incoming trade updates from Alpaca stream with async processing optimizations."""
        try:
            symbol = self._data_processor.extract_symbol_from_trade(trade)
            if not symbol:
                self.logger.warning(
                    "Received trade with no symbol",
                    extra={"correlation_id": self._correlation_id},
                )
                return

            price, volume, timestamp = self._data_processor.extract_trade_values(trade)

            if price and price > 0:
                try:
                    # Use asyncio.to_thread for potentially blocking lock operations
                    await asyncio.to_thread(
                        self._price_store.update_trade_data,
                        symbol,
                        price,
                        timestamp,
                        volume,
                    )
                except RuntimeError:
                    # Event loop executor has shut down - gracefully ignore
                    return

                # Update stats with thread safety
                with self._stats_lock:
                    self._stats["trades_received"] += 1
                    self._datetime_stats["last_heartbeat"] = datetime.now(UTC)

            # Yield control to event loop
            await asyncio.sleep(0)

        except RuntimeError:
            # Event loop executor has shut down during error handling - gracefully ignore
            pass
        except (AttributeError, ValueError, TypeError) as e:
            # Data processing errors - non-critical, log and continue
            with contextlib.suppress(RuntimeError):
                await asyncio.to_thread(
                    self.logger.error,
                    "Error processing trade due to data error",
                    extra={
                        "correlation_id": self._correlation_id,
                        "symbol": symbol if "symbol" in locals() else None,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
        except Exception as e:
            # Unexpected errors during trade processing
            with contextlib.suppress(RuntimeError):
                await asyncio.to_thread(
                    self.logger.error,
                    "Error processing trade due to unexpected error",
                    extra={
                        "correlation_id": self._correlation_id,
                        "symbol": symbol if "symbol" in locals() else None,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )

    # Price retrieval methods (delegate to price store)

    def get_real_time_quote(self, symbol: str) -> RealTimeQuote | None:
        """Get real-time quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            RealTimeQuote object or None if not available

        Warning:
            This method is deprecated. Use get_quote_data() for new code.

        """
        warnings.warn(
            "get_real_time_quote() is deprecated, use get_quote_data() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._price_store.get_real_time_quote(symbol)

    def get_quote_data(self, symbol: str) -> QuoteModel | None:
        """Get structured quote data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            QuoteModel object with bid/ask prices and sizes, or None if not available

        """
        return self._price_store.get_quote_data(symbol)

    def get_price_data(self, symbol: str) -> PriceDataModel | None:
        """Get structured price data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            PriceDataModel object with price, bid/ask, and volume, or None if not available

        """
        return self._price_store.get_price_data(symbol)

    def get_real_time_price(self, symbol: str) -> Decimal | None:
        """Get the best available real-time price for a symbol.

        Priority: mid-price > last trade > bid > ask

        Args:
            symbol: Stock symbol

        Returns:
            Current price as Decimal or None if not available

        Note:
            Always returns Decimal to ensure consistent numerical precision
            for financial calculations.

        """
        price = self._price_store.get_real_time_price(symbol)
        if price is None:
            return None
        # Convert float to Decimal via string to avoid precision loss
        return Decimal(str(price)) if isinstance(price, float) else price

    def get_bid_ask_spread(self, symbol: str) -> tuple[Decimal, Decimal] | None:
        """Get current bid/ask spread for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) as Decimal, or None if not available

        """
        spread = self._price_store.get_bid_ask_spread(symbol)
        if spread is None:
            return None
        bid, ask = spread
        # Ensure both are Decimal
        bid_decimal = Decimal(str(bid)) if isinstance(bid, float) else bid
        ask_decimal = Decimal(str(ask)) if isinstance(ask, float) else ask
        return (bid_decimal, ask_decimal)

    def is_connected(self) -> bool:
        """Check if the real-time service is connected."""
        return self._stream_manager.is_connected() if self._stream_manager else False

    def get_stats(self) -> dict[str, str | int | float | datetime | bool]:
        """Get service statistics."""
        last_hb = self._datetime_stats.get("last_heartbeat")
        uptime = (
            (datetime.now(UTC) - last_hb).total_seconds() if isinstance(last_hb, datetime) else 0
        )

        # Combine stats from all components
        price_stats = self._price_store.get_stats()
        sub_stats = self._subscription_manager.get_stats()

        return {
            **self._stats,
            **self._datetime_stats,
            **price_stats,
            **sub_stats,
            "connected": self.is_connected(),
            "uptime_seconds": uptime,
        }

    def _get_feed(self) -> Literal["iex", "sip"]:
        """Resolve the Alpaca data feed to use.

        Allows overriding via env vars `ALPACA_FEED` or `ALPACA_DATA_FEED`.
        Defaults to "iex". Use "sip" if you have the required subscription.
        """
        feed = (os.getenv("ALPACA_FEED") or os.getenv("ALPACA_DATA_FEED") or "iex").lower()
        if feed not in {"iex", "sip"}:
            self.logger.warning(
                f"Unknown ALPACA_FEED '{feed}', defaulting to 'iex'",
                extra={"correlation_id": self._correlation_id},
            )
            return "iex"
        return feed  # type: ignore[return-value]

    # Subscription methods (delegate to subscription manager)

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
            priority = time.time()

        normalized_symbols = self._subscription_manager.normalize_symbols(symbols)
        if not normalized_symbols:
            return {}

        self.logger.info(
            f"📡 Bulk subscribing to {len(normalized_symbols)} symbols with priority {priority:.1f}"
        )

        subscription_plan = self._subscription_manager.plan_bulk_subscription(
            normalized_symbols, priority
        )
        self._subscription_manager.execute_subscription_plan(subscription_plan, priority)

        # Auto-start on first subscription if not connected
        if subscription_plan.successfully_added > 0:
            if not self.is_connected():
                self.logger.info("🚀 Auto-starting pricing service on first subscription")
                if not self.start():
                    self.logger.error("❌ Failed to auto-start pricing service")
                    return subscription_plan.results
            elif self._stream_manager:
                self.logger.info(
                    f"🔄 Restarting stream to add {subscription_plan.successfully_added} new subscriptions"
                )
                self._stream_manager.restart()

        self.logger.info(
            f"✅ Bulk subscription complete: {subscription_plan.successfully_added}/"
            f"{len(subscription_plan.symbols_to_add)} new symbols subscribed"
        )
        return subscription_plan.results

    def subscribe_symbol(self, symbol: str, priority: float | None = None) -> None:
        """Subscribe to real-time updates for a specific symbol.

        Args:
            symbol: Stock symbol to subscribe to
            priority: Priority score (higher = more important). Defaults to timestamp.

        """
        if priority is None:
            priority = time.time()

        needs_restart, _ = self._subscription_manager.subscribe_symbol(symbol, priority)

        if needs_restart:
            # Auto-start on first subscription if not connected
            if not self.is_connected():
                self.logger.info(f"🚀 Auto-starting pricing service for {symbol}")
                self.start()
            elif self._stream_manager:
                self.logger.info(f"🔄 Restarting stream to add subscription for {symbol}")
                self._stream_manager.restart()

    def unsubscribe_symbol(self, symbol: str) -> None:
        """Unsubscribe from real-time updates for a specific symbol.

        Args:
            symbol: Stock symbol to unsubscribe from

        """
        self._subscription_manager.unsubscribe_symbol(symbol)

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
        self.subscribe_symbol(symbol, priority=time.time() + HIGH_PRIORITY_OFFSET)

        # Log for debugging
        self.logger.info(
            f"📊 Subscribed {symbol} for order placement (high priority)",
            extra={"correlation_id": self._correlation_id, "symbol": symbol},
        )

    def unsubscribe_after_order(self, symbol: str) -> None:
        """Optionally unsubscribe from a symbol after order placement.

        Args:
            symbol: The symbol to unsubscribe from

        """
        # For now, keep subscriptions active for potential re-pegging
        # Could implement cleanup logic here if needed
        self.logger.debug(f"Keeping {symbol} subscription active for monitoring")

    def get_optimized_price_for_order(self, symbol: str) -> Decimal | None:
        """Get the most accurate price for order placement with temporary subscription.

        Args:
            symbol: Stock symbol

        Returns:
            Current price as Decimal optimized for order accuracy, or None if not available

        """
        price = self._price_store.get_optimized_price_for_order(
            symbol,
            subscribe_callback=lambda s: self.subscribe_for_order_placement(s),
        )
        if price is None:
            return None
        # Convert float to Decimal via string to avoid precision loss
        return Decimal(str(price)) if isinstance(price, float) else price

    def get_subscribed_symbols(self) -> set[str]:
        """Get currently subscribed symbols.

        Returns:
            Set of subscribed symbol strings

        """
        return self._subscription_manager.get_subscribed_symbols()
