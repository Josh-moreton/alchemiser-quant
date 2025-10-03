"""Business Unit: scripts | Status: current.

Market data models for backtesting.

Defines the data structures for historical market data used in backtesting.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyBar(BaseModel):
    """Daily OHLCV bar with adjusted close.

    Schema: Date, Open, High, Low, Close, Volume, Adjusted_Close
    """

    model_config = ConfigDict(frozen=True, strict=True)

    date: datetime = Field(description="Trading date (UTC timezone-aware)")
    open: Decimal = Field(description="Opening price", gt=0)
    high: Decimal = Field(description="High price", gt=0)
    low: Decimal = Field(description="Low price", gt=0)
    close: Decimal = Field(description="Closing price", gt=0)
    volume: int = Field(description="Trading volume", ge=0)
    adjusted_close: Decimal = Field(description="Adjusted closing price", gt=0)


class MarketDataRequest(BaseModel):
    """Request for historical market data.

    Used to specify which data to download from providers.
    """

    model_config = ConfigDict(frozen=True, strict=True)

    symbols: list[str] = Field(description="List of symbols to fetch", min_length=1)
    start_date: datetime = Field(description="Start date for data (inclusive)")
    end_date: datetime = Field(description="End date for data (inclusive)")


class MarketDataMetadata(BaseModel):
    """Metadata about stored market data.

    Tracks data quality and availability for validation.
    """

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(description="Stock symbol")
    start_date: datetime = Field(description="Earliest available date")
    end_date: datetime = Field(description="Latest available date")
    bar_count: int = Field(description="Number of bars stored", ge=0)
    last_updated: datetime = Field(description="When data was last updated")
    has_gaps: bool = Field(description="Whether there are gaps in the data")
