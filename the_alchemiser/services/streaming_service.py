#!/usr/bin/env python3
"""
Streaming Service

Handles real-time price subscriptions via WebSocket.
Provides callback-based API for current price requests.
"""

import logging
from collections.abc import Callable


class StreamingService:
    """Service for real-time price streaming via WebSocket."""

    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True) -> None:
        """
        Initialize streaming service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_trading = paper_trading
        self._real_time_pricing = None
        self._fallback_provider: Callable[[str], float | None] | None = None

    def start(self) -> None:
        """Start the real-time pricing service."""
        try:
            from the_alchemiser.infrastructure.data_providers.real_time_pricing import (
                RealTimePricingManager,
            )

            self._real_time_pricing = RealTimePricingManager(
                self.api_key, self.secret_key, self.paper_trading
            )
            if self._fallback_provider:
                self._real_time_pricing.set_fallback_provider(self._fallback_provider)
            self._real_time_pricing.start()
            logging.info("✅ Real-time pricing service started")

        except Exception as e:
            logging.warning(f"Failed to start real-time pricing service: {e}")
            self._real_time_pricing = None

    def stop(self) -> None:
        """Stop the real-time pricing service."""
        if self._real_time_pricing:
            try:
                self._real_time_pricing.stop()
                logging.info("Real-time pricing service stopped")
            except Exception as e:
                logging.warning(f"Error stopping real-time pricing service: {e}")
            finally:
                self._real_time_pricing = None

    def set_fallback_provider(self, provider: Callable[[str], float | None]) -> None:
        """
        Set fallback provider for when streaming is unavailable.

        Args:
            provider: Function that takes symbol and returns price
        """
        self._fallback_provider = provider
        if self._real_time_pricing:
            self._real_time_pricing.set_fallback_provider(provider)

    def is_connected(self) -> bool:
        """Check if the streaming service is connected."""
        return self._real_time_pricing is not None and self._real_time_pricing.is_connected()

    def get_current_price(self, symbol: str) -> float | None:
        """
        Get current market price for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if unavailable
        """
        if self._real_time_pricing and self.is_connected():
            # Just-in-time subscription: subscribe only when we need pricing
            self.subscribe_for_trading(symbol)

            # Give a moment for real-time data to flow
            import time

            time.sleep(0.5)  # Brief wait for subscription to activate

            # Get real-time price
            price = self._real_time_pricing.get_current_price(symbol)
            if price is not None:
                logging.debug(f"Real-time price for {symbol}: ${price:.2f}")
                return price

        # Fallback to REST API if available
        if self._fallback_provider:
            return self._fallback_provider(symbol)

        return None

    def get_current_price_for_order(self, symbol: str) -> tuple[float | None, Callable[[], None]]:
        """
        Get current price specifically for order placement with optimized subscription management.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (price, cleanup_function)
        """
        from the_alchemiser.services.price_fetching_utils import (
            create_cleanup_function,
            subscribe_for_real_time,
        )

        # Create cleanup function
        cleanup: Callable[[], None] = create_cleanup_function(self._real_time_pricing, symbol)

        # Try real-time pricing with just-in-time subscription
        if subscribe_for_real_time(self._real_time_pricing, symbol):
            if self._real_time_pricing:
                price = self._real_time_pricing.get_current_price(symbol)
                if price is not None:
                    logging.info(f"Using real-time price for {symbol} order: ${price:.2f}")
                    return price, cleanup

        # Fallback to REST API
        price = self._fallback_provider(symbol) if self._fallback_provider else None
        if price is not None:
            logging.info(f"Using REST API price for {symbol} order: ${price:.2f}")

        return price, cleanup

    def subscribe_for_trading(self, symbol: str) -> None:
        """Subscribe to real-time data for a symbol used in trading."""
        if self._real_time_pricing:
            self._real_time_pricing.subscribe_for_trading(symbol)
