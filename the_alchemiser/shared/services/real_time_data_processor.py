"""Business Unit: shared | Status: current.

Real-time data processing for market data streams.

This module handles extraction, validation, and processing of incoming
quote and trade data from Alpaca WebSocket streams.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import QuoteExtractionResult

if TYPE_CHECKING:
    from alpaca.data.models import Quote, Trade

    AlpacaQuoteData = dict[str, str | float | int] | Quote
    AlpacaTradeData = dict[str, str | float | int] | Trade
else:
    AlpacaQuoteData = dict[str, str | float | int] | object
    AlpacaTradeData = dict[str, str | float | int] | object


class RealTimeDataProcessor:
    """Processes and extracts data from real-time market data streams."""

    def __init__(self) -> None:
        """Initialize the data processor."""
        self.logger = get_logger(__name__)

    def extract_symbol_from_quote(self, data: AlpacaQuoteData) -> str:
        """Extract symbol from quote data.

        Args:
            data: Quote data from Alpaca WebSocket

        Returns:
            Symbol string or empty string if not found

        """
        if hasattr(data, "symbol"):
            return str(data.symbol)
        return str(data.get("S", "")) if isinstance(data, dict) else ""

    def extract_quote_values(self, data: AlpacaQuoteData) -> QuoteExtractionResult:
        """Extract bid/ask data from quote.

        Args:
            data: Quote data from Alpaca WebSocket

        Returns:
            QuoteExtractionResult with extracted values

        """
        if isinstance(data, dict):
            return QuoteExtractionResult(
                bid_price=self._safe_float_convert(data.get("bp")),
                ask_price=self._safe_float_convert(data.get("ap")),
                bid_size=self._safe_float_convert(data.get("bs")),
                ask_size=self._safe_float_convert(data.get("as")),
                timestamp_raw=self._safe_datetime_convert(data.get("t")),
            )

        return QuoteExtractionResult(
            bid_price=self._safe_float_convert(getattr(data, "bid_price", None)),
            ask_price=self._safe_float_convert(getattr(data, "ask_price", None)),
            bid_size=self._safe_float_convert(getattr(data, "bid_size", None)),
            ask_size=self._safe_float_convert(getattr(data, "ask_size", None)),
            timestamp_raw=self._safe_datetime_convert(getattr(data, "timestamp", None)),
        )

    def extract_symbol_from_trade(self, data: AlpacaTradeData) -> str:
        """Extract symbol from trade data.

        Args:
            data: Trade data from Alpaca WebSocket

        Returns:
            Symbol string or empty string if not found

        """
        if hasattr(data, "symbol"):
            return str(data.symbol)
        return str(data.get("symbol", "")) if isinstance(data, dict) else ""

    def extract_trade_values(
        self, trade: AlpacaTradeData
    ) -> tuple[float, int | float | None, datetime]:
        """Extract price, volume, and timestamp from trade data.

        Args:
            trade: Trade data from Alpaca WebSocket

        Returns:
            Tuple of (price, volume, timestamp)

        """
        if isinstance(trade, dict):
            price = trade.get("price", 0)
            size = trade.get("size", 0)
            volume = trade.get("volume", size)
            timestamp_raw = trade.get("timestamp", datetime.now(UTC))
        else:
            price = trade.price
            size = trade.size
            volume = getattr(trade, "volume", size)
            timestamp_raw = trade.timestamp

        timestamp = self.get_trade_timestamp(timestamp_raw)
        # Convert volume to proper type
        volume_typed: int | float | None = None
        if volume is not None:
            try:
                volume_typed = (
                    float(volume) if isinstance(volume, (str, int, float)) else None
                )
            except (ValueError, TypeError):
                volume_typed = None

        return float(price), volume_typed, timestamp

    def get_quote_timestamp(self, timestamp_raw: datetime | None) -> datetime:
        """Ensure timestamp is a datetime for quotes.

        Args:
            timestamp_raw: Raw timestamp value

        Returns:
            Valid datetime object

        """
        return (
            timestamp_raw if isinstance(timestamp_raw, datetime) else datetime.now(UTC)
        )

    def get_trade_timestamp(
        self, timestamp_raw: datetime | str | float | int | None
    ) -> datetime:
        """Ensure timestamp is a datetime for trades.

        Args:
            timestamp_raw: Raw timestamp value

        Returns:
            Valid datetime object

        """
        if isinstance(timestamp_raw, datetime):
            return timestamp_raw
        return datetime.now(UTC)

    def _safe_float_convert(self, value: str | float | int | None) -> float | None:
        """Safely convert value to float.

        Args:
            value: Value to convert

        Returns:
            Float value or None if conversion fails

        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_datetime_convert(
        self, value: str | float | int | datetime | None
    ) -> datetime | None:
        """Safely convert value to datetime.

        Args:
            value: Value to convert

        Returns:
            Datetime value or None if not a datetime

        """
        if isinstance(value, datetime):
            return value
        return None

    async def log_quote_debug(
        self, symbol: str, bid_price: float | None, ask_price: float | None
    ) -> None:
        """Log quote data asynchronously for debugging.

        Args:
            symbol: Stock symbol
            bid_price: Bid price
            ask_price: Ask price

        """
        if self.logger.isEnabledFor(logging.DEBUG):
            with contextlib.suppress(RuntimeError):
                # Event loop executor has shut down - gracefully ignore
                await asyncio.to_thread(
                    self.logger.debug,
                    f"📊 Quote received for {symbol}: bid={bid_price}, ask={ask_price}",
                )
        await asyncio.sleep(0)

    async def handle_quote_error(self, error: Exception) -> None:
        """Handle errors in quote processing.

        Args:
            error: Exception that occurred

        """
        with contextlib.suppress(RuntimeError):
            # Event loop executor has shut down - gracefully ignore
            await asyncio.to_thread(
                self.logger.error, f"Error processing quote: {error}", exc_info=True
            )
        await asyncio.sleep(0)
