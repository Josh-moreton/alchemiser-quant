#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Signal analysis data transfer objects for orchestration module.

Provides typed DTOs for signal analysis results that replace dict[str, Any]
usage in signal orchestration business logic methods.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class StrategySignalResultDTO(BaseModel):
    """DTO for individual strategy signal result."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, description="Signal symbol or symbol list")
    symbols: list[str] | None = Field(
        default=None, description="Individual symbols for multi-symbol strategies"
    )
    action: str = Field(..., min_length=1, description="Signal action (BUY/SELL/HOLD)")
    confidence: Decimal = Field(..., ge=0, le=1, description="Signal confidence")
    reasoning: str = Field(..., min_length=1, description="Signal reasoning")
    is_multi_symbol: bool = Field(default=False, description="Whether signal covers multiple symbols")


class SignalAnalysisResultDTO(BaseModel):
    """DTO for complete signal analysis results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    strategy_signals: dict[str, StrategySignalResultDTO] = Field(
        ..., description="Signals by strategy type"
    )
    consolidated_portfolio: dict[str, Decimal] = Field(
        ..., description="Consolidated portfolio allocations"
    )
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="When analysis was performed"
    )
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracking")
    signal_quality_passed: bool = Field(
        default=True, description="Whether signals passed quality validation"
    )


class RebalancingPlanResultDTO(BaseModel):
    """DTO for rebalancing plan generation results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    plan: "RebalancePlanDTO" = Field(..., description="The rebalancing plan DTO")  # Forward reference
    trade_count: int = Field(..., ge=0, description="Number of trades in plan")
    total_trade_value: Decimal = Field(..., ge=0, description="Total value of trades")
    target_allocations: dict[str, Decimal] = Field(
        ..., description="Target allocations by symbol"
    )
    plan_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="When plan was created"
    )
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracking")