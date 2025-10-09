"""Business Unit: shared | Status: current.

Real-time data processing for market data streams.

This module handles extraction, validation, and processing of incoming
quote and trade data from Alpaca WebSocket streams.

All financial data (prices, sizes) uses Decimal for precision per Alchemiser guardrails.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import DataProviderError
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
    """Processes and extracts data from real-time market data streams.

    Handles extraction, validation, and conversion of real-time quote and trade data
    from Alpaca WebSocket streams. All financial data uses Decimal for precision.

    Attributes:
        logger: Structured logger instance for observability

    Examples:
        >>> processor = RealTimeDataProcessor()
        >>> quote_data = {"S": "AAPL", "bp": 150.25, "ap": 150.27}
        >>> result = processor.extract_quote_values(quote_data)
        >>> result.bid_price  # Returns Decimal("150.25")

    Raises:
        DataProviderError: When required data is missing or invalid

    """

    def __init__(self) -> None:
        """Initialize the data processor with structured logging."""
        self.logger = get_logger(__name__)

    def extract_symbol_from_quote(self, data: AlpacaQuoteData) -> str:
        """Extract symbol from quote data.

        Alpaca uses different key names for dict vs object format:
        - Dict format: "S" key (shorthand for symbol)
        - Object format: "symbol" attribute

        Args:
            data: Quote data from Alpaca WebSocket (dict or Quote object)

        Returns:
            Symbol string

        Raises:
            DataProviderError: If symbol cannot be extracted from data

        """
        if hasattr(data, "symbol"):
            symbol = str(data.symbol)
        elif isinstance(data, dict):
            symbol = str(data.get("S", ""))
        else:
            symbol = ""

        if not symbol or not symbol.strip():
            raise DataProviderError(
                "Symbol missing or empty in quote data",
                {"data_type": type(data).__name__},
            )

        return symbol

    def extract_quote_values(self, data: AlpacaQuoteData) -> QuoteExtractionResult:
        """Extract bid/ask data from quote.

        Converts all financial data to Decimal for precision per Alchemiser guardrails.
        Alpaca dict format uses abbreviated keys: bp=bid_price, ap=ask_price,
        bs=bid_size, as=ask_size, t=timestamp.

        Args:
            data: Quote data from Alpaca WebSocket (dict or Quote object)

        Returns:
            QuoteExtractionResult with extracted Decimal values

        Raises:
            DataProviderError: If required quote data is missing or invalid

        """
        if isinstance(data, dict):
            return QuoteExtractionResult(
                bid_price=self._safe_decimal_convert(data.get("bp")),
                ask_price=self._safe_decimal_convert(data.get("ap")),
                bid_size=self._safe_decimal_convert(data.get("bs")),
                ask_size=self._safe_decimal_convert(data.get("as")),
                timestamp_raw=self._safe_datetime_convert(data.get("t")),
            )

        return QuoteExtractionResult(
            bid_price=self._safe_decimal_convert(getattr(data, "bid_price", None)),
            ask_price=self._safe_decimal_convert(getattr(data, "ask_price", None)),
            bid_size=self._safe_decimal_convert(getattr(data, "bid_size", None)),
            ask_size=self._safe_decimal_convert(getattr(data, "ask_size", None)),
            timestamp_raw=self._safe_datetime_convert(getattr(data, "timestamp", None)),
        )

    def extract_symbol_from_trade(self, data: AlpacaTradeData) -> str:
        """Extract symbol from trade data.

        Alpaca uses different key names for dict vs object format:
        - Dict format: "symbol" key (full name, not abbreviated like quotes)
        - Object format: "symbol" attribute

        Args:
            data: Trade data from Alpaca WebSocket (dict or Trade object)

        Returns:
            Symbol string

        Raises:
            DataProviderError: If symbol cannot be extracted from data

        """
        if hasattr(data, "symbol"):
            symbol = str(data.symbol)
        elif isinstance(data, dict):
            symbol = str(data.get("symbol", ""))
        else:
            symbol = ""

        if not symbol or not symbol.strip():
            raise DataProviderError(
                "Symbol missing or empty in trade data",
                {"data_type": type(data).__name__},
            )

        return symbol

    def extract_trade_values(
        self, trade: AlpacaTradeData
    ) -> tuple[Decimal, Decimal | None, datetime]:
        """Extract price, volume, and timestamp from trade data.

        Uses Decimal for price and volume to maintain financial precision per
        Alchemiser guardrails. Requires timestamp to be present.

        Args:
            trade: Trade data from Alpaca WebSocket (dict or Trade object)

        Returns:
            Tuple of (price, volume, timestamp) with Decimal precision

        Raises:
            DataProviderError: If timestamp is missing or data is invalid

        """
        timestamp_raw: datetime | str | float | int | None
        if isinstance(trade, dict):
            price_raw = trade.get("price")
            if price_raw is None:
                raise DataProviderError("Price missing in trade data", {"data_type": "dict"})
            size = trade.get("size", 0)
            volume = trade.get("volume", size)
            timestamp_raw = trade.get("timestamp")
        else:
            if not hasattr(trade, "price"):
                raise DataProviderError(
                    "Price missing in trade data", {"data_type": type(trade).__name__}
                )
            price_raw = trade.price
            size = trade.size if hasattr(trade, "size") else 0
            volume = getattr(trade, "volume", size)
            timestamp_raw = trade.timestamp if hasattr(trade, "timestamp") else None

        # Convert price to Decimal
        price = self._safe_decimal_convert(price_raw)
        if price is None:
            raise DataProviderError("Invalid price in trade data", {"price_raw": str(price_raw)})

        # Convert volume to Decimal (volume can be None)
        volume_decimal: Decimal | None = self._safe_decimal_convert(volume)

        # Get timestamp (required)
        timestamp = self.get_trade_timestamp(timestamp_raw)

        return price, volume_decimal, timestamp

    def get_quote_timestamp(self, timestamp_raw: datetime | None) -> datetime:
        """Ensure timestamp is a datetime for quotes.

        Deterministic behavior: raises exception if timestamp is missing rather
        than using datetime.now() which breaks test reproducibility.

        Args:
            timestamp_raw: Raw timestamp value from quote data

        Returns:
            Valid datetime object

        Raises:
            DataProviderError: If timestamp is None or not a datetime

        """
        if not isinstance(timestamp_raw, datetime):
            raise DataProviderError(
                "Quote timestamp missing or invalid",
                {"timestamp_type": (type(timestamp_raw).__name__ if timestamp_raw else "None")},
            )
        return timestamp_raw

    def get_trade_timestamp(self, timestamp_raw: datetime | str | float | int | None) -> datetime:
        """Ensure timestamp is a datetime for trades.

        Deterministic behavior: raises exception if timestamp is missing rather
        than using datetime.now() which breaks test reproducibility.

        Args:
            timestamp_raw: Raw timestamp value from trade data

        Returns:
            Valid datetime object

        Raises:
            DataProviderError: If timestamp is None or not a datetime

        """
        if not isinstance(timestamp_raw, datetime):
            raise DataProviderError(
                "Trade timestamp missing or invalid",
                {"timestamp_type": (type(timestamp_raw).__name__ if timestamp_raw else "None")},
            )
        return timestamp_raw

    def _safe_decimal_convert(self, value: str | float | int | None) -> Decimal | None:
        """Safely convert value to Decimal for financial precision.

        Per Alchemiser guardrails, all financial data must use Decimal
        to avoid floating-point precision issues.

        Args:
            value: Value to convert (price, size, volume, etc.)

        Returns:
            Decimal value or None if value is None or conversion fails

        """
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, ArithmeticError):
            self.logger.warning(
                "Failed to convert value to Decimal",
                extra={"value": str(value), "value_type": type(value).__name__},
            )
            return None

    def _safe_datetime_convert(self, value: str | float | int | datetime | None) -> datetime | None:
        """Safely convert value to datetime.

        Args:
            value: Value to convert

        Returns:
            Datetime value or None if not a datetime

        """
        if isinstance(value, datetime):
            return value
        return None

    def log_quote_debug(
        self,
        symbol: str,
        bid_price: Decimal | None,
        ask_price: Decimal | None,
        correlation_id: str | None = None,
    ) -> None:
        """Log quote data for debugging with structured logging.

        Uses structured logging with correlation_id for observability.
        Simplified to synchronous as logging is thread-safe.

        Args:
            symbol: Stock symbol
            bid_price: Bid price (Decimal)
            ask_price: Ask price (Decimal)
            correlation_id: Optional correlation ID for tracing

        """
        self.logger.debug(
            "Quote received",
            extra={
                "symbol": symbol,
                "bid_price": str(bid_price) if bid_price else None,
                "ask_price": str(ask_price) if ask_price else None,
                "correlation_id": correlation_id,
            },
        )

    def handle_quote_error(self, error: Exception, correlation_id: str | None = None) -> None:
        """Handle errors in quote processing with structured logging.

        Uses structured logging with correlation_id for observability.
        Simplified to synchronous as logging is thread-safe.

        Args:
            error: Exception that occurred
            correlation_id: Optional correlation ID for tracing

        """
        self.logger.error(
            "Error processing quote",
            extra={
                "error": str(error),
                "error_type": type(error).__name__,
                "correlation_id": correlation_id,
            },
            exc_info=True,
        )
