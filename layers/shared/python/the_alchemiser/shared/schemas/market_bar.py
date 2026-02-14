#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Market bar data transfer objects for strategy consumption.

Provides typed DTOs specifically for OHLCV bar data used by strategy engines,
with optimized structure for technical analysis and indicator calculations.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..constants import CONTRACT_VERSION
from ..logging import get_logger
from ..utils.timezone_utils import ensure_timezone_aware

logger = get_logger(__name__)

# Module exports
__all__ = ["MarketBar"]

# Constants for decimal field handling
_DECIMAL_FIELDS: Final[tuple[str, ...]] = (
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "vwap",
)


class MarketBar(BaseModel):
    """DTO for market bar data optimized for strategy consumption.

    Focused specifically on OHLCV data needed by strategy engines
    for technical analysis and indicator calculations.

    Example:
        >>> from datetime import datetime, UTC
        >>> from decimal import Decimal
        >>> bar = MarketBar(
        ...     timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=UTC),
        ...     symbol="AAPL",
        ...     timeframe="1D",
        ...     open_price=Decimal("150.00"),
        ...     high_price=Decimal("155.00"),
        ...     low_price=Decimal("149.00"),
        ...     close_price=Decimal("154.00"),
        ...     volume=1000000,
        ... )

    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema versioning for evolution tracking
    schema_version: str = Field(
        default=CONTRACT_VERSION, description="Schema version for compatibility"
    )

    # Bar identification
    timestamp: datetime = Field(..., description="Bar timestamp")
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Trading symbol (supports extended notation like EQUITIES::SYMBOL//USD)",
    )
    timeframe: str = Field(..., description="Timeframe (1D, 1H, 15Min, etc.)")

    # OHLCV data
    open_price: Decimal = Field(..., gt=0, description="Opening price")
    high_price: Decimal = Field(..., gt=0, description="Highest price")
    low_price: Decimal = Field(..., gt=0, description="Lowest price")
    close_price: Decimal = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

    # Optional technical analysis fields
    vwap: Decimal | None = Field(default=None, gt=0, description="Volume weighted average price")
    trade_count: int | None = Field(default=None, ge=0, description="Number of trades")

    # Data quality indicators
    data_source: str | None = Field(default=None, description="Data source identifier")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timeframe")
    @classmethod
    def normalize_timeframe(cls, v: str) -> str:
        """Normalize timeframe format."""
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @model_validator(mode="after")
    def validate_ohlc_relationships(self) -> MarketBar:
        """Validate OHLC price relationships after all fields are set."""
        # Validate high >= low
        if self.high_price < self.low_price:
            raise ValueError("High price must be >= low price")

        # Validate open is within [low, high]
        if self.open_price < self.low_price or self.open_price > self.high_price:
            raise ValueError(f"Open price must be within [{self.low_price}, {self.high_price}]")

        # Validate close is within [low, high]
        if self.close_price < self.low_price or self.close_price > self.high_price:
            raise ValueError(f"Close price must be within [{self.low_price}, {self.high_price}]")

        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation optimized for JSON serialization.

        """
        data = self.model_dump()

        # Convert datetime to ISO string (timestamp is always present as required field)
        data["timestamp"] = self.timestamp.isoformat()

        # Convert Decimal fields to string for JSON serialization
        for field_name in _DECIMAL_FIELDS:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketBar:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing bar data

        Returns:
            MarketBar instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Convert string timestamp back to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                timestamp_str = data["timestamp"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e

        # Convert string decimal fields back to Decimal
        for field_name in _DECIMAL_FIELDS:
            if (
                field_name in data
                and data[field_name] is not None
                and isinstance(data[field_name], str)
            ):
                try:
                    data[field_name] = Decimal(data[field_name])
                except Exception as e:
                    raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

        return cls(**data)

    @classmethod
    def from_alpaca_bar(cls, bar_dict: dict[str, Any], symbol: str, timeframe: str) -> MarketBar:
        """Create MarketBar from Alpaca SDK bar data.

        Args:
            bar_dict: Alpaca bar dictionary containing OHLCV data
            symbol: Trading symbol
            timeframe: Bar timeframe

        Returns:
            MarketBar instance

        Raises:
            ValueError: If required fields are missing or invalid

        """
        try:
            # Extract timestamp - handle both 't' and 'timestamp' keys
            timestamp_value = bar_dict.get("t") or bar_dict.get("timestamp")
            if timestamp_value is None:
                raise ValueError("Missing timestamp in bar data")

            # Handle datetime or string timestamp
            if isinstance(timestamp_value, datetime):
                timestamp = timestamp_value
            else:
                timestamp = datetime.fromisoformat(str(timestamp_value).replace("Z", "+00:00"))

            logger.info(
                "converting_alpaca_bar",
                symbol=symbol,
                timeframe=timeframe,
                has_vwap="vw" in bar_dict,
                has_trade_count="n" in bar_dict,
            )

            return cls(
                timestamp=timestamp,
                symbol=symbol,
                timeframe=timeframe,
                open_price=Decimal(str(bar_dict["o"])),
                high_price=Decimal(str(bar_dict["h"])),
                low_price=Decimal(str(bar_dict["l"])),
                close_price=Decimal(str(bar_dict["c"])),
                volume=int(bar_dict["v"]),
                vwap=Decimal(str(bar_dict["vw"])) if "vw" in bar_dict else None,
                trade_count=int(bar_dict["n"]) if "n" in bar_dict else None,
                data_source="alpaca",
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "alpaca_bar_conversion_failed",
                symbol=symbol,
                timeframe=timeframe,
                error=str(e),
            )
            raise ValueError(f"Invalid Alpaca bar data for {symbol}: {e}") from e

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert to legacy dictionary format for backward compatibility.

        Note: This method converts Decimal prices to float, which may result in
        precision loss. This is necessary for backward compatibility with existing
        strategy engines that expect float values.

        Returns:
            Dictionary in the format expected by existing strategy engines.

        """
        return {
            "t": self.timestamp,
            "o": float(self.open_price),
            "h": float(self.high_price),
            "l": float(self.low_price),
            "c": float(self.close_price),
            "v": self.volume,
            "vw": float(self.vwap) if self.vwap else None,
            "n": self.trade_count,
        }
