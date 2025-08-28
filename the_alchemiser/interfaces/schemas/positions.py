#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Position DTOs for The Alchemiser Trading System.

This module contains DTOs for position data, portfolio summaries, and position analytics,
providing type-safe interfaces for position management operations.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Decimal precision for financial values
- Comprehensive field validation and normalization
- Type safety for position lifecycle management
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.interfaces.schemas.base import ResultDTO


class PositionDTO(BaseModel):
    """DTO for individual position information.

    Used when returning position data from TradingSystemCoordinator methods.
    Provides validation and normalization of position parameters.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    quantity: Decimal = Field(..., description="Position quantity")
    average_entry_price: Decimal = Field(..., ge=0, description="Average entry price")
    current_price: Decimal = Field(..., ge=0, description="Current market price")
    market_value: Decimal = Field(..., description="Current market value")
    unrealized_pnl: Decimal = Field(..., description="Unrealized profit/loss")
    unrealized_pnl_percent: Decimal = Field(..., description="Unrealized P&L percentage")


class PositionSummaryDTO(ResultDTO):
    """DTO for position summary with additional context.

    Contains position data plus metadata about the request/response.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    position: PositionDTO | None = None
    error: str | None = None
    # End of file newline ensured below


class PortfolioSummaryDTO(ResultDTO):
    """DTO for overall portfolio summary.

    Aggregated view of all positions and portfolio metrics.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    portfolio: PortfolioMetricsDTO | None = None
    error: str | None = None


class PortfolioMetricsDTO(BaseModel):
    """DTO for portfolio-level metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    total_market_value: Decimal
    cash_balance: Decimal
    total_positions: int
    largest_position_percent: Decimal


class PositionAnalyticsDTO(ResultDTO):
    """DTO for position risk analytics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    risk_metrics: dict[str, Any] | None = None
    error: str | None = None


class PositionMetricsDTO(ResultDTO):
    """DTO for portfolio-wide position metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    diversification_score: Decimal | None = None
    largest_positions: list[LargestPositionDTO] | None = None
    error: str | None = None


class LargestPositionDTO(BaseModel):
    """DTO for largest position information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str
    weight_percent: Decimal
    market_value: Decimal


class ClosePositionResultDTO(ResultDTO):
    """DTO for position closure results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None
    error: str | None = None


class PortfolioValueDTO(BaseModel):
    """DTO for portfolio value information.

    Provides both raw numeric value and typed Money object for portfolio valuation.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    value: Decimal = Field(..., ge=0, description="Raw portfolio value")
    money: Any = Field(..., description="Typed Money object for portfolio value")
