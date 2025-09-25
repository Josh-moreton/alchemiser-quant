#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Market Data DTOs for The Alchemiser Trading System.

This module contains DTOs for market data operations, price queries,
spread analysis, and market status information.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Decimal precision for financial values
- Comprehensive field validation and normalization
- Type safety for market data operations
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from the_alchemiser.shared.schemas.base import Result
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware


class PriceResult(Result):
    """DTO for latest price information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    price: Decimal | None = None
    error: str | None = None


class PriceHistoryResult(Result):
    """DTO for price history data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    timeframe: str | None = None
    limit: int | None = None
    data: list[dict[str, Any]] | None = None
    error: str | None = None


class SpreadAnalysisResult(Result):
    """DTO for bid-ask spread analysis."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    spread_analysis: dict[str, Any] | None = None
    error: str | None = None


class MarketStatusResult(Result):
    """DTO for market status information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    market_open: bool | None = None
    error: str | None = None


class MultiSymbolQuotesResult(Result):
    """DTO for multi-symbol quote data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    quotes: dict[str, Decimal] | None = None
    symbols: list[str] | None = None
    error: str | None = None


class MarketBar(BaseModel):
    """DTO for market bar data optimized for strategy consumption.

    Focused specifically on OHLCV data needed by strategy engines
    for technical analysis and indicator calculations.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Bar identification
    timestamp: datetime = Field(..., description="Bar timestamp")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
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
    is_incomplete: bool = Field(default=False, description="Whether bar data is incomplete")
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

    @field_validator("high_price")
    @classmethod
    def validate_high_price(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        """Validate high price is >= low price if both present."""
        if hasattr(info, "data") and "low_price" in info.data and v < info.data["low_price"]:
            raise ValueError("High price must be >= low price")
        return v

    @field_validator("low_price")
    @classmethod
    def validate_low_price(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        """Validate low price is <= high price if both present."""
        if hasattr(info, "data") and "high_price" in info.data and v > info.data["high_price"]:
            raise ValueError("Low price must be <= high price")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation optimized for JSON serialization.

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        # Convert Decimal fields to string for JSON serialization
        decimal_fields = [
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "vwap",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketBarDTO:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing bar data

        Returns:
            MarketBarDTO instance

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
        decimal_fields = [
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "vwap",
        ]
        for field_name in decimal_fields:
            if (
                field_name in data
                and data[field_name] is not None
                and isinstance(data[field_name], str)
            ):
                try:
                    data[field_name] = Decimal(data[field_name])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

        return cls(**data)

    @classmethod
    def from_alpaca_bar(cls, bar_dict: dict[str, Any], symbol: str, timeframe: str) -> MarketBarDTO:
        """Create MarketBarDTO from Alpaca SDK bar data.

        Args:
            bar_dict: Alpaca bar dictionary containing OHLCV data
            symbol: Trading symbol
            timeframe: Bar timeframe

        Returns:
            MarketBarDTO instance

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
            raise ValueError(f"Invalid Alpaca bar data for {symbol}: {e}") from e

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert to legacy dictionary format for backward compatibility.

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


# Backward compatibility aliases - will be removed in future version
PriceDTO = PriceResult
PriceHistoryDTO = PriceHistoryResult
SpreadAnalysisDTO = SpreadAnalysisResult
MarketStatusDTO = MarketStatusResult
MultiSymbolQuotesDTO = MultiSymbolQuotesResult

