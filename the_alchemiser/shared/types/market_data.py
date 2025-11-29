"""Business Unit: shared | Status: current.

Market data domain models.

This module provides immutable dataclass-based models for market data used
throughout the trading system. Models include OHLCV bars, quotes, and price data.

✅ Uses Decimal for all financial data to ensure precision in calculations,
per Alchemiser guardrails for monetary values.

Usage:
    from the_alchemiser.shared.types.market_data import BarModel, QuoteModel

    # Convert from TypedDict (adapter layer)
    bar = BarModel.from_dict(market_data_point)

    # Access OHLC data with Decimal precision
    if bar.is_valid_ohlc:
        strategy.process(bar)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.constants import UTC_TIMEZONE_SUFFIX
from the_alchemiser.shared.errors.exceptions import (
    PriceValidationError,
    SymbolValidationError,
    ValidationError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.value_objects.core_types import (
    MarketDataPoint,
    PriceData,
    QuoteData,
)

if TYPE_CHECKING:
    import pandas as pd

logger = get_logger(__name__)

# Error message constants (SonarQube: S1192)
_ERR_SYMBOL_EMPTY = "Symbol cannot be empty"
_ERR_TIMESTAMP_EMPTY = "Timestamp cannot be empty"
_ERR_EMPTY_OR_WHITESPACE = "Empty or whitespace"


@dataclass(frozen=True)
class BarModel:
    """Immutable market bar data model for OHLCV candlestick data.

    Represents a single time period of market data with open, high, low, close
    prices and volume. Used by strategy engines for technical analysis.

    ✅ Uses Decimal for all prices to ensure precision in financial calculations,
    per Alchemiser guardrails for monetary values.

    Attributes:
        symbol: Trading symbol (e.g., "AAPL", "BTC/USD")
        timestamp: Bar timestamp in UTC (timezone-aware)
        open: Opening price for the period (Decimal)
        high: Highest price during the period (Decimal)
        low: Lowest price during the period (Decimal)
        close: Closing price for the period (Decimal)
        volume: Trading volume (number of shares/units)

    Validation:
        - OHLC relationships are validated via is_valid_ohlc property
        - Timestamps must be timezone-aware UTC
        - Prices should be non-negative
        - Volume should be non-negative

    """

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    @classmethod
    def from_dict(cls, data: MarketDataPoint) -> BarModel:
        """Create from MarketDataPoint TypedDict.

        Converts Decimal values from TypedDict to float for internal storage.
        Validates input data and ensures timezone-aware timestamps.

        Args:
            data: MarketDataPoint TypedDict from adapter layer

        Returns:
            BarModel instance

        Raises:
            ValueError: If timestamp format is invalid
            ValueError: If symbol is empty
            ValueError: If prices are negative
            ValueError: If volume is negative

        Example:
            >>> data: MarketDataPoint = {
            ...     "symbol": "AAPL",
            ...     "timestamp": "2024-01-01T10:00:00Z",
            ...     "open": Decimal("150.00"),
            ...     "high": Decimal("155.00"),
            ...     "low": Decimal("149.00"),
            ...     "close": Decimal("154.00"),
            ...     "volume": 1000000,
            ... }
            >>> bar = BarModel.from_dict(data)

        """
        # Validate symbol
        symbol = data["symbol"]
        if not symbol or not symbol.strip():
            raise SymbolValidationError(
                _ERR_SYMBOL_EMPTY, symbol=symbol, reason=_ERR_EMPTY_OR_WHITESPACE
            )

        # Parse and validate timestamp
        timestamp_raw = data["timestamp"]
        if not timestamp_raw:
            raise ValidationError(_ERR_TIMESTAMP_EMPTY, field_name="timestamp")

        try:
            # Handle both 'Z' suffix and '+00:00' suffix
            timestamp_str = timestamp_raw.replace("Z", UTC_TIMEZONE_SUFFIX)
            timestamp_parsed = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid timestamp format: {timestamp_raw}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValidationError(
                f"Invalid timestamp format: {timestamp_raw}",
                field_name="timestamp",
                value=timestamp_raw,
            ) from e

        # Ensure timezone-aware
        if timestamp_parsed.tzinfo is None:
            logger.warning(
                f"Timestamp missing timezone info, assuming UTC: {timestamp_raw}",
                extra={"symbol": symbol},
            )
            timestamp_parsed = timestamp_parsed.replace(tzinfo=UTC)

        # Convert prices to Decimal and validate
        try:
            open_price = Decimal(str(data["open"]))
            high_price = Decimal(str(data["high"]))
            low_price = Decimal(str(data["low"]))
            close_price = Decimal(str(data["close"]))
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid price data for {symbol}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise PriceValidationError(
                f"Invalid price data: {e}", symbol=symbol, field_name="ohlc_prices"
            ) from e

        # Validate prices are non-negative
        if any(p < 0 for p in [open_price, high_price, low_price, close_price]):
            raise PriceValidationError(
                f"Prices cannot be negative: "
                f"open={open_price}, high={high_price}, low={low_price}, close={close_price}",
                symbol=symbol,
                field_name="ohlc_prices",
            )

        # Validate volume
        volume = data["volume"]
        if volume < 0:
            raise ValidationError(
                f"Volume cannot be negative: {volume}", field_name="volume", value=volume
            )

        bar = cls(
            symbol=symbol,
            timestamp=timestamp_parsed,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
        )

        # Validate OHLC relationships
        if not bar.is_valid_ohlc:
            logger.warning(
                f"Invalid OHLC relationships for {symbol}",
                extra={
                    "symbol": symbol,
                    "timestamp": timestamp_raw,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                },
            )

        return bar

    def to_dict(self) -> MarketDataPoint:
        """Convert to MarketDataPoint TypedDict.

        Returns Decimal values directly for TypedDict compliance with the
        adapter layer contract.

        Returns:
            MarketDataPoint TypedDict suitable for adapter layer

        """
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

    @property
    def is_valid_ohlc(self) -> bool:
        """Check if OHLC values satisfy standard relationships.

        Validates:
        - High >= max(open, close)
        - Low <= min(open, close)
        - All prices >= 0

        Returns:
            True if OHLC relationships are valid, False otherwise

        Note:
            Uses Decimal comparison which is exact and suitable for financial data.

        """
        return (
            self.high >= max(self.open, self.close)
            and self.low <= min(self.open, self.close)
            and all(x >= 0 for x in [self.open, self.high, self.low, self.close])
        )


@dataclass(frozen=True)
class QuoteModel:
    """Immutable quote data model for bid/ask market quotes.

    Represents Level 1 market data with bid/ask prices and sizes.
    Used for spread analysis and mid-price calculations.

    ✅ Uses Decimal for all prices and sizes to ensure precision in financial
    calculations, per Alchemiser guardrails for monetary values.

    Attributes:
        symbol: Trading symbol
        bid_price: Best bid price (Decimal)
        ask_price: Best ask price (Decimal)
        bid_size: Size (shares/units) at bid price (Decimal)
        ask_size: Size (shares/units) at ask price (Decimal)
        timestamp: Quote timestamp in UTC (timezone-aware)

    Properties:
        spread: Bid-ask spread (ask_price - bid_price)
        mid_price: Mid-point price ((bid_price + ask_price) / 2)

    """

    symbol: str
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: QuoteData, symbol: str) -> QuoteModel:
        """Create from QuoteData TypedDict (domain-pure).

        Converts Decimal values from TypedDict to float for internal storage.
        Validates input data and ensures timezone-aware timestamps.

        Args:
            data: QuoteData TypedDict from adapter layer
            symbol: Trading symbol for this quote

        Returns:
            QuoteModel instance

        Raises:
            ValidationError: If timestamp format is invalid
            SymbolValidationError: If symbol is empty
            PriceValidationError: If prices or sizes are negative
            PriceValidationError: If bid_price > ask_price (inverted quote)

        """
        # Validate symbol
        if not symbol or not symbol.strip():
            raise SymbolValidationError(
                _ERR_SYMBOL_EMPTY, symbol=symbol, reason=_ERR_EMPTY_OR_WHITESPACE
            )

        # Parse and validate timestamp
        timestamp_raw = data["timestamp"]
        if not timestamp_raw:
            raise ValidationError(_ERR_TIMESTAMP_EMPTY, field_name="timestamp")

        try:
            timestamp_str = timestamp_raw.replace("Z", UTC_TIMEZONE_SUFFIX)
            timestamp_parsed = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid timestamp format: {timestamp_raw}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValidationError(
                f"Invalid timestamp format: {timestamp_raw}",
                field_name="timestamp",
                value=timestamp_raw,
            ) from e

        # Ensure timezone-aware
        if timestamp_parsed.tzinfo is None:
            logger.warning(
                f"Timestamp missing timezone info, assuming UTC: {timestamp_raw}",
                extra={"symbol": symbol},
            )
            timestamp_parsed = timestamp_parsed.replace(tzinfo=UTC)

        # Convert prices and sizes to Decimal and validate
        try:
            bid_price = Decimal(str(data["bid_price"]))
            ask_price = Decimal(str(data["ask_price"]))
            bid_size = Decimal(str(data["bid_size"]))
            ask_size = Decimal(str(data["ask_size"]))
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid quote data for {symbol}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise PriceValidationError(
                f"Invalid quote data: {e}", symbol=symbol, field_name="quote_data"
            ) from e

        # Validate prices and sizes are non-negative
        if bid_price < 0 or ask_price < 0:
            raise PriceValidationError(
                f"Prices cannot be negative: bid={bid_price}, ask={ask_price}",
                symbol=symbol,
                field_name="quote_prices",
            )
        if bid_size < 0 or ask_size < 0:
            raise ValidationError(
                f"Sizes cannot be negative: bid_size={bid_size}, ask_size={ask_size}",
                field_name="quote_sizes",
            )

        # Validate bid <= ask (normal quote)
        if bid_price > ask_price:
            logger.warning(
                f"Inverted quote detected for {symbol}: bid={bid_price} > ask={ask_price}",
                extra={
                    "symbol": symbol,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                },
            )

        return cls(
            symbol=symbol,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=bid_size,
            ask_size=ask_size,
            timestamp=timestamp_parsed,
        )

    def to_dict(self) -> QuoteData:
        """Convert to QuoteData TypedDict.

        Returns Decimal values directly for TypedDict compliance.

        Returns:
            QuoteData TypedDict suitable for adapter layer

        """
        return {
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
            "timestamp": self.timestamp.isoformat(),
        }

    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread.

        Returns:
            Spread as (ask_price - bid_price) in Decimal

        """
        return self.ask_price - self.bid_price

    @property
    def mid_price(self) -> Decimal:
        """Calculate mid-point price between bid and ask.

        Returns:
            Mid-price as (bid_price + ask_price) / 2 in Decimal

        """
        return (self.bid_price + self.ask_price) / Decimal("2")


def _validate_and_convert_optional_price(
    value: Decimal | float | int | None,
    price_name: str,
    symbol: str,
) -> Decimal | None:
    """Validate and convert an optional price value to Decimal.

    Helper function to reduce cognitive complexity in from_dict methods.

    Args:
        value: Optional price value to validate and convert
        price_name: Name of the price field (for error messages)
        symbol: Trading symbol (for error messages)

    Returns:
        Decimal value if input is not None, otherwise None

    Raises:
        PriceValidationError: If value is invalid or negative

    """
    if value is None:
        return None

    try:
        decimal_val = Decimal(str(value))
        if decimal_val < 0:
            raise PriceValidationError(
                f"{price_name} cannot be negative: {decimal_val}",
                symbol=symbol,
                price=float(decimal_val),
                field_name=price_name,
            )
        return decimal_val
    except (ValueError, TypeError) as e:
        logger.error(
            f"Invalid {price_name.lower()} for {symbol}",
            extra={"symbol": symbol, "error": str(e)},
        )
        raise PriceValidationError(
            f"Invalid {price_name.lower()}: {e}", symbol=symbol, field_name=price_name
        ) from e


@dataclass(frozen=True)
class PriceDataModel:
    """Immutable price data model for real-time price information.

    Represents current market price with optional bid/ask spread and volume.
    Used for current price lookups and market data snapshots.

    ✅ Uses Decimal for all prices to ensure precision in financial calculations,
    per Alchemiser guardrails for monetary values.

    Attributes:
        symbol: Trading symbol
        price: Current market price (Decimal)
        timestamp: Price timestamp in UTC (timezone-aware)
        bid: Optional bid price (Decimal)
        ask: Optional ask price (Decimal)
        volume: Optional current volume

    Properties:
        has_quote_data: True if both bid and ask are present

    """

    symbol: str
    price: Decimal
    timestamp: datetime
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: int | None = None

    @classmethod
    def from_dict(cls, data: PriceData) -> PriceDataModel:
        """Create from PriceData TypedDict.

        Converts Decimal values from TypedDict to float for internal storage.
        Validates input data and ensures timezone-aware timestamps.

        Args:
            data: PriceData TypedDict from adapter layer

        Returns:
            PriceDataModel instance

        Raises:
            ValidationError: If timestamp format is invalid
            SymbolValidationError: If symbol is empty
            PriceValidationError: If price is negative
            PriceValidationError: If bid or ask are negative (when present)

        """
        # Validate symbol
        symbol = data["symbol"]
        if not symbol or not symbol.strip():
            raise SymbolValidationError(
                _ERR_SYMBOL_EMPTY, symbol=symbol, reason=_ERR_EMPTY_OR_WHITESPACE
            )

        # Parse and validate timestamp
        timestamp_raw = data["timestamp"]
        if not timestamp_raw:
            raise ValidationError(_ERR_TIMESTAMP_EMPTY, field_name="timestamp")

        try:
            timestamp_str = timestamp_raw.replace("Z", UTC_TIMEZONE_SUFFIX)
            timestamp_parsed = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid timestamp format: {timestamp_raw}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValidationError(
                f"Invalid timestamp format: {timestamp_raw}",
                field_name="timestamp",
                value=timestamp_raw,
            ) from e

        # Ensure timezone-aware
        if timestamp_parsed.tzinfo is None:
            logger.warning(
                f"Timestamp missing timezone info, assuming UTC: {timestamp_raw}",
                extra={"symbol": symbol},
            )
            timestamp_parsed = timestamp_parsed.replace(tzinfo=UTC)

        # Convert price to Decimal and validate
        try:
            price = Decimal(str(data["price"]))
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid price for {symbol}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise PriceValidationError(
                f"Invalid price data: {e}", symbol=symbol, field_name="price"
            ) from e

        if price < 0:
            raise PriceValidationError(
                f"Price cannot be negative: {price}",
                symbol=symbol,
                price=float(price),
                field_name="price",
            )

        # Handle optional bid/ask using helper function
        bid_decimal = _validate_and_convert_optional_price(data.get("bid"), "Bid price", symbol)
        ask_decimal = _validate_and_convert_optional_price(data.get("ask"), "Ask price", symbol)

        # Validate bid <= ask if both present
        if bid_decimal is not None and ask_decimal is not None and bid_decimal > ask_decimal:
            logger.warning(
                f"Inverted quote for {symbol}: bid={bid_decimal} > ask={ask_decimal}",
                extra={
                    "symbol": symbol,
                    "bid": bid_decimal,
                    "ask": ask_decimal,
                },
            )

        return cls(
            symbol=symbol,
            price=price,
            timestamp=timestamp_parsed,
            bid=bid_decimal,
            ask=ask_decimal,
            volume=data.get("volume"),
        )

    def to_dict(self) -> PriceData:
        """Convert to PriceData TypedDict.

        Returns Decimal values directly for TypedDict compliance.

        Returns:
            PriceData TypedDict suitable for adapter layer

        """
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "bid": self.bid if self.bid is not None else None,
            "ask": self.ask if self.ask is not None else None,
            "volume": self.volume,
        }

    @property
    def has_quote_data(self) -> bool:
        """Check if bid/ask quote data is available.

        Returns:
            True if both bid and ask are present, False otherwise

        """
        return self.bid is not None and self.ask is not None


def bars_to_dataframe(bars: list[BarModel]) -> pd.DataFrame:
    """Convert list of BarModel to pandas DataFrame for analysis.

    Creates a DataFrame with OHLCV columns indexed by timestamp, suitable for
    technical analysis and indicator calculations.

    Args:
        bars: List of BarModel instances (should all be same symbol)

    Returns:
        DataFrame with columns [Open, High, Low, Close, Volume] indexed by Date
        Empty DataFrame if bars list is empty

    Example:
        >>> bars = [BarModel(...), BarModel(...)]
        >>> df = bars_to_dataframe(bars)
        >>> df['Close'].mean()  # Calculate average close price

    """
    import pandas as pd

    if not bars:
        return pd.DataFrame()

    data = {
        "Open": [bar.open for bar in bars],
        "High": [bar.high for bar in bars],
        "Low": [bar.low for bar in bars],
        "Close": [bar.close for bar in bars],
        "Volume": [bar.volume for bar in bars],
    }

    df = pd.DataFrame(data, index=[bar.timestamp for bar in bars])
    df.index.name = "Date"
    return df


def dataframe_to_bars(df: pd.DataFrame, symbol: str) -> list[BarModel]:
    """Convert pandas DataFrame to list of BarModel.

    Converts a DataFrame with OHLCV columns to a list of BarModel instances.
    Expects DataFrame index to be timestamps. Converts price values to Decimal.

    Args:
        df: DataFrame with columns [Open, High, Low, Close, Volume (optional)]
        symbol: Trading symbol to assign to all bars

    Returns:
        List of BarModel instances with Decimal prices

    Note:
        Uses iterrows() which is not the most efficient for large DataFrames.
        For better performance with large datasets, consider vectorized conversion
        or df.to_dict('records') approach.

    Example:
        >>> df = pd.DataFrame(...)  # OHLCV data
        >>> bars = dataframe_to_bars(df, "AAPL")

    """
    bars = []
    for timestamp, row in df.iterrows():
        bars.append(
            BarModel(
                symbol=symbol,
                timestamp=timestamp,
                open=Decimal(str(row["Open"])),
                high=Decimal(str(row["High"])),
                low=Decimal(str(row["Low"])),
                close=Decimal(str(row["Close"])),
                volume=int(row.get("Volume", 0)),
            )
        )
    return bars


@dataclass
class RealTimeQuote:
    """Real-time quote data structure (legacy).

    ⚠️ DEPRECATED: Use QuoteModel for new code.

    This class is kept for backward compatibility with existing code that
    relies on mutable quote objects. New code should use the immutable
    QuoteModel instead.

    Planned removal: v3.0.0
    Migration path: Replace with QuoteModel.from_dict()

    Attributes:
        bid: Bid price
        ask: Ask price
        last_price: Last trade price
        timestamp: Quote timestamp

    """

    bid: float
    ask: float
    last_price: float
    timestamp: datetime

    @property
    def mid_price(self) -> float:
        """Calculate mid-point between bid and ask with fallback logic.

        Returns bid/ask mid-price if both present, otherwise falls back to
        single side or last_price.

        Returns:
            Mid-price if bid and ask both > 0
            Bid price if only bid > 0
            Ask price if only ask > 0
            Last price otherwise

        """
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        if self.bid > 0:
            return self.bid
        if self.ask > 0:
            return self.ask
        return self.last_price


@dataclass
class SubscriptionPlan:
    """Helper class for bulk subscription planning (internal use).

    Used internally by streaming/subscription management code to track
    subscription allocation and results.

    Note: Intentionally mutable as it tracks dynamic subscription state.
    """

    results: dict[str, bool]
    symbols_to_add: list[str]
    symbols_to_replace: list[str]
    available_slots: int
    successfully_added: int = 0


@dataclass(frozen=True)
class QuoteExtractionResult:
    """Container for quote values extracted from incoming data (internal use).

    Used internally by quote parsing/extraction logic to temporarily hold
    parsed quote components before validation and conversion.

    All prices and sizes use Decimal for financial precision per Alchemiser guardrails.
    """

    bid_price: Decimal | None
    ask_price: Decimal | None
    bid_size: Decimal | None
    ask_size: Decimal | None
    timestamp_raw: datetime | None


# Public API
__all__ = [
    "BarModel",
    "PriceDataModel",
    "QuoteExtractionResult",
    "QuoteModel",
    "RealTimeQuote",
    "SubscriptionPlan",
    "bars_to_dataframe",
    "dataframe_to_bars",
]
