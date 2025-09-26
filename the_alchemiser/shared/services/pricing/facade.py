"""Business Unit: shared | Status: current.

Main facade for the pricing service that maintains the original API while delegating
to extracted components.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from datetime import datetime

from the_alchemiser.shared.types.market_data import PriceDataModel, QuoteModel

from .bootstrap import load_pricing_config, validate_config
from .cleanup import QuoteCleanupManager
from .compat import get_real_time_quote_with_warning
from .data_store import PricingDataStore
from .models import AlpacaQuoteData, AlpacaTradeData, QuoteValues, RealTimeQuote
from .quote_parser import extract_quote_values, extract_symbol_from_quote, get_quote_timestamp
from .stats import PricingStats
from .stream_runner import StreamRunner
from .subscription_planner import SubscriptionPlanner
from .trade_parser import extract_trade_data, get_symbol_from_trade

logger = logging.getLogger(__name__)


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
        # Load and validate configuration
        self._config = load_pricing_config(
            api_key=api_key,
            secret_key=secret_key,
            paper_trading=paper_trading,
            max_symbols=max_symbols,
        )
        validate_config(self._config)

        # Initialize core components
        self._data_store = PricingDataStore()
        self._stats = PricingStats(self._data_store)
        self._subscription_planner = SubscriptionPlanner(max_symbols)
        self._cleanup_manager = QuoteCleanupManager(self._data_store)

        # Subscription management
        self._subscribed_symbols: set[str] = set()
        self._subscription_priority: dict[str, float] = {}
        self._subscription_lock = threading.Lock()

        # Stream management
        self._stream_runner: StreamRunner | None = None

        # Initialize logger for this instance
        self.logger = logging.getLogger(__name__)

        logging.info(
            f"📡 Real-time pricing service initialized ({'paper' if paper_trading else 'live'})"
        )

    @property
    def api_key(self) -> str:
        """Get API key."""
        return self._config.api_key

    @property
    def secret_key(self) -> str:
        """Get secret key."""
        return self._config.secret_key

    @property
    def paper_trading(self) -> bool:
        """Get paper trading flag."""
        return self._config.paper_trading

    def start(self) -> bool:
        """Start the real-time pricing service.

        Returns:
            True if service started successfully

        """
        if self._stream_runner is not None and self._stream_runner.is_connected():
            self.logger.warning("Real-time pricing service already running")
            return True

        self.logger.info("🚀 Starting real-time pricing service...")

        # Create stream runner
        self._stream_runner = StreamRunner(
            api_key=self._config.api_key,
            secret_key=self._config.secret_key,
            feed=self._config.feed,
            quote_handler=self._on_quote,
            trade_handler=self._on_trade,
            get_symbols_callback=self._get_symbols_to_subscribe,
        )

        # Start cleanup manager
        self._cleanup_manager.start_cleanup()

        # Start stream
        success = self._stream_runner.start()

        if success:
            self._stats.set_connected(connected=True)
            self.logger.info("✅ Real-time pricing service started successfully")
        else:
            self.logger.error("❌ Failed to start real-time pricing service")

        return success

    def stop(self) -> None:
        """Stop the real-time pricing service."""
        self.logger.info("🛑 Stopping real-time pricing service...")

        # Stop cleanup manager
        self._cleanup_manager.stop_cleanup()

        # Stop stream
        if self._stream_runner:
            self._stream_runner.stop()
            self._stream_runner = None

        self._stats.set_connected(connected=False)
        self.logger.info("🛑 Real-time pricing service stopped")

    def get_real_time_quote(self, symbol: str) -> RealTimeQuote | None:
        """Get real-time quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            RealTimeQuote object or None if not available

        Warning:
            This method is deprecated. Use get_quote_data() for new code.

        """
        return get_real_time_quote_with_warning(
            symbol, self._data_store.get_real_time_quote
        )

    def get_quote_data(self, symbol: str) -> QuoteModel | None:
        """Get structured quote data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            QuoteModel object with bid/ask prices and sizes, or None if not available

        """
        return self._data_store.get_quote_data(symbol)

    def get_price_data(self, symbol: str) -> PriceDataModel | None:
        """Get structured price data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            PriceDataModel object with price, bid/ask, and volume, or None if not available

        """
        return self._data_store.get_price_data(symbol)

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

        return quote.mid_price

    def get_bid_ask_spread(self, symbol: str) -> tuple[float, float] | None:
        """Get bid/ask spread for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) or None if not available

        """
        quote = self.get_quote_data(symbol)
        if not quote:
            return None

        # Additional validation: ensure ask > bid for a reasonable spread
        if quote.ask_price <= quote.bid_price:
            logging.warning(
                f"Invalid spread for {symbol}: bid={quote.bid_price}, ask={quote.ask_price} (ask <= bid)"
            )
            return None

        return quote.bid_price, quote.ask_price

    def is_connected(self) -> bool:
        """Check if the real-time service is connected."""
        return self._stats.is_connected()

    def get_stats(self) -> dict[str, str | int | float | datetime | bool]:
        """Get service statistics."""
        return self._stats.get_stats()

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
            priority = self._subscription_planner.get_default_priority()

        normalized_symbols = self._subscription_planner.normalize_symbols(symbols)
        if not normalized_symbols:
            return {}

        logging.info(
            f"📡 Bulk subscribing to {len(normalized_symbols)} symbols with priority {priority:.1f}"
        )

        with self._subscription_lock:
            subscription_plan = self._subscription_planner.plan_bulk_subscription(
                normalized_symbols, priority, self._subscribed_symbols, self._subscription_priority
            )
            self._subscription_planner.execute_subscription_plan(
                subscription_plan, priority, self._subscribed_symbols, 
                self._subscription_priority, self._stats.get_raw_stats()
            )

        self._restart_stream_if_needed(subscription_plan.successfully_added)

        logging.info(
            f"✅ Bulk subscription complete: {subscription_plan.successfully_added}/"
            f"{len(subscription_plan.symbols_to_add)} new symbols subscribed"
        )
        return subscription_plan.results

    # Alias for backward compatibility
    def bulk_subscribe_symbols(
        self, symbols: list[str], priority: float | None = None
    ) -> dict[str, bool]:
        """Alias for subscribe_symbols_bulk for backward compatibility."""
        return self.subscribe_symbols_bulk(symbols, priority)

    def subscribe_symbol(self, symbol: str, priority: float | None = None) -> None:
        """Subscribe to real-time updates for a specific symbol.

        Args:
            symbol: Stock symbol to subscribe to
            priority: Priority score (higher = more important). Defaults to timestamp.

        """
        self.subscribe_symbols_bulk([symbol], priority)

    def unsubscribe_symbol(self, symbol: str) -> None:
        """Unsubscribe from real-time updates for a symbol.

        Args:
            symbol: Stock symbol to unsubscribe from

        """
        with self._subscription_lock:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
                self._subscription_priority.pop(symbol, None)
                logging.info(f"📡 Unsubscribed from {symbol}")
                self._restart_stream_if_needed(0)

    def subscribe_for_trading(self, symbol: str) -> None:
        """Subscribe for trading with high priority."""
        self.subscribe_symbol(symbol, priority=1000.0)

    def subscribe_for_order_placement(self, symbol: str) -> None:
        """Subscribe for order placement with highest priority."""
        self.subscribe_symbol(symbol, priority=2000.0)

    def unsubscribe_after_order(self, symbol: str) -> None:
        """Unsubscribe after order completion (alias for unsubscribe_symbol)."""
        self.unsubscribe_symbol(symbol)

    def get_optimized_price_for_order(self, symbol: str) -> float | None:
        """Get optimized price for order placement with brief wait for updates.

        Args:
            symbol: Stock symbol

        Returns:
            Best available price after brief wait

        """
        max_wait = 2.0  # Maximum wait time in seconds
        check_interval = 0.1  # Check every 100ms
        elapsed = 0.0

        while elapsed < max_wait:
            price = self.get_real_time_price(symbol)
            if price is not None:
                break

            time.sleep(check_interval)
            elapsed += check_interval

        # Get the best available price
        return self.get_real_time_price(symbol)

    def get_subscribed_symbols(self) -> set[str]:
        """Get currently subscribed symbols.

        Returns:
            Set of subscribed symbols

        """
        with self._subscription_lock:
            return self._subscribed_symbols.copy()

    # Internal methods

    def _get_symbols_to_subscribe(self) -> list[str]:
        """Get current subscription list in a thread-safe way."""
        with self._subscription_lock:
            return list(self._subscribed_symbols)

    def _restart_stream_if_needed(self, successfully_added: int) -> None:
        """Restart stream if new symbols were added and we're connected."""
        if successfully_added > 0 and self.is_connected() and self._stream_runner:
            logging.info(f"🔄 Restarting stream to add {successfully_added} new subscriptions")
            self._stream_runner.restart_for_new_subscription()

    async def _on_quote(self, data: AlpacaQuoteData) -> None:
        """Handle incoming quote data with async processing optimizations."""
        try:
            symbol = extract_symbol_from_quote(data)
            if not symbol:
                self.logger.warning("Received quote with no symbol")
                return

            quote_values = extract_quote_values(data)
            timestamp = get_quote_timestamp(quote_values.timestamp_raw)

            await self._process_quote_data(symbol, quote_values, timestamp, data)
            self._stats.increment_quotes_received()
            self._data_store.update_quote_timestamp(symbol)

        except Exception as e:
            await self._handle_async_error(f"Error processing quote: {e}")

    async def _process_quote_data(self, symbol: str, quote_values: QuoteValues, timestamp: datetime, original_data: AlpacaQuoteData) -> None:
        """Process and store quote data."""
        # Store complete quote data (non-blocking)
        self._data_store.update_latest_quote(symbol, original_data)

        if quote_values.bid_price is not None and quote_values.ask_price is not None:
            # Update tracking data
            self._data_store.update_latest_bid_ask(symbol, quote_values.bid_price, quote_values.ask_price)
            
            # Use asyncio.to_thread for potentially blocking operations
            await asyncio.to_thread(
                self._data_store.update_quote_data,
                symbol,
                quote_values.bid_price,
                quote_values.ask_price,
                quote_values.bid_size,
                quote_values.ask_size,
                timestamp,
            )

    async def _on_trade(self, trade: AlpacaTradeData) -> None:
        """Handle incoming trade updates from Alpaca stream."""
        try:
            trade_data = extract_trade_data(trade)
            if not trade_data:
                return

            # Use asyncio.to_thread for potentially blocking lock operations
            await asyncio.to_thread(
                self._data_store.update_trade_data,
                trade_data.symbol,
                trade_data.price,
                trade_data.timestamp,
                trade_data.volume,
            )

            # Update statistics
            self._stats.increment_trades_received()
            self._stats.update_last_heartbeat()

        except Exception as e:
            symbol_str = get_symbol_from_trade(trade)
            await self._handle_async_error(f"Error processing trade for {symbol_str}: {e}")

    async def _handle_async_error(self, message: str) -> None:
        """Handle errors in async processing."""
        if self._stream_runner:
            error_task = asyncio.create_task(
                asyncio.to_thread(self.logger.error, message, exc_info=True)
            )
            self._stream_runner.add_background_task(error_task)
        else:
            self.logger.error(message, exc_info=True)