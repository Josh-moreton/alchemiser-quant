"""Business Unit: execution | Status: current.

Quote acquisition and validation for smart execution strategy.

This module provides a unified interface for obtaining and validating market quotes,
handling both streaming and REST API fallback scenarios.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.types.market_data import QuoteModel

from .models import ExecutionConfig

logger = logging.getLogger(__name__)


class QuoteProvider:
    """Unified quote provider with streaming-first approach and REST fallback."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService | None = None,
        config: ExecutionConfig | None = None,
    ) -> None:
        """Initialize quote provider.

        Args:
            alpaca_manager: Alpaca broker manager for REST API fallback
            pricing_service: Real-time pricing service for streaming quotes
            config: Execution configuration for timeouts and validation

        """
        self.alpaca_manager = alpaca_manager
        self.pricing_service = pricing_service
        self.config = config or ExecutionConfig()

    def get_quote_with_validation(
        self, symbol: str, _order_size: float
    ) -> tuple[QuoteModel, bool] | None:
        """Get validated quote data from streaming source with REST API fallback.

        First attempts to get streaming quote data, then falls back to REST API
        if streaming data is not available - following Josh's guidance to use
        the same bid/ask data feed that strategy engines use.

        Args:
            symbol: Stock symbol
            _order_size: Size of order to place (in shares) - currently unused but reserved for future validation logic

        Returns:
            (QuoteModel, used_fallback) if valid quote available, otherwise None
            used_fallback is True if REST API was used instead of streaming

        """
        # Try streaming quote if pricing service available
        if self.pricing_service:
            # Wait for quote data to arrive from stream
            logger.info(f"⏳ Waiting for streaming quote data for {symbol}...")
            max_wait_time = 30.0  # Maximum 30 seconds to wait
            check_interval = 0.1  # Check every 100ms
            elapsed = 0.0

            quote = None
            while elapsed < max_wait_time:
                quote = self.pricing_service.get_quote_data(symbol)
                if quote:
                    logger.info(f"✅ Received streaming quote for {symbol} after {elapsed:.1f}s")
                    break

                time.sleep(check_interval)
                elapsed += check_interval

            if quote:
                # Check quote freshness
                quote_age = (datetime.now(UTC) - quote.timestamp).total_seconds()
                if quote_age <= self.config.quote_freshness_seconds:
                    # Simple price validation - ensure we have at least one valid price
                    if quote.bid_price > 0 or quote.ask_price > 0:
                        return quote, False  # Streaming quote success
                    logger.warning(
                        f"Invalid streaming prices for {symbol}: bid={quote.bid_price}, ask={quote.ask_price}"
                    )
                else:
                    logger.warning(
                        f"Streaming quote stale for {symbol} ({quote_age:.1f}s > {self.config.quote_freshness_seconds}s)"
                    )

        # Fallback to REST API using the same data feed as strategy engines
        logger.info(f"📊 Falling back to REST API quote data for {symbol}")
        rest_quote = self.alpaca_manager.get_latest_quote(symbol)

        if not rest_quote:
            logger.error(f"❌ No quote data available for {symbol} (streaming and REST failed)")
            return None

        bid_price, ask_price = rest_quote

        # Create QuoteModel from REST data for consistent processing
        quote = QuoteModel(
            symbol=symbol,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=0.0,  # REST API doesn't provide size data
            ask_size=0.0,  # REST API doesn't provide size data
            timestamp=datetime.now(UTC),
        )

        logger.info(f"✅ Got REST quote for {symbol}: bid=${bid_price:.2f}, ask=${ask_price:.2f}")

        return quote, True  # Used REST fallback

    def wait_for_quote_data(
        self, symbol: str, timeout: float | None = None
    ) -> dict[str, float | int] | None:
        """Wait for real-time quote data to be available.

        Args:
            symbol: Symbol to get quote for
            timeout: Maximum time to wait in seconds

        Returns:
            Quote data or None if timeout

        """
        timeout = timeout or self.config.max_wait_time_seconds
        start_time = time.time()

        # Return None if no pricing service available
        if self.pricing_service is None:
            logger.warning(f"⚠️ No pricing service available for {symbol}")
            return None

        # Initial quick check
        real_time_quote = self.pricing_service.get_real_time_quote(symbol)
        if real_time_quote:
            quote = {
                "bid_price": real_time_quote.bid,
                "ask_price": real_time_quote.ask,
                "bid_size": 0,  # Not available in RealTimeQuote
                "ask_size": 0,  # Not available in RealTimeQuote
                "timestamp": real_time_quote.timestamp.timestamp(),
            }
            logger.info(f"✅ Got immediate quote for {symbol}")
            return quote

        # Subscribe if not already subscribed
        if symbol not in self.pricing_service.get_subscribed_symbols():
            logger.info(f"📊 Subscribing to {symbol} for quote data")
            self.pricing_service.subscribe_for_order_placement(symbol)

            # Wait a bit for subscription to take effect
            time.sleep(1.0)  # Give stream time to restart if needed

        # Poll for quote data with exponential backoff
        check_interval = 0.1  # Start with 100ms
        max_interval = 1.0  # Cap at 1 second

        while time.time() - start_time < timeout:
            real_time_quote = self.pricing_service.get_real_time_quote(symbol)
            if real_time_quote:
                quote = {
                    "bid_price": real_time_quote.bid,
                    "ask_price": real_time_quote.ask,
                    "bid_size": 0,  # Not available in RealTimeQuote
                    "ask_size": 0,  # Not available in RealTimeQuote
                    "timestamp": real_time_quote.timestamp.timestamp(),
                }
                logger.info(f"✅ Got quote for {symbol} after {time.time() - start_time:.1f}s")
                return quote

            time.sleep(check_interval)
            # Exponential backoff to reduce CPU usage
            check_interval = min(check_interval * 1.5, max_interval)

        logger.warning(f"⏱️ Timeout waiting for quote data for {symbol} after {timeout}s")
        return None

    def validate_quote_liquidity(self, symbol: str, quote: dict[str, float | int]) -> bool:
        """Validate that the quote has sufficient liquidity.

        Args:
            symbol: Symbol being validated
            quote: Quote data to validate

        Returns:
            True if quote passes validation

        """
        try:
            # Handle both dict and Quote object formats
            if isinstance(quote, dict):
                bid_price = quote.get("bid_price", 0)
                ask_price = quote.get("ask_price", 0)
                bid_size = quote.get("bid_size", 0)
                ask_size = quote.get("ask_size", 0)
            else:
                bid_price = getattr(quote, "bid_price", 0)
                ask_price = getattr(quote, "ask_price", 0)
                bid_size = getattr(quote, "bid_size", 0)
                ask_size = getattr(quote, "ask_size", 0)

            # Basic price validation
            if bid_price <= 0 or ask_price <= 0:
                logger.warning(f"Invalid prices for {symbol}: bid={bid_price}, ask={ask_price}")
                return False

            # Spread validation (max 0.5% spread for liquidity)
            spread = (ask_price - bid_price) / ask_price
            max_spread = 0.005  # 0.5%
            if spread > max_spread:
                logger.warning(f"Spread too wide for {symbol}: {spread:.2%} > {max_spread:.2%}")
                return False

            # Size validation (ensure minimum liquidity)
            min_size = 100  # Minimum 100 shares at bid/ask
            if bid_size < min_size or ask_size < min_size:
                logger.warning(
                    f"Insufficient liquidity for {symbol}: "
                    f"bid_size={bid_size}, ask_size={ask_size} < {min_size}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating quote for {symbol}: {e}")
            return False

    def get_latest_quote(self, symbol: str) -> dict[str, float | int] | None:
        """Get the latest quote from the pricing service.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Quote data or None if not available

        """
        # Return None if no pricing service available
        if self.pricing_service is None:
            return None

        # Try to get structured quote data first
        quote_data = self.pricing_service.get_quote_data(symbol)
        if quote_data:
            # Convert to dict format for compatibility
            ts = quote_data.timestamp
            timestamp_value = ts.timestamp() if isinstance(ts, datetime) else float(ts)
            return {
                "bid_price": quote_data.bid_price,
                "ask_price": quote_data.ask_price,
                "bid_size": quote_data.bid_size,
                "ask_size": quote_data.ask_size,
                "timestamp": timestamp_value,
            }

        # Fallback to bid/ask spread
        spread = self.pricing_service.get_bid_ask_spread(symbol)
        if spread:
            bid, ask = spread
            return {
                "bid_price": bid,
                "ask_price": ask,
                "bid_size": 0,  # Unknown
                "ask_size": 0,  # Unknown
                "timestamp": datetime.now(UTC).timestamp(),
            }

        return None

    def cleanup_subscription(self, symbol: str) -> None:
        """Clean up subscription after order placement.

        Args:
            symbol: Symbol to unsubscribe from

        """
        if self.pricing_service:
            self.pricing_service.unsubscribe_after_order(symbol)
