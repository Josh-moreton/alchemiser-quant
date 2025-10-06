"""Business Unit: shared | Status: current.

Market data domain models.

This module provides immutable dataclass-based models for market data used
throughout the trading system. Models include OHLCV bars, quotes, and price data.

⚠️ KNOWN ISSUE: Uses float for financial data (see FILE_REVIEW_market_data.md)
Current implementation uses float types for prices, which can cause precision
issues in financial calculations. Migration to Decimal is planned.

Usage:
    from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
    
    # Convert from TypedDict (adapter layer)
    bar = BarModel.from_dict(market_data_point)
    
    # Access OHLC data
    if bar.is_valid_ohlc:
        strategy.process(bar)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd

from the_alchemiser.shared.constants import UTC_TIMEZONE_SUFFIX
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.value_objects.core_types import MarketDataPoint, PriceData, QuoteData

logger = get_logger(__name__)


@dataclass(frozen=True)
class BarModel:
    """Immutable market bar data model for OHLCV candlestick data.
    
    Represents a single time period of market data with open, high, low, close
    prices and volume. Used by strategy engines for technical analysis.
    
    ⚠️ KNOWN ISSUE: Uses float for prices instead of Decimal
    This can cause precision issues in financial calculations. A migration to
    Decimal types is planned but requires coordinated changes across the system.
    
    Attributes:
        symbol: Trading symbol (e.g., "AAPL", "BTC/USD")
        timestamp: Bar timestamp in UTC (timezone-aware)
        open: Opening price for the period
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price for the period
        volume: Trading volume (number of shares/units)
    
    Validation:
        - OHLC relationships are validated via is_valid_ohlc property
        - Timestamps must be timezone-aware UTC
        - Prices should be non-negative
        - Volume should be non-negative
    """

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
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
            raise ValueError("Symbol cannot be empty")
        
        # Parse and validate timestamp
        timestamp_raw = data["timestamp"]
        if not timestamp_raw:
            raise ValueError("Timestamp cannot be empty")
            
        try:
            # Handle both 'Z' suffix and '+00:00' suffix
            timestamp_str = timestamp_raw.replace("Z", UTC_TIMEZONE_SUFFIX)
            timestamp_parsed = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid timestamp format: {timestamp_raw}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValueError(f"Invalid timestamp format: {timestamp_raw}") from e
        
        # Ensure timezone-aware
        if timestamp_parsed.tzinfo is None:
            logger.warning(
                f"Timestamp missing timezone info, assuming UTC: {timestamp_raw}",
                extra={"symbol": symbol},
            )
            timestamp_parsed = timestamp_parsed.replace(tzinfo=UTC)
        
        # Convert prices to float and validate
        try:
            open_price = float(data["open"])
            high_price = float(data["high"])
            low_price = float(data["low"])
            close_price = float(data["close"])
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid price data for {symbol}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValueError(f"Invalid price data: {e}") from e
        
        # Validate prices are non-negative
        if any(p < 0 for p in [open_price, high_price, low_price, close_price]):
            raise ValueError(
                f"Prices cannot be negative: "
                f"open={open_price}, high={high_price}, low={low_price}, close={close_price}"
            )
        
        # Validate volume
        volume = data["volume"]
        if volume < 0:
            raise ValueError(f"Volume cannot be negative: {volume}")

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
        
        Converts float values to Decimal for TypedDict compliance with the
        adapter layer contract.
        
        Returns:
            MarketDataPoint TypedDict suitable for adapter layer
            
        Note:
            Float→Decimal conversion may introduce representation artifacts.
            For precise round-trips, consider using Decimal throughout the model.
        """
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": Decimal(str(self.open)),
            "high": Decimal(str(self.high)),
            "low": Decimal(str(self.low)),
            "close": Decimal(str(self.close)),
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
            Uses direct float comparison without tolerance. For production use
            with Decimal types, consider using explicit comparison contexts.
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
    
    ⚠️ KNOWN ISSUE: Uses float for prices instead of Decimal
    This can cause precision issues in financial calculations. A migration to
    Decimal types is planned but requires coordinated changes across the system.
    
    Attributes:
        symbol: Trading symbol
        bid_price: Best bid price
        ask_price: Best ask price
        bid_size: Size (shares/units) at bid price
        ask_size: Size (shares/units) at ask price
        timestamp: Quote timestamp in UTC (timezone-aware)
    
    Properties:
        spread: Bid-ask spread (ask_price - bid_price)
        mid_price: Mid-point price ((bid_price + ask_price) / 2)
    """

    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
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
            ValueError: If timestamp format is invalid
            ValueError: If symbol is empty
            ValueError: If prices or sizes are negative
            ValueError: If bid_price > ask_price (inverted quote)
        """
        # Validate symbol
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        # Parse and validate timestamp
        timestamp_raw = data["timestamp"]
        if not timestamp_raw:
            raise ValueError("Timestamp cannot be empty")
            
        try:
            timestamp_str = timestamp_raw.replace("Z", UTC_TIMEZONE_SUFFIX)
            timestamp_parsed = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid timestamp format: {timestamp_raw}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValueError(f"Invalid timestamp format: {timestamp_raw}") from e
        
        # Ensure timezone-aware
        if timestamp_parsed.tzinfo is None:
            logger.warning(
                f"Timestamp missing timezone info, assuming UTC: {timestamp_raw}",
                extra={"symbol": symbol},
            )
            timestamp_parsed = timestamp_parsed.replace(tzinfo=UTC)
        
        # Convert prices and sizes to float and validate
        try:
            bid_price = float(data["bid_price"])
            ask_price = float(data["ask_price"])
            bid_size = float(data["bid_size"])
            ask_size = float(data["ask_size"])
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid quote data for {symbol}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValueError(f"Invalid quote data: {e}") from e
        
        # Validate prices and sizes are non-negative
        if bid_price < 0 or ask_price < 0:
            raise ValueError(
                f"Prices cannot be negative: bid={bid_price}, ask={ask_price}"
            )
        if bid_size < 0 or ask_size < 0:
            raise ValueError(
                f"Sizes cannot be negative: bid_size={bid_size}, ask_size={ask_size}"
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
        
        Converts float values to Decimal for TypedDict compliance.
        
        Returns:
            QuoteData TypedDict suitable for adapter layer
        """
        return {
            "bid_price": Decimal(str(self.bid_price)),
            "ask_price": Decimal(str(self.ask_price)),
            "bid_size": Decimal(str(self.bid_size)),
            "ask_size": Decimal(str(self.ask_size)),
            "timestamp": self.timestamp.isoformat(),
        }

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread.
        
        Returns:
            Spread as (ask_price - bid_price)
            
        Note:
            Uses float arithmetic. For precise financial calculations,
            consider using Decimal types throughout.
        """
        return self.ask_price - self.bid_price

    @property
    def mid_price(self) -> float:
        """Calculate mid-point price between bid and ask.
        
        Returns:
            Mid-price as (bid_price + ask_price) / 2
            
        Note:
            Uses float arithmetic. For precise financial calculations,
            consider using Decimal types throughout.
        """
        return (self.bid_price + self.ask_price) / 2


@dataclass(frozen=True)
class PriceDataModel:
    """Immutable price data model for real-time price information.
    
    Represents current market price with optional bid/ask spread and volume.
    Used for current price lookups and market data snapshots.
    
    ⚠️ KNOWN ISSUE: Uses float for prices instead of Decimal
    This can cause precision issues in financial calculations. A migration to
    Decimal types is planned but requires coordinated changes across the system.
    
    Attributes:
        symbol: Trading symbol
        price: Current market price
        timestamp: Price timestamp in UTC (timezone-aware)
        bid: Optional bid price
        ask: Optional ask price
        volume: Optional current volume
    
    Properties:
        has_quote_data: True if both bid and ask are present
    """

    symbol: str
    price: float
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
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
            ValueError: If timestamp format is invalid
            ValueError: If symbol is empty
            ValueError: If price is negative
            ValueError: If bid or ask are negative (when present)
        """
        # Validate symbol
        symbol = data["symbol"]
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        # Parse and validate timestamp
        timestamp_raw = data["timestamp"]
        if not timestamp_raw:
            raise ValueError("Timestamp cannot be empty")
            
        try:
            timestamp_str = timestamp_raw.replace("Z", UTC_TIMEZONE_SUFFIX)
            timestamp_parsed = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid timestamp format: {timestamp_raw}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValueError(f"Invalid timestamp format: {timestamp_raw}") from e
        
        # Ensure timezone-aware
        if timestamp_parsed.tzinfo is None:
            logger.warning(
                f"Timestamp missing timezone info, assuming UTC: {timestamp_raw}",
                extra={"symbol": symbol},
            )
            timestamp_parsed = timestamp_parsed.replace(tzinfo=UTC)
        
        # Convert price to float and validate
        try:
            price = float(data["price"])
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid price for {symbol}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise ValueError(f"Invalid price data: {e}") from e
        
        if price < 0:
            raise ValueError(f"Price cannot be negative: {price}")
        
        # Handle optional bid/ask
        bid_val = data.get("bid")
        ask_val = data.get("ask")
        
        bid_float: float | None = None
        ask_float: float | None = None
        
        if bid_val is not None:
            try:
                bid_float = float(bid_val)
                if bid_float < 0:
                    raise ValueError(f"Bid price cannot be negative: {bid_float}")
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Invalid bid price for {symbol}",
                    extra={"symbol": symbol, "error": str(e)},
                )
                raise ValueError(f"Invalid bid price: {e}") from e
        
        if ask_val is not None:
            try:
                ask_float = float(ask_val)
                if ask_float < 0:
                    raise ValueError(f"Ask price cannot be negative: {ask_float}")
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Invalid ask price for {symbol}",
                    extra={"symbol": symbol, "error": str(e)},
                )
                raise ValueError(f"Invalid ask price: {e}") from e
        
        # Validate bid <= ask if both present
        if bid_float is not None and ask_float is not None and bid_float > ask_float:
            logger.warning(
                f"Inverted quote for {symbol}: bid={bid_float} > ask={ask_float}",
                extra={
                    "symbol": symbol,
                    "bid": bid_float,
                    "ask": ask_float,
                },
            )
        
        return cls(
            symbol=symbol,
            price=price,
            timestamp=timestamp_parsed,
            bid=bid_float,
            ask=ask_float,
            volume=data.get("volume"),
        )

    def to_dict(self) -> PriceData:
        """Convert to PriceData TypedDict.
        
        Converts float values to Decimal for TypedDict compliance.
        
        Returns:
            PriceData TypedDict suitable for adapter layer
        """
        return {
            "symbol": self.symbol,
            "price": Decimal(str(self.price)),
            "timestamp": self.timestamp.isoformat(),
            "bid": Decimal(str(self.bid)) if self.bid is not None else None,
            "ask": Decimal(str(self.ask)) if self.ask is not None else None,
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
    Expects DataFrame index to be timestamps.
    
    Args:
        df: DataFrame with columns [Open, High, Low, Close, Volume (optional)]
        symbol: Trading symbol to assign to all bars
        
    Returns:
        List of BarModel instances
        
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
                timestamp=timestamp,  # type: ignore[arg-type]
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
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


@dataclass
class QuoteExtractionResult:
    """Container for quote values extracted from incoming data (internal use).
    
    Used internally by quote parsing/extraction logic to temporarily hold
    parsed quote components before validation and conversion.
    
    Note: Intentionally mutable as it's an internal parsing container.
    """

    bid_price: float | None
    ask_price: float | None
    bid_size: float | None
    ask_size: float | None
    timestamp_raw: datetime | None


# Public API
__all__ = [
    "BarModel",
    "QuoteModel",
    "PriceDataModel",
    "bars_to_dataframe",
    "dataframe_to_bars",
    # Legacy (deprecated but still exported for backward compatibility)
    "RealTimeQuote",
    "SubscriptionPlan",
    "QuoteExtractionResult",
]
