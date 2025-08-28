"""Business Unit: strategy & signal generation; Status: current.

Modern price fetching service.

Provides async/callback-based API for current price requests with
graceful REST fallback when streaming is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from the_alchemiser.services.market_data.market_data_client import MarketDataClient
from the_alchemiser.services.market_data.streaming_service import StreamingService


class ModernPriceFetchingService:
    """Modern price fetching with async support and fallback strategies."""

    def __init__(
        self,
        market_data_client: MarketDataClient,
        streaming_service: StreamingService | None,
    ) -> None:
        """Initialize modern price fetching service.

        Args:
            market_data_client: Market data client for REST API calls
            streaming_service: Streaming service for real-time data

        """
        self._market_data_client = market_data_client
        self._streaming_service = streaming_service
        self._price_callbacks: dict[str, list[Callable[[str, float], None]]] = {}

    async def get_current_price_async(
        self, symbol: str, timeout_seconds: float = 5.0
    ) -> float | None:
        """Get current price asynchronously with timeout.

        Args:
            symbol: Stock symbol
            timeout_seconds: Timeout for price retrieval

        Returns:
            Current price or None if unavailable

        """
        try:
            # Try streaming first
            if self._streaming_service and self._streaming_service.is_connected():
                price = await asyncio.wait_for(
                    self._get_streaming_price_async(symbol), timeout=timeout_seconds
                )
                if price is not None:
                    return price

            # Fallback to REST API
            return await asyncio.get_event_loop().run_in_executor(
                None, self._market_data_client.get_current_price_from_quote, symbol
            )

        except TimeoutError:
            logging.warning(f"Timeout getting price for {symbol}")
            return None
        except Exception as e:
            logging.error(f"Error getting async price for {symbol}: {e}")
            return None

    async def _get_streaming_price_async(self, symbol: str) -> float | None:
        """Get price from streaming service asynchronously."""
        service = self._streaming_service
        if not service:
            return None
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, service.get_current_price, symbol)

    def get_current_price_with_callback(
        self,
        symbol: str,
        callback: Callable[[str, float | None], None],
        fallback_to_rest: bool = True,
    ) -> None:
        """Get current price and call callback when available.

        Args:
            symbol: Stock symbol
            callback: Callback function to call with (symbol, price)
            fallback_to_rest: Whether to use REST API as fallback

        """
        try:
            # Try streaming first
            if self._streaming_service and self._streaming_service.is_connected():
                price = self._streaming_service.get_current_price(symbol)
                if price is not None:
                    callback(symbol, price)
                    return

            # Fallback to REST API if enabled
            if fallback_to_rest:
                price = self._market_data_client.get_current_price_from_quote(symbol)
                callback(symbol, price)
            else:
                callback(symbol, None)

        except Exception as e:
            logging.error(f"Error getting callback price for {symbol}: {e}")
            callback(symbol, None)

    def subscribe_to_price_updates(
        self, symbol: str, callback: Callable[[str, float], None]
    ) -> str:
        """Subscribe to price updates for a symbol.

        Args:
            symbol: Stock symbol
            callback: Callback function for price updates

        Returns:
            Subscription ID for unsubscribing

        """
        if symbol not in self._price_callbacks:
            self._price_callbacks[symbol] = []
            # Subscribe to streaming service
            if self._streaming_service:
                self._streaming_service.subscribe_for_trading(symbol)

        self._price_callbacks[symbol].append(callback)
        subscription_id = f"{symbol}_{len(self._price_callbacks[symbol])}"

        logging.debug(f"Subscribed to price updates for {symbol}: {subscription_id}")
        return subscription_id

    def unsubscribe_from_price_updates(self, symbol: str, subscription_id: str) -> bool:
        """Unsubscribe from price updates.

        Args:
            symbol: Stock symbol
            subscription_id: Subscription ID returned from subscribe

        Returns:
            True if unsubscribed successfully

        """
        if symbol not in self._price_callbacks:
            return False

        # Remove callback by subscription ID (simplified implementation)
        callbacks_before = len(self._price_callbacks[symbol])
        # Note: In a real implementation, we'd map subscription_id to specific callbacks
        self._price_callbacks[symbol] = []

        if not self._price_callbacks[symbol]:
            del self._price_callbacks[symbol]

        logging.debug(f"Unsubscribed from price updates for {symbol}: {subscription_id}")
        return callbacks_before > len(self._price_callbacks.get(symbol, []))

    def get_multiple_prices_async(
        self, symbols: list[str], timeout_seconds: float = 10.0
    ) -> Awaitable[dict[str, float | None]]:
        """Get prices for multiple symbols concurrently.

        Args:
            symbols: List of stock symbols
            timeout_seconds: Timeout for all price retrievals

        Returns:
            Dictionary mapping symbols to prices

        """
        return self._fetch_multiple_prices(symbols, timeout_seconds)

    async def _fetch_multiple_prices(
        self, symbols: list[str], timeout_seconds: float
    ) -> dict[str, float | None]:
        """Internal method to fetch multiple prices concurrently."""
        tasks = [
            self.get_current_price_async(symbol, timeout_seconds / max(len(symbols), 1))
            for symbol in symbols
        ]

        try:
            prices = await asyncio.gather(*tasks, return_exceptions=True)
            result: dict[str, float | None] = {}

            for symbol, price in zip(symbols, prices, strict=True):
                if isinstance(price, BaseException):
                    logging.error(f"Error getting price for {symbol}: {price}")
                    result[symbol] = None
                else:
                    # price is float | None and result expects float | None
                    result[symbol] = price

            return result

        except Exception as e:
            logging.error(f"Error getting multiple prices: {e}")
            # Ensure keys exist with None values on error
            return dict.fromkeys(symbols, None)

    def get_price_with_fallback_chain(
        self, symbol: str, fallback_methods: list[str] | None = None
    ) -> float | None:
        """Get price using a chain of fallback methods.

        Args:
            symbol: Stock symbol
            fallback_methods: List of methods to try in order
                             ['streaming', 'quote', 'historical']

        Returns:
            Current price or None if all methods fail

        """
        if fallback_methods is None:
            fallback_methods = ["streaming", "quote", "historical"]

        for method in fallback_methods:
            try:
                if (
                    method == "streaming"
                    and self._streaming_service
                    and self._streaming_service.is_connected()
                ):
                    price = self._streaming_service.get_current_price(symbol)
                    if price is not None:
                        logging.debug(f"Got price for {symbol} via streaming: ${price:.2f}")
                        return price

                elif method == "quote":
                    price = self._market_data_client.get_current_price_from_quote(symbol)
                    if price is not None:
                        logging.debug(f"Got price for {symbol} via quote: ${price:.2f}")
                        return price

                elif method == "historical":
                    # Get latest close from recent historical data
                    df = self._market_data_client.get_historical_bars(symbol, "1d", "1d")
                    if not df.empty:
                        price = float(df["Close"].iloc[-1])
                        logging.debug(f"Got price for {symbol} via historical: ${price:.2f}")
                        return price

            except Exception as e:
                logging.debug(f"Method {method} failed for {symbol}: {e}")
                continue

        logging.warning(f"All fallback methods failed for {symbol}")
        return None

    def health_check(self) -> dict[str, Any]:
        """Check health of price fetching service.

        Returns:
            Health status dictionary

        """
        status: dict[str, Any] = {
            "streaming_connected": (
                self._streaming_service.is_connected() if self._streaming_service else False
            ),
            "rest_api_available": True,  # Assume available unless proven otherwise
            "active_subscriptions": len(self._price_callbacks),
            "rest_api_error": None,  # Will be set if there's an error
        }

        # Test REST API availability
        try:
            test_price = self._market_data_client.get_current_price_from_quote("AAPL")
            status["rest_api_available"] = test_price is not None
        except Exception as e:
            status["rest_api_available"] = False
            status["rest_api_error"] = str(e)

        return status
