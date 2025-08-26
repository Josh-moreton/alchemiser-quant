#!/usr/bin/env python3
"""Execution Summary DTOs for The Alchemiser Trading System.

This module provides structured DTOs for execution summaries, replacing
dict[str, Any] usage in MultiStrategyExecutionResultDTO and other execution contexts.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Comprehensive execution metadata
- Decimal precision for financial values
- Type safety for strategy execution tracking

Part of the Pydantic v2 migration to eliminate dict/Any boundaries.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.domain.types import AccountInfo


class AllocationSummaryDTO(BaseModel):
    """DTO for portfolio allocation summary data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    total_allocation: Decimal = Field(..., description="Total portfolio allocation percentage")
    num_positions: int = Field(..., ge=0, description="Number of positions")
    largest_position_pct: Decimal = Field(..., ge=0, description="Largest position percentage")


class StrategyPnLSummaryDTO(BaseModel):
    """DTO for strategy P&L summary data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    total_pnl: Decimal = Field(..., description="Total P&L across all strategies")
    best_performer: str | None = Field(None, description="Best performing strategy")
    worst_performer: str | None = Field(None, description="Worst performing strategy")
    num_profitable: int = Field(..., ge=0, description="Number of profitable strategies")


class StrategySummaryDTO(BaseModel):
    """DTO for individual strategy summary within execution."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    strategy_name: str = Field(..., min_length=1, description="Strategy identifier")
    allocation_pct: Decimal = Field(..., ge=0, le=100, description="Strategy allocation percentage")
    signal_strength: Decimal = Field(..., ge=0, le=1, description="Signal strength (0-1)")
    pnl: Decimal = Field(..., description="Strategy P&L")


class TradingSummaryDTO(BaseModel):
    """DTO for trading execution summary."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    total_orders: int = Field(..., ge=0, description="Total number of orders")
    orders_executed: int = Field(..., ge=0, description="Number of executed orders")
    success_rate: Decimal = Field(..., ge=0, le=1, description="Execution success rate (0-1)")
    total_value: Decimal = Field(..., ge=0, description="Total value of executed orders")


class ExecutionSummaryDTO(BaseModel):
    """DTO for comprehensive execution summary.

    Replaces the dict[str, Any] execution_summary field in MultiStrategyExecutionResultDTO.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core execution metrics
    allocations: AllocationSummaryDTO = Field(..., description="Portfolio allocation summary")
    strategy_summary: dict[str, StrategySummaryDTO] = Field(
        ..., description="Individual strategy summaries"
    )
    trading_summary: TradingSummaryDTO = Field(..., description="Trading execution summary")
    pnl_summary: StrategyPnLSummaryDTO = Field(..., description="P&L summary across strategies")

    # Account state tracking
    account_info_before: AccountInfo = Field(..., description="Account state before execution")
    account_info_after: AccountInfo = Field(..., description="Account state after execution")

    # Execution mode and metadata
    mode: str = Field(..., description="Execution mode (paper/live)")
    engine_mode: str | None = Field(None, description="Engine execution mode context")
    error: str | None = Field(None, description="Error message if execution failed")


class PortfolioStateDTO(BaseModel):
    """DTO for final portfolio state.

    Replaces the dict[str, Any] final_portfolio_state field in MultiStrategyExecutionResultDTO.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Portfolio value metrics
    total_portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value")

    # Allocation data per symbol
    target_allocations: dict[str, Decimal] = Field(
        ..., description="Target allocation percentages by symbol"
    )
    current_allocations: dict[str, Decimal] = Field(
        ..., description="Current allocation percentages by symbol"
    )
    target_values: dict[str, Decimal] = Field(..., description="Target dollar values by symbol")
    current_values: dict[str, Decimal] = Field(..., description="Current dollar values by symbol")

    # Allocation discrepancy analysis
    allocation_discrepancies: dict[str, Decimal] = Field(
        ..., description="Allocation discrepancies by symbol (current - target)"
    )
    largest_discrepancy: Decimal | None = Field(None, description="Largest allocation discrepancy")

    # Summary metrics
    total_symbols: int = Field(..., ge=0, description="Total number of symbols in portfolio")
    rebalance_needed: bool = Field(..., description="Whether rebalancing is needed")
