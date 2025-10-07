"""Business Unit: execution | Status: current.

Quote acquisition and validation for smart execution strategy.

This module provides a unified interface for obtaining and validating market quotes,
handling both streaming and REST API fallback scenarios.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.types.market_data import QuoteModel

from .models import ExecutionConfig

logger = get_logger(__name__)


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

    def get_quote_with_validation(self, symbol: str) -> tuple[QuoteModel, bool] | None:
        """Get validated quote data from streaming source with REST API fallback.

        First attempts to get streaming quote data, then falls back to REST API
        if streaming data is not available - following Josh's guidance to use
        the same bid/ask data feed that strategy engines use.

        Args:
            symbol: Stock symbol

        Returns:
            (QuoteModel, used_fallback) if valid quote available, otherwise None
            used_fallback is True if REST API was used instead of streaming

        """
        # Try streaming quote first if available
        streaming_quote = self._try_streaming_quote(symbol)
        if streaming_quote:
            # Check if streaming quote looks suspicious - if so, validate with REST
            if self._is_streaming_quote_suspicious(streaming_quote, symbol):
                logger.warning(
                    f"🚨 Suspicious streaming prices for {symbol}, validating with REST NBBO"
                )
                rest_result = self._validate_suspicious_quote_with_rest(
                    streaming_quote, symbol
                )
                if rest_result:
                    return rest_result
                # If REST validation fails, continue with streaming quote as fallback
                logger.warning(
                    f"⚠️ REST validation failed for {symbol}, using streaming quote despite suspicion"
                )
            return streaming_quote, False

        # Fallback to REST API
        return self._try_rest_fallback_quote(symbol)

    def _try_streaming_quote(self, symbol: str) -> QuoteModel | None:
        """Try to get a valid streaming quote.

        Args:
            symbol: Stock symbol

        Returns:
            QuoteModel if successful, None otherwise

        """
        if not self.pricing_service:
            return None

        logger.info(f"⏳ Waiting for streaming quote data for {symbol}...")
        quote = self._wait_for_streaming_quote(symbol)

        if not quote:
            return None

        # Validate quote freshness and prices
        if self._is_streaming_quote_valid(quote, symbol):
            logger.info(f"✅ Received valid streaming quote for {symbol}")
            return quote

        return None

    def _wait_for_streaming_quote(self, symbol: str) -> QuoteModel | None:
        """Wait for streaming quote data to arrive.

        Args:
            symbol: Stock symbol

        Returns:
            QuoteModel if received, None if timeout

        """
        if not self.pricing_service:
            return None

        max_wait_time = 30.0  # Maximum 30 seconds to wait
        check_interval = 0.1  # Check every 100ms
        elapsed = 0.0

        while elapsed < max_wait_time:
            quote = self.pricing_service.get_quote_data(symbol)
            if quote:
                logger.info(
                    f"✅ Received streaming quote for {symbol} after {elapsed:.1f}s"
                )
                return quote

            time.sleep(check_interval)
            elapsed += check_interval

        return None

    def _is_streaming_quote_valid(self, quote: QuoteModel, symbol: str) -> bool:
        """Check if streaming quote is fresh and has valid prices.

        Args:
            quote: Quote to validate
            symbol: Stock symbol for logging

        Returns:
            True if quote is valid

        """
        from the_alchemiser.shared.utils.validation_utils import (
            validate_quote_freshness,
            validate_quote_prices,
        )

        # Check quote freshness
        if not validate_quote_freshness(
            quote.timestamp, self.config.quote_freshness_seconds
        ):
            quote_age = (datetime.now(UTC) - quote.timestamp).total_seconds()
            logger.debug(
                f"Streaming quote stale for {symbol} ({quote_age:.1f}s > {self.config.quote_freshness_seconds}s)"
            )
            return False

        # Simple price validation - ensure we have at least one valid price
        if not validate_quote_prices(quote.bid_price, quote.ask_price):
            logger.warning(
                f"Invalid streaming prices for {symbol}: bid={quote.bid_price}, ask={quote.ask_price}"
            )
            return False

        return True

    def _is_streaming_quote_suspicious(self, quote: QuoteModel, symbol: str) -> bool:
        """Check if streaming quote prices look suspicious and warrant REST validation.

        Detects anomalies like:
        - Negative prices
        - Inverted spreads (ask < bid)
        - Unreasonably low prices (penny stock filter)
        - Excessive spreads indicating stale data

        Args:
            quote: Quote to check for suspicious patterns
            symbol: Stock symbol for logging

        Returns:
            True if quote looks suspicious and should be validated with REST

        """
        from the_alchemiser.shared.utils.validation_utils import (
            detect_suspicious_quote_prices,
        )

        is_suspicious, reasons = detect_suspicious_quote_prices(
            quote.bid_price,
            quote.ask_price,
            min_price=0.01,  # We don't trade penny stocks
            max_spread_percent=10.0,  # 10% spread is excessive for most stocks
        )

        if is_suspicious:
            reasons_str = "; ".join(reasons)
            logger.warning(
                f"🚨 Suspicious streaming quote detected for {symbol}: {reasons_str} "
                f"(bid={quote.bid_price}, ask={quote.ask_price})"
            )

        return is_suspicious

    def _validate_suspicious_quote_with_rest(
        self, streaming_quote: QuoteModel, symbol: str
    ) -> tuple[QuoteModel, bool] | None:
        """Validate suspicious streaming quote by fetching REST NBBO and recomputing if needed.

        Args:
            streaming_quote: The suspicious streaming quote
            symbol: Stock symbol

        Returns:
            (corrected_quote, True) if REST validation provides better data, None if REST fails

        """
        logger.info(
            f"📊 Fetching REST NBBO to validate suspicious streaming prices for {symbol}"
        )

        rest_result = self._try_rest_fallback_quote(symbol)
        if not rest_result:
            logger.error(
                f"❌ REST NBBO fetch failed for {symbol} during suspicious quote validation"
            )
            return None

        rest_quote, _ = rest_result

        # Check if REST quote is reasonable compared to streaming
        rest_suspicious, rest_reasons = self._check_quote_suspicious_patterns(
            rest_quote
        )

        if rest_suspicious:
            logger.warning(
                f"⚠️ REST quote also suspicious for {symbol}: {'; '.join(rest_reasons)} - "
                f"using streaming quote as lesser evil"
            )
            return None

        # REST quote looks reasonable - compare with streaming to decide
        streaming_mid = (streaming_quote.bid_price + streaming_quote.ask_price) / 2
        rest_mid = (rest_quote.bid_price + rest_quote.ask_price) / 2

        # If REST mid-price is significantly different, prefer REST
        if (
            streaming_mid <= 0 or abs(rest_mid - streaming_mid) / rest_mid > 0.1
        ):  # 10% difference threshold
            logger.info(
                f"✅ Using REST quote for {symbol}: mid=${rest_mid:.2f} vs streaming=${streaming_mid:.2f} "
                f"(REST provides more reasonable pricing)"
            )
            return rest_quote, True

        # If both are similar and REST isn't suspicious, prefer REST for safety
        logger.info(
            f"✅ Using REST quote for {symbol} as validation passed (mid=${rest_mid:.2f})"
        )
        return rest_quote, True

    def _check_quote_suspicious_patterns(
        self, quote: QuoteModel
    ) -> tuple[bool, list[str]]:
        """Check quote for suspicious patterns without logging.

        Args:
            quote: Quote to check

        Returns:
            Tuple of (is_suspicious, list_of_reasons)

        """
        from the_alchemiser.shared.utils.validation_utils import (
            detect_suspicious_quote_prices,
        )

        return detect_suspicious_quote_prices(
            quote.bid_price, quote.ask_price, min_price=0.01, max_spread_percent=10.0
        )

    def _try_rest_fallback_quote(self, symbol: str) -> tuple[QuoteModel, bool] | None:
        """Try to get quote using REST API fallback.

        Args:
            symbol: Stock symbol

        Returns:
            (QuoteModel, True) if successful, None if failed

        """
        logger.info(f"📊 Falling back to REST API quote data for {symbol}")
        rest_quote = self.alpaca_manager.get_latest_quote(symbol)

        if not rest_quote:
            logger.error(
                f"❌ No quote data available for {symbol} (streaming and REST failed)"
            )
            return None

        # Extract bid/ask from QuoteModel
        bid_price = Decimal(str(rest_quote.bid))
        ask_price = Decimal(str(rest_quote.ask))

        # Create enhanced QuoteModel from REST data for consistent processing
        quote = QuoteModel(
            symbol=symbol,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=Decimal("0.0"),  # REST API doesn't provide size data
            ask_size=Decimal("0.0"),  # REST API doesn't provide size data
            timestamp=datetime.now(UTC),
        )

        logger.info(
            f"✅ Got REST quote for {symbol}: bid=${bid_price:.2f}, ask=${ask_price:.2f}"
        )
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
                logger.info(
                    f"✅ Got quote for {symbol} after {time.time() - start_time:.1f}s"
                )
                return quote

            time.sleep(check_interval)
            # Exponential backoff to reduce CPU usage
            check_interval = min(check_interval * 1.5, max_interval)

        logger.warning(
            f"⏱️ Timeout waiting for quote data for {symbol} after {timeout}s"
        )
        return None

    def validate_quote_liquidity(
        self, symbol: str, quote: dict[str, float | int]
    ) -> bool:
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
                logger.warning(
                    f"Invalid prices for {symbol}: bid={bid_price}, ask={ask_price}"
                )
                return False

            # Spread validation (max 0.5% spread for liquidity)
            spread = (ask_price - bid_price) / ask_price
            max_spread = 0.005  # 0.5%
            if spread > max_spread:
                logger.warning(
                    f"Spread too wide for {symbol}: {spread:.2%} > {max_spread:.2%}"
                )
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
            # Convert to dict format for compatibility (convert Decimal to float for JSON/logging)
            ts = quote_data.timestamp
            timestamp_value = ts.timestamp() if isinstance(ts, datetime) else float(ts)
            return {
                "bid_price": float(quote_data.bid_price),
                "ask_price": float(quote_data.ask_price),
                "bid_size": float(quote_data.bid_size),
                "ask_size": float(quote_data.ask_size),
                "timestamp": timestamp_value,
            }

        # Fallback to bid/ask spread
        spread = self.pricing_service.get_bid_ask_spread(symbol)
        if spread:
            bid, ask = spread
            return {
                "bid_price": float(bid),
                "ask_price": float(ask),
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
