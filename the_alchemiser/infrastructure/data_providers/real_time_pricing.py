#!/usr/bin/env python3
"""Real-time WebSocket Price Streaming for Alpaca Trading.

This module provides real-time stock price updates via Alpaca's WebSocket streams
to ensure accurate limit order pricing. It maintains current bid/ask quotes and
last trade prices for symbols used in trading strategies.

DESIGN PHILOSOPHY:
=================
- Real-time pricing for accurate limit orders
- Minimal latency for high-frequency quote updates
- Thread-safe quote storage with automatic cleanup
- Graceful fallback to REST API when needed
- Subscribe only to symbols being actively traded

KEY FEATURES:
============
1. Real-time quote updates (bid/ask/last price)
2. Automatic symbol subscription management
3. Thread-safe price storage
4. Connection health monitoring
5. Smart reconnection logic
6. Memory-efficient quote caching
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from alpaca.data.enums import DataFeed
from alpaca.data.live import StockDataStream
from alpaca.data.models import Quote, Trade

# TODO: Phase 11 - Types available for future migration to structured pricing data
# from the_alchemiser.domain.types import PriceData, QuoteData


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


class RealTimePricingService:
    """Real-time pricing service using Alpaca's WebSocket data streams.

    Provides up-to-date bid/ask quotes and last trade prices for accurate
    limit order placement. Automatically manages subscriptions based on
    active trading symbols.
    """

    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True) -> None:
        """Initialize real-time pricing service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading environment

        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_trading = paper_trading

        # Real-time quote storage (thread-safe)
        self._quotes: dict[str, RealTimeQuote] = {}
        self._quotes_lock = threading.RLock()

        # Subscription management
        self._subscribed_symbols: set[str] = set()
        self._subscription_lock = threading.RLock()
        self._subscription_priority: dict[str, float] = {}  # symbol -> priority score
        self._max_symbols = 5  # Stay under Alpaca's subscription limits

        # Connection management
        self._stream: StockDataStream | None = None
        self._stream_thread: threading.Thread | None = None
        self._connected = False
        self._should_reconnect = True

        # Quote age tracking for cleanup
        self._last_update: dict[str, datetime] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._max_quote_age = 600  # 10 minutes

        # Statistics
        self._stats: dict[str, Any] = {
            "quotes_received": 0,
            "trades_received": 0,
            "connection_errors": 0,
            "subscription_limit_hits": 0,
            "last_heartbeat": None,
        }

        logging.info(
            f"📡 Real-time pricing service initialized ({'paper' if paper_trading else 'live'})"
        )

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
            self._stream = StockDataStream(
                api_key=self.api_key,
                secret_key=self.secret_key,
                feed=DataFeed.IEX,  # Use IEX feed for both paper and live (free tier)
                # feed=DataFeed.SIP if not self.paper_trading else DataFeed.IEX  # Uncomment when SIP subscription is active
            )

            # NOTE: Do NOT subscribe to wildcard "*" - it hits subscription limits immediately
            # We'll subscribe to specific symbols only when needed via subscribe_for_order_placement()

            # Start the stream in a background thread
            self._should_reconnect = True
            self._stream_thread = threading.Thread(
                target=self._run_stream, name="RealTimePricing", daemon=True
            )
            self._stream_thread.start()

            # Wait a moment for connection
            for _ in range(50):  # 5 second timeout
                if self._connected:
                    break
                time.sleep(0.1)

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

    def _run_stream(self) -> None:
        """Run the WebSocket stream with automatic reconnection."""
        while self._should_reconnect:
            try:
                if self._stream:
                    logging.info("📡 Starting real-time data stream...")
                    self._connected = True
                    self._stats["last_heartbeat"] = datetime.now(UTC)
                    self._stream.run()

            except Exception as e:
                self._connected = False
                self._stats["connection_errors"] += 1
                logging.error(f"Real-time stream error: {e}")

                if self._should_reconnect:
                    logging.info("🔄 Reconnecting in 10 seconds...")
                    time.sleep(10)

    async def _on_quote(self, quote: Quote | dict[str, Any]) -> None:
        """Handle incoming quote updates."""
        try:
            # Handle both Quote objects and dictionary format
            if isinstance(quote, dict):
                symbol = quote.get("symbol")
                bid_price = quote.get("bid_price", 0)
                ask_price = quote.get("ask_price", 0)
                timestamp = quote.get("timestamp", datetime.now(UTC))
            else:
                symbol = quote.symbol
                bid_price = quote.bid_price
                ask_price = quote.ask_price
                timestamp = quote.timestamp

            if not symbol:
                return

            # Update quote data
            with self._quotes_lock:
                current_quote = self._quotes.get(symbol)
                last_price = current_quote.last_price if current_quote else 0.0

                self._quotes[symbol] = RealTimeQuote(
                    bid=float(bid_price or 0),
                    ask=float(ask_price or 0),
                    last_price=last_price,  # Keep existing last price from trades
                    timestamp=timestamp or datetime.now(UTC),
                )

                self._last_update[symbol] = datetime.now(UTC)
                self._stats["quotes_received"] += 1

            # Update heartbeat
            self._stats["last_heartbeat"] = datetime.now(UTC)

            logging.debug(
                f"📊 Quote: {symbol} ${float(bid_price or 0):.2f}/${float(ask_price or 0):.2f}"
            )

        except Exception as e:
            symbol_str = str(
                quote.get("symbol", "unknown")
                if isinstance(quote, dict)
                else getattr(quote, "symbol", "unknown")
            )
            logging.error(f"Error processing quote for {symbol_str}: {e}")

    async def _on_trade(self, trade: Trade | dict[str, Any]) -> None:
        """Handle incoming trade updates."""
        try:
            # Handle both Trade objects and dictionary format
            if isinstance(trade, dict):
                symbol = trade.get("symbol")
                price = trade.get("price", 0)
                size = trade.get("size", 0)
                timestamp = trade.get("timestamp", datetime.now(UTC))
            else:
                symbol = trade.symbol
                price = trade.price
                size = trade.size
                timestamp = trade.timestamp

            if not symbol:
                return

            # Update last trade price
            with self._quotes_lock:
                current_quote = self._quotes.get(symbol)
                if current_quote:
                    # Update existing quote with new trade price
                    self._quotes[symbol] = RealTimeQuote(
                        bid=current_quote.bid,
                        ask=current_quote.ask,
                        last_price=float(price or 0),
                        timestamp=timestamp or datetime.now(UTC),
                    )
                else:
                    # Create new quote with trade price only
                    self._quotes[symbol] = RealTimeQuote(
                        bid=0.0,
                        ask=0.0,
                        last_price=float(price or 0),
                        timestamp=timestamp or datetime.now(UTC),
                    )

                self._last_update[symbol] = datetime.now(UTC)
                self._stats["trades_received"] += 1

            # Update heartbeat
            self._stats["last_heartbeat"] = datetime.now(UTC)

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
                        self._quotes.pop(symbol, None)
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

        """
        with self._quotes_lock:
            return self._quotes.get(symbol)

    def get_real_time_price(self, symbol: str) -> float | None:
        """Get the best available real-time price for a symbol.

        Priority: mid-price > last trade > bid > ask

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if not available

        """
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

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "connected": self._connected,
            "symbols_tracked": len(self._quotes),
            "uptime_seconds": (
                (datetime.now(UTC) - self._stats["last_heartbeat"]).total_seconds()
                if self._stats["last_heartbeat"]
                else 0
            ),
        }

    def subscribe_symbol(self, symbol: str, priority: float | None = None) -> None:
        """Subscribe to real-time updates for a specific symbol with smart limit management.

        Args:
            symbol: Stock symbol to subscribe to
            priority: Priority score (higher = more important). Defaults to timestamp.

        """
        if priority is None:
            priority = time.time()  # Use current timestamp as default priority

        with self._subscription_lock:
            # Check if we need to manage subscription limits
            if (
                symbol not in self._subscribed_symbols
                and len(self._subscribed_symbols) >= self._max_symbols
            ):
                # Find lowest priority symbol to unsubscribe
                lowest_priority_symbol = min(
                    self._subscribed_symbols, key=lambda s: self._subscription_priority.get(s, 0)
                )
                lowest_priority = self._subscription_priority.get(lowest_priority_symbol, 0)

                if priority > lowest_priority:
                    # Unsubscribe lowest priority symbol
                    logging.info(
                        f"📊 Subscription limit reached. Replacing {lowest_priority_symbol} (priority: {lowest_priority:.1f}) with {symbol} (priority: {priority:.1f})"
                    )
                    self.unsubscribe_symbol(lowest_priority_symbol)
                    self._stats["subscription_limit_hits"] += 1
                else:
                    logging.warning(
                        f"⚠️ Cannot subscribe to {symbol} - priority {priority:.1f} too low (limit: {self._max_symbols} symbols)"
                    )
                    return

            if symbol not in self._subscribed_symbols:
                self._subscribed_symbols.add(symbol)
                self._subscription_priority[symbol] = priority

                if self._stream and self._connected:
                    try:
                        # Subscribe to both quotes and trades for this symbol
                        self._stream.subscribe_quotes(self._on_quote, symbol)
                        self._stream.subscribe_trades(self._on_trade, symbol)
                        logging.info(
                            f"📡 Subscribed to real-time data for {symbol} (priority: {priority:.1f})"
                        )
                    except Exception as e:
                        logging.error(f"Error subscribing to {symbol}: {e}")
            else:
                # Update priority for existing subscription
                self._subscription_priority[symbol] = max(
                    self._subscription_priority.get(symbol, 0), priority
                )

    def unsubscribe_symbol(self, symbol: str) -> None:
        """Unsubscribe from real-time updates for a specific symbol.

        Args:
            symbol: Stock symbol to unsubscribe from

        """
        with self._subscription_lock:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
                self._subscription_priority.pop(symbol, None)

                # Remove quote data
                with self._quotes_lock:
                    self._quotes.pop(symbol, None)
                    self._last_update.pop(symbol, None)

                logging.info(f"📴 Unsubscribed from real-time data for {symbol}")

    def subscribe_for_trading(self, symbol: str) -> None:
        """Subscribe to a symbol with high priority for active trading.

        Args:
            symbol: Stock symbol being actively traded

        """
        # High priority for active trading
        trading_priority = time.time() + 86400  # Current time + 1 day
        self.subscribe_symbol(symbol, trading_priority)

    def subscribe_for_order_placement(self, symbol: str) -> None:
        """Subscribe to a symbol temporarily for order placement.
        Uses the highest priority to ensure subscription.

        Args:
            symbol: Stock symbol for order placement

        """
        # Maximum priority for order placement
        order_priority = time.time() + 172800  # Current time + 2 days (highest priority)
        self.subscribe_symbol(symbol, order_priority)
        logging.debug(
            f"Subscribed to {symbol} for order placement (priority: {order_priority:.1f})"
        )

    def unsubscribe_after_order(self, symbol: str) -> None:
        """Unsubscribe from a symbol after order placement is complete.
        Only unsubscribes if no other high-priority needs exist.

        Args:
            symbol: Stock symbol to potentially unsubscribe from

        """
        with self._subscription_lock:
            if symbol in self._subscribed_symbols:
                # Check if this was a temporary subscription for order placement
                current_priority = self._subscription_priority.get(symbol, 0)
                base_priority = time.time()  # Current time as baseline

                # If priority is very high (order placement), reduce it
                if current_priority > base_priority + 86400:  # More than 1 day ahead
                    # Reduce priority to normal level
                    self._subscription_priority[symbol] = base_priority
                    logging.debug(f"Reduced priority for {symbol} after order placement")

                    # If we're over subscription limits, this may trigger unsubscription
                    # during the next subscription request
                else:
                    logging.debug(
                        f"Keeping subscription for {symbol} (normal priority: {current_priority:.1f})"
                    )

    def get_optimized_price_for_order(self, symbol: str) -> float | None:
        """Get the most accurate price for order placement with temporary subscription.

        Args:
            symbol: Stock symbol

        Returns:
            Current price optimized for order accuracy

        """
        # Subscribe with highest priority for order placement
        self.subscribe_for_order_placement(symbol)

        # Wait briefly for real-time data
        import time

        time.sleep(0.5)

        # Get the best available price
        return self.get_real_time_price(symbol)

    def get_subscribed_symbols(self) -> set[str]:
        """Get set of currently subscribed symbols."""
        with self._subscription_lock:
            return self._subscribed_symbols.copy()


class RealTimePricingManager:
    """Manager class for real-time pricing integration with existing data providers.

    Provides a clean interface for integrating real-time pricing into
    existing trading systems while maintaining backward compatibility.
    """

    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True) -> None:
        """Initialize real-time pricing manager.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading environment

        """
        self.pricing_service = RealTimePricingService(api_key, secret_key, paper_trading)
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

        """
        # Try real-time data first
        price = self.pricing_service.get_real_time_price(symbol)
        if price is not None:
            return price

        # Fallback to REST API
        if self._fallback_provider:
            return self._fallback_provider(symbol)

        return None

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
        if self._fallback_provider:
            return self._fallback_provider(symbol)

        return None

    def is_connected(self) -> bool:
        """Check if real-time pricing is available."""
        return self.pricing_service.is_connected()

    def get_stats(self) -> dict[str, Any]:
        """Get real-time pricing statistics."""
        return self.pricing_service.get_stats()

    def get_subscribed_symbols(self) -> set[str]:
        """Get currently subscribed symbols."""
        return self.pricing_service.get_subscribed_symbols()
