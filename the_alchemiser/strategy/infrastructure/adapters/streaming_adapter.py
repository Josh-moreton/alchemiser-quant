"""Business Unit: strategy & signal generation | Status: current.

Streaming adapter for strategy context.

Handles real-time price subscriptions via WebSocket for strategy signal generation.
Provides callback-based API for current price requests.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol, cast


class _RealTimePricingProtocol(Protocol):
    """Structural protocol for the real-time pricing manager used by this service."""

    def set_fallback_provider(self, provider: Callable[[str], float | None]) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_connected(self) -> bool: ...
    def get_current_price(self, symbol: str) -> float | None: ...
    def subscribe_for_trading(self, symbol: str) -> None: ...


class StreamingAdapter:
    """Adapter for real-time price streaming via WebSocket for strategy context."""

    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True) -> None:
        """Initialize streaming adapter.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading

        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_trading = paper_trading
        self._real_time_pricing: _RealTimePricingProtocol | None = None
        self._fallback_provider: Callable[[str], float | None] | None = None

    def start(self) -> None:
        """Start the real-time pricing service."""
        try:
            from the_alchemiser.infrastructure.data_providers.real_time_pricing import (
                RealTimePricingManager,
            )

            self._real_time_pricing = cast(
                _RealTimePricingProtocol,
                RealTimePricingManager(
                    api_key=self.api_key,
                    secret_key=self.secret_key,
                    paper_trading=self.paper_trading,
                ),
            )

            if self._fallback_provider:
                self._real_time_pricing.set_fallback_provider(self._fallback_provider)

            self._real_time_pricing.start()
            logging.info("Real-time pricing service started")

        except ImportError as e:
            logging.warning(f"Real-time pricing not available: {e}")
            self._real_time_pricing = None

    def stop(self) -> None:
        """Stop the real-time pricing service."""
        if self._real_time_pricing:
            self._real_time_pricing.stop()
            logging.info("Real-time pricing service stopped")

    def is_connected(self) -> bool:
        """Check if the streaming service is connected.

        Returns:
            True if connected, False otherwise

        """
        if self._real_time_pricing:
            return self._real_time_pricing.is_connected()
        return False

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol via streaming.

        Args:
            symbol: Symbol to get price for

        Returns:
            Current price or None if not available

        """
        if self._real_time_pricing:
            return self._real_time_pricing.get_current_price(symbol)

        # Fallback to provider if available
        if self._fallback_provider:
            return self._fallback_provider(symbol)

        return None

    def subscribe_for_trading(self, symbol: str) -> None:
        """Subscribe to real-time prices for a symbol.

        Args:
            symbol: Symbol to subscribe to

        """
        if self._real_time_pricing:
            self._real_time_pricing.subscribe_for_trading(symbol)
            logging.info(f"Subscribed to real-time prices for {symbol}")
        else:
            logging.warning(f"Cannot subscribe to {symbol} - real-time pricing not available")

    def set_fallback_provider(self, provider: Callable[[str], float | None]) -> None:
        """Set fallback price provider for when streaming is not available.

        Args:
            provider: Function that takes symbol and returns price

        """
        self._fallback_provider = provider
        if self._real_time_pricing:
            self._real_time_pricing.set_fallback_provider(provider)

    def get_status(self) -> dict[str, bool | str]:
        """Get status information for the streaming service.

        Returns:
            Dictionary with status information

        """
        return {
            "service_available": self._real_time_pricing is not None,
            "connected": self.is_connected(),
            "has_fallback": self._fallback_provider is not None,
            "paper_trading": self.paper_trading,
        }
