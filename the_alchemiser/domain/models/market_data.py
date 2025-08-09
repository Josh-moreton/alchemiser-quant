"""Market data domain models."""

from dataclasses import (
    dataclass,
)  # TODO(PYDANTIC-MIGRATION): Convert BarModel, QuoteModel, PriceDataModel to Pydantic for datetime parsing & validation.
from datetime import datetime

import pandas as pd

from the_alchemiser.domain.types import MarketDataPoint, PriceData, QuoteData


@dataclass(
    frozen=True
)  # TODO(PYDANTIC-MIGRATION): Replace with BarModel(BaseModel) and move timestamp parsing to validator.
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
    def from_dict(cls, data: MarketDataPoint) -> "BarModel":
        """Create from MarketDataPoint TypedDict."""
        timestamp_raw = data["timestamp"]
        timestamp_parsed = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))

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


@dataclass(
    frozen=True
)  # TODO(PYDANTIC-MIGRATION): Replace with QuoteModel(BaseModel) and enforce bid<=ask, positive sizes.
class QuoteModel:
    """Immutable quote data model."""

    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: QuoteData, symbol: str) -> "QuoteModel":
        """Create from QuoteData TypedDict."""
        timestamp_raw = data["timestamp"]
        timestamp_parsed = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))

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


@dataclass(
    frozen=True
)  # TODO(PYDANTIC-MIGRATION): Replace with PriceDataModel(BaseModel); optional bid/ask validation.
class PriceDataModel:
    """Immutable price data model."""

    symbol: str
    price: float
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
    volume: int | None = None

    @classmethod
    def from_dict(cls, data: PriceData) -> "PriceDataModel":
        """Create from PriceData TypedDict."""
        timestamp_raw = data["timestamp"]
        timestamp_parsed = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))

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
