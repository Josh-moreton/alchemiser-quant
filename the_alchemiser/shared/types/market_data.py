"""Business Unit: utilities; Status: current.

Market data domain models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from the_alchemiser.shared.constants import UTC_TIMEZONE_SUFFIX
from the_alchemiser.shared.value_objects.core_types import MarketDataPoint, PriceData, QuoteData

# Legacy alias for backward compatibility
_UTC_TIMEZONE_SUFFIX = UTC_TIMEZONE_SUFFIX


@dataclass(frozen=True)
class BarModel:
    """Immutable market bar data model."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    @classmethod
    def from_dict(cls, data: MarketDataPoint) -> BarModel:
        """Create from MarketDataPoint TypedDict."""
        timestamp_raw = data["timestamp"]
        timestamp_parsed = datetime.fromisoformat(timestamp_raw.replace("Z", _UTC_TIMEZONE_SUFFIX))

        return cls(
            symbol=data["symbol"],
            timestamp=timestamp_parsed,
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
        )

    def to_dict(self) -> MarketDataPoint:
        """Convert to MarketDataPoint TypedDict."""
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
        """Check if OHLC values are valid."""
        return (
            self.high >= max(self.open, self.close)
            and self.low <= min(self.open, self.close)
            and all(x >= 0 for x in [self.open, self.high, self.low, self.close])
        )


@dataclass(frozen=True)
class QuoteModel:
    """Immutable quote data model."""

    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: QuoteData, symbol: str) -> QuoteModel:
        """Create from QuoteData TypedDict (domain-pure)."""
        timestamp_raw = data["timestamp"]
        timestamp_parsed = datetime.fromisoformat(timestamp_raw.replace("Z", _UTC_TIMEZONE_SUFFIX))

        return cls(
            symbol=symbol,
            bid_price=data["bid_price"],
            ask_price=data["ask_price"],
            bid_size=data["bid_size"],
            ask_size=data["ask_size"],
            timestamp=timestamp_parsed,
        )

    def to_dict(self) -> QuoteData:
        """Convert to QuoteData TypedDict."""
        return {
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
            "timestamp": self.timestamp.isoformat(),
        }

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        return self.ask_price - self.bid_price

    @property
    def mid_price(self) -> float:
        """Calculate mid-point price."""
        return (self.bid_price + self.ask_price) / 2


@dataclass(frozen=True)
class PriceDataModel:
    """Immutable price data model."""

    symbol: str
    price: float
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
    volume: int | None = None

    @classmethod
    def from_dict(cls, data: PriceData) -> PriceDataModel:
        """Create from PriceData TypedDict."""
        timestamp_raw = data["timestamp"]
        timestamp_parsed = datetime.fromisoformat(timestamp_raw.replace("Z", _UTC_TIMEZONE_SUFFIX))

        return cls(
            symbol=data["symbol"],
            price=data["price"],
            timestamp=timestamp_parsed,
            bid=data.get("bid"),
            ask=data.get("ask"),
            volume=data.get("volume"),
        )

    def to_dict(self) -> PriceData:
        """Convert to PriceData TypedDict."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "bid": self.bid,
            "ask": self.ask,
            "volume": self.volume,
        }

    @property
    def has_quote_data(self) -> bool:
        """Check if bid/ask data is available."""
        return self.bid is not None and self.ask is not None


def bars_to_dataframe(bars: list[BarModel]) -> pd.DataFrame:
    """Convert list of BarModel to pandas DataFrame."""
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
    """Convert pandas DataFrame to list of BarModel."""
    bars = []
    for timestamp, row in df.iterrows():
        bars.append(
            BarModel(
                symbol=symbol,
                timestamp=timestamp,
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
    
    Deprecated: Use QuoteModel for new code.
    Kept for backward compatibility with existing code.
    """

    bid: float
    ask: float
    last_price: float
    timestamp: datetime

    @property
    def mid_price(self) -> float:
        """Calculate mid-point between bid and ask."""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        if self.bid > 0:
            return self.bid
        if self.ask > 0:
            return self.ask
        return self.last_price


@dataclass
class SubscriptionPlan:
    """Helper class for bulk subscription planning."""

    results: dict[str, bool]
    symbols_to_add: list[str]
    symbols_to_replace: list[str]
    available_slots: int
    successfully_added: int = 0


@dataclass
class QuoteExtractionResult:
    """Container for quote values extracted from incoming data."""

    bid_price: float | None
    ask_price: float | None
    bid_size: float | None
    ask_size: float | None
    timestamp_raw: datetime | None
