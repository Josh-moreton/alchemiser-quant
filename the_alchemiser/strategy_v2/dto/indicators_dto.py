#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DTOs for strategy-related data transfer.

Provides typed DTOs for technical indicators, market data, and strategy calculations
to replace dict[str, Any] usage in strategy engines.

Part of the typing architecture enforcement initiative.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TechnicalIndicatorsDTO(BaseModel):
    """DTO for technical indicators calculated by strategy engines."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    rsi_10: float | None = Field(default=None, ge=0, le=100, description="10-period RSI")
    rsi_20: float | None = Field(default=None, ge=0, le=100, description="20-period RSI")
    ma_200: float | None = Field(default=None, gt=0, description="200-period moving average")
    ma_20: float | None = Field(default=None, gt=0, description="20-period moving average")
    ma_return_90: float | None = Field(default=None, description="90-period moving average return")
    cum_return_60: float | None = Field(default=None, description="60-period cumulative return")
    current_price: Decimal = Field(..., gt=0, description="Current asset price")


class StrategyIndicatorsDTO(BaseModel):
    """DTO for aggregated technical indicators across multiple symbols."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    indicators: dict[str, TechnicalIndicatorsDTO] = Field(
        ..., description="Technical indicators by symbol"
    )
    correlation_id: str = Field(..., min_length=1, description="Correlation identifier")
    calculation_timestamp: str = Field(..., description="When indicators were calculated")


class MarketDataInput(BaseModel):
    """DTO for market data input to strategy calculations."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    price_data: dict[str, float] = Field(..., description="Price data points")
    volume_data: dict[str, float] | None = Field(default=None, description="Volume data points")
    timestamp: str = Field(..., description="Data timestamp")