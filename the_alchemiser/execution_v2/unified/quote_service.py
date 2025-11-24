"""Business Unit: execution | Status: current.

Unified quote service with streaming-first approach and explicit 0-handling.

This service provides a single source of truth for market quotes with:
- Streaming WebSocket quotes as primary source (lowest latency)
- REST API fallback for reliability
- Explicit handling of 0 bids/asks (common Alpaca issue)
- Clear metrics and logging for observability
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
    from the_alchemiser.shared.types.market_data import QuoteModel

logger = get_logger(__name__)

# Module-level configuration
DEFAULT_STREAMING_TIMEOUT_MS = 5000
DEFAULT_QUOTE_FRESHNESS_SECONDS = 10.0
MINIMUM_VALID_PRICE = Decimal("0.01")


class QuoteSource(str, Enum):
    """Source of the quote data."""

    STREAMING = "streaming"  # WebSocket real-time data
    REST = "rest"  # REST API fallback
    UNAVAILABLE = "unavailable"  # No usable quote available


@dataclass(frozen=True)
class QuoteResult:
    """Result of quote acquisition with full metadata.

    Attributes:
        symbol: Stock symbol
        bid: Bid price (may be derived from ask if original bid was 0)
        ask: Ask price (may be derived from bid if original ask was 0)
        mid: Mid-market price
        source: Where the quote came from
        timestamp: When the quote was generated
        is_stale: Whether the quote is considered stale
        had_zero_bid: True if original bid was 0 and was substituted
        had_zero_ask: True if original ask was 0 and was substituted
        success: True if a usable quote was obtained

    """

    symbol: str
    bid: Decimal
    ask: Decimal
    mid: Decimal
    source: QuoteSource
    timestamp: datetime
    is_stale: bool
    had_zero_bid: bool
    had_zero_ask: bool
    success: bool
    error_message: str | None = None

    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread."""
        return self.ask - self.bid

    @property
    def spread_percent(self) -> float:
        """Calculate spread as percentage of mid price."""
        if self.mid > 0:
            return float(self.spread / self.mid * 100)
        return 0.0


class QuoteMetrics:
    """Metrics tracker for quote service observability."""

    def __init__(self) -> None:
        """Initialize metrics counters."""
        self.streaming_success_count = 0
        self.rest_fallback_count = 0
        self.no_usable_quote_count = 0
        self.zero_bid_count = 0
        self.zero_ask_count = 0
        self.both_zero_count = 0
        self.stale_quote_count = 0

    def log_summary(self) -> None:
        """Log current metrics summary."""
        total = self.streaming_success_count + self.rest_fallback_count + self.no_usable_quote_count
        if total == 0:
            return

        logger.info(
            "Quote service metrics summary",
            total_requests=total,
            streaming_success=self.streaming_success_count,
            streaming_success_rate=f"{self.streaming_success_count / total * 100:.1f}%",
            rest_fallback=self.rest_fallback_count,
            rest_fallback_rate=f"{self.rest_fallback_count / total * 100:.1f}%",
            failures=self.no_usable_quote_count,
            failure_rate=f"{self.no_usable_quote_count / total * 100:.1f}%",
            zero_issues={
                "zero_bid": self.zero_bid_count,
                "zero_ask": self.zero_ask_count,
                "both_zero": self.both_zero_count,
            },
            stale_quotes=self.stale_quote_count,
        )


class UnifiedQuoteService:
    """Single source of truth for market quotes.

    This service implements a streaming-first approach with REST fallback
    and explicit handling of Alpaca's 0 bid/ask issues.

    Flow:
        1. Try streaming quote (WebSocket) with configurable timeout
        2. Check for 0 bids/asks and handle explicitly:
           - If bid=0 and ask>0: use ask for both (with warning)
           - If ask=0 and bid>0: use bid for both (with warning)
           - If both=0: treat as unusable, try REST fallback
        3. Check quote freshness (not stale)
        4. If streaming fails/unusable: fall back to REST API
        5. Return QuoteResult with full metadata for audit trail

    Thread Safety:
        This class is not thread-safe. Callers should synchronize access
        if used from multiple threads.

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService | None = None,
        *,
        streaming_timeout_ms: int = DEFAULT_STREAMING_TIMEOUT_MS,
        quote_freshness_seconds: float = DEFAULT_QUOTE_FRESHNESS_SECONDS,
    ) -> None:
        """Initialize unified quote service.

        Args:
            alpaca_manager: Alpaca broker manager for REST API fallback
            pricing_service: Real-time pricing service for streaming quotes (optional)
            streaming_timeout_ms: Max time to wait for streaming quote
            quote_freshness_seconds: Max age for quote to be considered fresh

        """
        self.alpaca_manager = alpaca_manager
        self.pricing_service = pricing_service
        self.streaming_timeout_ms = streaming_timeout_ms
        self.quote_freshness_seconds = quote_freshness_seconds
        self.metrics = QuoteMetrics()

        logger.debug(
            "UnifiedQuoteService initialized",
            has_streaming=pricing_service is not None,
            streaming_timeout_ms=streaming_timeout_ms,
            quote_freshness_seconds=quote_freshness_seconds,
        )

    async def get_best_quote(
        self, symbol: str, *, correlation_id: str | None = None
    ) -> QuoteResult:
        """Get best available quote with streaming-first approach.

        Args:
            symbol: Stock symbol to get quote for
            correlation_id: Optional correlation ID for tracing

        Returns:
            QuoteResult with quote data and metadata

        """
        log_extra = {"symbol": symbol, "correlation_id": correlation_id}

        # Step 1: Try streaming quote first
        streaming_result = await self._try_streaming_quote(symbol, correlation_id=correlation_id)
        if streaming_result.success:
            self.metrics.streaming_success_count += 1
            logger.info(
                "Got usable streaming quote",
                **log_extra,
                bid=streaming_result.bid,
                ask=streaming_result.ask,
                source=streaming_result.source.value,
            )
            return streaming_result

        # Step 2: Fall back to REST API
        logger.warning("Streaming quote failed, falling back to REST", **log_extra)
        self.metrics.rest_fallback_count += 1

        rest_result = self._try_rest_quote(symbol, correlation_id=correlation_id)
        if rest_result.success:
            logger.info(
                "Got usable REST quote",
                **log_extra,
                bid=rest_result.bid,
                ask=rest_result.ask,
                source=rest_result.source.value,
            )
            return rest_result

        # Step 3: No usable quote available
        self.metrics.no_usable_quote_count += 1
        logger.error("No usable quote available from any source", **log_extra)

        return QuoteResult(
            symbol=symbol,
            bid=Decimal("0"),
            ask=Decimal("0"),
            mid=Decimal("0"),
            source=QuoteSource.UNAVAILABLE,
            timestamp=datetime.now(UTC),
            is_stale=True,
            had_zero_bid=False,
            had_zero_ask=False,
            success=False,
            error_message=f"No usable quote available for {symbol}",
        )

    async def _try_streaming_quote(
        self, symbol: str, *, correlation_id: str | None = None
    ) -> QuoteResult:
        """Try to get a valid streaming quote.

        Args:
            symbol: Stock symbol
            correlation_id: Optional correlation ID for tracing

        Returns:
            QuoteResult (success=False if failed)

        """
        if not self.pricing_service:
            return self._create_unavailable_result(
                symbol, "No streaming service available", correlation_id=correlation_id
            )

        # Wait for streaming quote with timeout
        quote = await self._wait_for_streaming_quote(symbol, correlation_id=correlation_id)
        if not quote:
            return self._create_unavailable_result(
                symbol, "Streaming quote timeout", correlation_id=correlation_id
            )

        # Check freshness
        age_seconds = (datetime.now(UTC) - quote.timestamp).total_seconds()
        is_stale = age_seconds > self.quote_freshness_seconds

        if is_stale:
            self.metrics.stale_quote_count += 1
            logger.warning(
                "Streaming quote is stale",
                symbol=symbol,
                age_seconds=age_seconds,
                max_age=self.quote_freshness_seconds,
                correlation_id=correlation_id,
            )
            return self._create_unavailable_result(
                symbol,
                f"Streaming quote too stale ({age_seconds:.1f}s)",
                correlation_id=correlation_id,
            )

        # Handle 0 bids/asks explicitly
        return self._handle_zero_prices(quote, QuoteSource.STREAMING, correlation_id=correlation_id)

    async def _wait_for_streaming_quote(
        self, symbol: str, *, correlation_id: str | None = None
    ) -> QuoteModel | None:
        """Wait for streaming quote to arrive.

        Args:
            symbol: Stock symbol
            correlation_id: Optional correlation ID for tracing

        Returns:
            QuoteModel if received, None if timeout

        """
        if not self.pricing_service:
            return None

        timeout_seconds = self.streaming_timeout_ms / 1000.0
        check_interval = 0.1  # Check every 100ms
        elapsed = 0.0

        while elapsed < timeout_seconds:
            quote = self.pricing_service.get_quote_data(symbol)
            if quote:
                logger.debug(
                    "Received streaming quote",
                    symbol=symbol,
                    elapsed_seconds=elapsed,
                    correlation_id=correlation_id,
                )
                return quote

            await asyncio.sleep(check_interval)
            elapsed += check_interval

        logger.debug(
            "Streaming quote timeout",
            symbol=symbol,
            timeout_seconds=timeout_seconds,
            correlation_id=correlation_id,
        )
        return None

    def _try_rest_quote(self, symbol: str, *, correlation_id: str | None = None) -> QuoteResult:
        """Try to get a valid REST quote.

        Args:
            symbol: Stock symbol
            correlation_id: Optional correlation ID for tracing

        Returns:
            QuoteResult (success=False if failed)

        """
        try:
            quote = self.alpaca_manager.get_latest_quote(symbol)
            if not quote:
                return self._create_unavailable_result(
                    symbol, "REST API returned no quote", correlation_id=correlation_id
                )

            # REST quotes are assumed fresh (just fetched)
            return self._handle_zero_prices(quote, QuoteSource.REST, correlation_id=correlation_id)

        except Exception as e:
            logger.error(
                "REST quote fetch failed",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return self._create_unavailable_result(
                symbol, f"REST API error: {e}", correlation_id=correlation_id
            )

    def _handle_zero_prices(
        self,
        quote: QuoteModel,
        source: QuoteSource,
        *,
        correlation_id: str | None = None,
    ) -> QuoteResult:
        """Handle quotes with 0 bid or ask prices (common Alpaca issue).

        Strategy:
            - If bid=0 and ask>0: use ask for both sides (conservative)
            - If ask=0 and bid>0: use bid for both sides (conservative)
            - If both=0: unusable quote

        Args:
            quote: Quote model with potentially 0 prices
            source: Source of the quote
            correlation_id: Optional correlation ID for tracing

        Returns:
            QuoteResult with handled 0 prices

        """
        original_bid = quote.bid_price
        original_ask = quote.ask_price
        had_zero_bid = original_bid <= 0
        had_zero_ask = original_ask <= 0

        # Case 1: Both are 0 or invalid - unusable
        if had_zero_bid and had_zero_ask:
            self.metrics.both_zero_count += 1
            logger.warning(
                "Quote has both bid and ask at 0 - unusable",
                symbol=quote.symbol,
                source=source.value,
                correlation_id=correlation_id,
            )
            return self._create_unavailable_result(
                quote.symbol, "Both bid and ask are 0", correlation_id=correlation_id
            )

        # Case 2: Bid is 0, use ask
        if had_zero_bid and not had_zero_ask:
            self.metrics.zero_bid_count += 1
            final_bid = original_ask
            final_ask = original_ask
            logger.warning(
                "Quote has 0 bid - using ask for both sides",
                symbol=quote.symbol,
                source=source.value,
                original_ask=original_ask,
                correlation_id=correlation_id,
            )

        # Case 3: Ask is 0, use bid
        elif had_zero_ask and not had_zero_bid:
            self.metrics.zero_ask_count += 1
            final_bid = original_bid
            final_ask = original_bid
            logger.warning(
                "Quote has 0 ask - using bid for both sides",
                symbol=quote.symbol,
                source=source.value,
                original_bid=original_bid,
                correlation_id=correlation_id,
            )

        # Case 4: Both are valid
        else:
            final_bid = original_bid
            final_ask = original_ask

        # Ensure prices are Decimal
        bid = Decimal(str(final_bid))
        ask = Decimal(str(final_ask))
        mid = (bid + ask) / Decimal("2")

        # Validate final prices are reasonable
        if bid < MINIMUM_VALID_PRICE or ask < MINIMUM_VALID_PRICE:
            logger.error(
                "Final quote prices below minimum",
                symbol=quote.symbol,
                bid=bid,
                ask=ask,
                min_price=MINIMUM_VALID_PRICE,
                correlation_id=correlation_id,
            )
            return self._create_unavailable_result(
                quote.symbol,
                f"Prices below minimum ({MINIMUM_VALID_PRICE})",
                correlation_id=correlation_id,
            )

        return QuoteResult(
            symbol=quote.symbol,
            bid=bid,
            ask=ask,
            mid=mid,
            source=source,
            timestamp=quote.timestamp,
            is_stale=False,
            had_zero_bid=had_zero_bid,
            had_zero_ask=had_zero_ask,
            success=True,
            error_message=None,
        )

    def _create_unavailable_result(
        self,
        symbol: str,
        reason: str,
        *,
        correlation_id: str | None = None,
    ) -> QuoteResult:
        """Create a result indicating quote is unavailable.

        Args:
            symbol: Stock symbol
            reason: Why the quote is unavailable
            correlation_id: Optional correlation ID for tracing

        Returns:
            QuoteResult with success=False

        """
        return QuoteResult(
            symbol=symbol,
            bid=Decimal("0"),
            ask=Decimal("0"),
            mid=Decimal("0"),
            source=QuoteSource.UNAVAILABLE,
            timestamp=datetime.now(UTC),
            is_stale=True,
            had_zero_bid=False,
            had_zero_ask=False,
            success=False,
            error_message=reason,
        )

    def log_metrics_summary(self) -> None:
        """Log metrics summary for observability."""
        self.metrics.log_summary()
