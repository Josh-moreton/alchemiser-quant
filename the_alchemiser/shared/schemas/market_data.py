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
    """Schema for market bar data optimized for strategy consumption.

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
    open: Decimal = Field(..., gt=0, description="Open price")
    high: Decimal = Field(..., gt=0, description="High price")
    low: Decimal = Field(..., gt=0, description="Low price")
    close: Decimal = Field(..., gt=0, description="Close price")
    volume: int = Field(..., ge=0, description="Volume")

    # Optional computed fields for strategy use
    vwap: Decimal | None = Field(default=None, gt=0, description="Volume weighted average price")
    trade_count: int | None = Field(default=None, ge=0, description="Number of trades")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("high")
    @classmethod
    def validate_high(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        """Validate high price is >= low and open and close."""
        if hasattr(info, "data") and info.data:
            low_val = info.data.get("low")
            open_val = info.data.get("open")
            close_val = info.data.get("close")
            
            if low_val is not None and v < low_val:
                msg = f"High {v} cannot be less than low {low_val}"
                raise ValueError(msg)
            if open_val is not None and v < open_val:
                msg = f"High {v} cannot be less than open {open_val}"
                raise ValueError(msg)
            if close_val is not None and v < close_val:
                msg = f"High {v} cannot be less than close {close_val}"
                raise ValueError(msg)
        return v

    @field_validator("low")
    @classmethod
    def validate_low(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        """Validate low price is <= high and open and close."""
        if hasattr(info, "data") and info.data:
            high_val = info.data.get("high")
            open_val = info.data.get("open")
            close_val = info.data.get("close")
            
            if high_val is not None and v > high_val:
                msg = f"Low {v} cannot be greater than high {high_val}"
                raise ValueError(msg)
            if open_val is not None and v > open_val:
                msg = f"Low {v} cannot be greater than open {open_val}"
                raise ValueError(msg)
            if close_val is not None and v > close_val:
                msg = f"Low {v} cannot be greater than close {close_val}"
                raise ValueError(msg)
        return v



