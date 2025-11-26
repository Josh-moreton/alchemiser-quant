"""Streaming quote provider with REST fallback validation.

Business Unit: execution | Status: current.

This module supplies a minimal QuoteProvider implementation that:
- fetches streaming quotes from the pricing service
- validates suspicious prices using shared validation utilities
- falls back to REST NBBO quotes when streaming data looks unsafe

Note: the broader execution_v2 package already exposes a comprehensive
UnifiedQuoteService with streaming-first behavior, REST fallback, and
0-bid/ask handling. This provider now delegates to that service to avoid
duplicating logic while preserving the suspicious-price guard specific to
smart execution.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Tuple

from the_alchemiser.shared.types.market_data import QuoteModel
from the_alchemiser.shared.utils.validation_utils import detect_suspicious_quote_prices

from ...unified.quote_service import QuoteResult, QuoteSource, UnifiedQuoteService

from .models import ExecutionConfig


class QuoteProvider:
    """Provide streaming quotes with safety checks and REST fallback."""

    def __init__(
        self,
        alpaca_manager: Any,
        pricing_service: Any,
        config: ExecutionConfig,
        *,
        quote_service: UnifiedQuoteService | None = None,
        use_unified_service: bool = True,
    ) -> None:
        self.alpaca_manager = alpaca_manager
        self.pricing_service = pricing_service
        self.config = config
        self.quote_service = quote_service
        if use_unified_service:
            self.quote_service = quote_service or UnifiedQuoteService(
                alpaca_manager,
                pricing_service,
                streaming_timeout_ms=config.quote_wait_milliseconds,
                quote_freshness_seconds=float(config.quote_freshness_seconds),
            )

    def get_quote_with_validation(
        self, symbol: str
    ) -> Optional[Tuple[QuoteModel, bool]]:
        """Return a validated quote and whether REST fallback was used.

        Args:
            symbol: Trading symbol.

        Returns:
            Tuple of (QuoteModel, used_rest_fallback) or ``None`` if no quote.
        """

        result = asyncio.run(self.get_quote_with_validation_async(symbol))
        if result is None:
            return None

        return result

    async def get_quote_with_validation_async(
        self, symbol: str
    ) -> Optional[Tuple[QuoteModel, bool]]:
        """Async variant for callers already in an event loop."""

        result = await self._get_best_quote(symbol)
        if result is None or not result.success:
            return None

        if result.source == QuoteSource.STREAMING and self._is_streaming_quote_suspicious(
            result, symbol
        ):
            rest_quote = self._validate_suspicious_quote_with_rest(result, symbol)
            if rest_quote is None:
                return None
            return rest_quote, True

        return self._to_quote_model(result), result.source == QuoteSource.REST

    async def _get_best_quote(self, symbol: str) -> QuoteResult | None:
        """Fetch the best quote using the shared unified quote service."""

        if self.quote_service is not None:
            return await self.quote_service.get_best_quote(symbol)

        streaming_quote = self._try_streaming_quote(symbol)
        if streaming_quote is None:
            return None

        return self._to_quote_result(streaming_quote)

    def _try_streaming_quote(self, symbol: str) -> Optional[QuoteModel]:
        """Fetch a streaming quote via the pricing service."""

        if hasattr(self.pricing_service, "get_quote"):
            return self.pricing_service.get_quote(symbol)
        return None

    def _is_streaming_quote_suspicious(
        self, quote: QuoteModel | QuoteResult, symbol: str
    ) -> bool:
        """Detect suspicious streaming prices using shared validation."""

        bid = getattr(quote, "bid_price", None)
        if bid is None:
            bid = getattr(quote, "bid")

        ask = getattr(quote, "ask_price", None)
        if ask is None:
            ask = getattr(quote, "ask")

        is_suspicious, _ = detect_suspicious_quote_prices(
            bid_price=bid, ask_price=ask
        )
        return is_suspicious

    def _validate_suspicious_quote_with_rest(
        self, streaming_quote: QuoteModel | QuoteResult, symbol: str
    ) -> Optional[QuoteModel]:
        """Validate suspicious streaming data by fetching REST NBBO."""

        rest_quote = self.alpaca_manager.get_latest_quote(symbol)
        if rest_quote is None:
            return None

        return QuoteModel(
            symbol=symbol,
            bid_price=Decimal(str(rest_quote.bid)),
            ask_price=Decimal(str(rest_quote.ask)),
            bid_size=self._to_decimal_safe(getattr(rest_quote, "bid_size", 0)),
            ask_size=self._to_decimal_safe(getattr(rest_quote, "ask_size", 0)),
            timestamp=streaming_quote.timestamp,
        )

    @staticmethod
    def _to_quote_result(streaming_quote: QuoteModel) -> QuoteResult:
        """Convert a streaming QuoteModel into a QuoteResult for validation."""

        return QuoteResult(
            symbol=streaming_quote.symbol,
            bid=Decimal(streaming_quote.bid_price),
            ask=Decimal(streaming_quote.ask_price),
            mid=(Decimal(streaming_quote.bid_price) + Decimal(streaming_quote.ask_price))
            / Decimal("2"),
            source=QuoteSource.STREAMING,
            timestamp=streaming_quote.timestamp,
            is_stale=False,
            had_zero_bid=False,
            had_zero_ask=False,
            success=True,
            error_message=None,
        )

    @staticmethod
    def _to_quote_model(result: QuoteResult) -> QuoteModel:
        """Convert a QuoteResult to the shared QuoteModel type."""

        return QuoteModel(
            symbol=result.symbol,
            bid_price=result.bid,
            ask_price=result.ask,
            bid_size=Decimal(0),
            ask_size=Decimal(0),
            timestamp=result.timestamp,
        )

    @staticmethod
    def _to_decimal_safe(value: Any) -> Decimal:
        """Convert arbitrary values to Decimal with a safe default."""

        try:
            return Decimal(value)
        except (TypeError, InvalidOperation):
            return Decimal(0)
