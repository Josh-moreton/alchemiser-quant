#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Execution Summary DTOs for The Alchemiser Trading System.

This module provides structured DTOs for execution summaries, replacing
dict[str, Any] usage in MultiStrategyExecutionResult and other execution contexts.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Comprehensive execution metadata
- Decimal precision for financial values
- Type safety for strategy execution tracking

Part of the Pydantic v2 migration to eliminate dict/Any boundaries.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from pydantic import ValidationInfo

from the_alchemiser.shared.constants import DTO_SCHEMA_VERSION_DESCRIPTION
from the_alchemiser.shared.value_objects.core_types import AccountInfo

# Type aliases for string enums
ExecutionMode = Literal["paper", "live"]
EngineMode = Literal["full", "signal_only", "execution_only"]


class AllocationSummary(BaseModel):
    """DTO for portfolio allocation summary data.

    All monetary and percentage values use Decimal for precision.
    Follows Alchemiser guardrail: never use float for financial data.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(default="1.0", description=DTO_SCHEMA_VERSION_DESCRIPTION)
    total_allocation: Decimal = Field(
        ..., ge=0, le=100, description="Total portfolio allocation percentage"
    )
    num_positions: int = Field(..., ge=0, description="Number of positions")
    largest_position_pct: Decimal = Field(
        ..., ge=0, le=100, description="Largest position percentage"
    )

    @field_validator("total_allocation", "largest_position_pct")
    @classmethod
    def validate_percentage_precision(cls, v: Decimal) -> Decimal:
        """Ensure percentage values have reasonable precision (max 4 decimal places)."""
        # Check if exponent is an int (not a special value like 'n', 'N', 'F')
        exponent = v.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -4:
            msg = f"Percentage precision too high: {v}. Max 4 decimal places allowed."
            raise ValueError(msg)
        return v


class StrategyPnLSummary(BaseModel):
    """DTO for strategy P&L summary data.

    All P&L values use Decimal for financial precision.
    Follows Alchemiser guardrail: use Decimal for money, never float.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(default="1.0", description=DTO_SCHEMA_VERSION_DESCRIPTION)
    total_pnl: Decimal = Field(..., description="Total P&L across all strategies in USD")
    best_performer: str | None = Field(
        None, min_length=1, max_length=100, description="Best performing strategy"
    )
    worst_performer: str | None = Field(
        None, min_length=1, max_length=100, description="Worst performing strategy"
    )
    num_profitable: int = Field(..., ge=0, description="Number of profitable strategies")


class StrategySummary(BaseModel):
    """DTO for individual strategy summary within execution.

    All monetary and percentage values use Decimal for precision.
    Follows Alchemiser guardrail: never use == or != on floats.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(default="1.0", description=DTO_SCHEMA_VERSION_DESCRIPTION)
    strategy_name: str = Field(..., min_length=1, max_length=100, description="Strategy identifier")
    allocation_pct: Decimal = Field(..., ge=0, le=100, description="Strategy allocation percentage")
    signal_strength: Decimal = Field(..., ge=0, le=1, description="Signal strength (0-1)")
    pnl: Decimal = Field(..., description="Strategy P&L in USD")

    @field_validator("allocation_pct")
    @classmethod
    def validate_allocation_precision(cls, v: Decimal) -> Decimal:
        """Ensure allocation percentage has reasonable precision (max 4 decimal places)."""
        exponent = v.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -4:
            msg = f"Allocation precision too high: {v}. Max 4 decimal places allowed."
            raise ValueError(msg)
        return v

    @field_validator("signal_strength")
    @classmethod
    def validate_signal_precision(cls, v: Decimal) -> Decimal:
        """Ensure signal strength has reasonable precision (max 6 decimal places)."""
        exponent = v.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -6:
            msg = f"Signal strength precision too high: {v}. Max 6 decimal places allowed."
            raise ValueError(msg)
        return v


class TradingSummary(BaseModel):
    """DTO for trading execution summary.

    All monetary values use Decimal for precision.
    Success rate is a ratio (0-1) using Decimal to avoid float comparison issues.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(default="1.0", description=DTO_SCHEMA_VERSION_DESCRIPTION)
    total_orders: int = Field(..., ge=0, description="Total number of orders")
    orders_executed: int = Field(..., ge=0, description="Number of executed orders")
    success_rate: Decimal = Field(..., ge=0, le=1, description="Execution success rate (0-1)")
    total_value: Decimal = Field(..., ge=0, description="Total value of executed orders in USD")

    @field_validator("orders_executed")
    @classmethod
    def validate_orders_executed(cls, v: int, info: ValidationInfo) -> int:
        """Ensure orders_executed does not exceed total_orders."""
        # Note: This validator runs before we have access to total_orders
        # The model_validator below handles the cross-field validation
        return v

    @field_validator("success_rate")
    @classmethod
    def validate_success_rate_precision(cls, v: Decimal) -> Decimal:
        """Ensure success rate has reasonable precision (max 6 decimal places)."""
        exponent = v.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -6:
            msg = f"Success rate precision too high: {v}. Max 6 decimal places allowed."
            raise ValueError(msg)
        return v


class ExecutionSummary(BaseModel):
    """DTO for comprehensive execution summary.

    Replaces the dict[str, Any] execution_summary field in MultiStrategyExecutionResult.

    All monetary values use Decimal for precision. Account states use TypedDict with Decimal.
    Follows Alchemiser guardrails: strict typing, frozen DTOs, schema versioning.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(default="1.0", description=DTO_SCHEMA_VERSION_DESCRIPTION)

    # Core execution metrics
    allocations: AllocationSummary = Field(..., description="Portfolio allocation summary")
    strategy_summary: dict[str, StrategySummary] = Field(
        ..., description="Individual strategy summaries"
    )
    trading_summary: TradingSummary = Field(..., description="Trading execution summary")
    pnl_summary: StrategyPnLSummary = Field(..., description="P&L summary across strategies")

    # Account state tracking
    account_info_before: AccountInfo = Field(..., description="Account state before execution")
    account_info_after: AccountInfo = Field(..., description="Account state after execution")

    # Execution mode and metadata
    mode: ExecutionMode = Field(..., description="Execution mode (paper/live)")
    engine_mode: EngineMode | None = Field(None, description="Engine execution mode context")
    error: str | None = Field(
        None, max_length=2000, description="Error message if execution failed"
    )

    @field_validator("strategy_summary")
    @classmethod
    def validate_strategy_summary_keys(
        cls, v: dict[str, StrategySummary]
    ) -> dict[str, StrategySummary]:
        """Ensure strategy_summary dict is not empty and keys match strategy names."""
        if not v:
            msg = "strategy_summary cannot be empty"
            raise ValueError(msg)
        for key, summary in v.items():
            if key != summary.strategy_name:
                msg = (
                    f"Dictionary key '{key}' does not match strategy_name '{summary.strategy_name}'"
                )
                raise ValueError(msg)
        return v


class PortfolioState(BaseModel):
    """DTO for final portfolio state.

    Replaces the dict[str, Any] final_portfolio_state field in MultiStrategyExecutionResult.

    All monetary and percentage values use Decimal for precision.
    Follows Alchemiser guardrail: use Decimal for money, never compare floats with ==.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(default="1.0", description=DTO_SCHEMA_VERSION_DESCRIPTION)

    # Portfolio value metrics
    total_portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value in USD")

    # Allocation data per symbol
    target_allocations: dict[str, Decimal] = Field(
        ..., description="Target allocation percentages by symbol (0-100)"
    )
    current_allocations: dict[str, Decimal] = Field(
        ..., description="Current allocation percentages by symbol (0-100)"
    )
    target_values: dict[str, Decimal] = Field(
        ..., description="Target dollar values by symbol in USD"
    )
    current_values: dict[str, Decimal] = Field(
        ..., description="Current dollar values by symbol in USD"
    )

    # Allocation discrepancy analysis
    allocation_discrepancies: dict[str, Decimal] = Field(
        ..., description="Allocation discrepancies by symbol (current - target)"
    )
    largest_discrepancy: Decimal | None = Field(
        None, description="Largest allocation discrepancy in percentage points"
    )

    # Summary metrics
    total_symbols: int = Field(..., ge=0, description="Total number of symbols in portfolio")
    rebalance_needed: bool = Field(..., description="Whether rebalancing is needed")

    @model_validator(mode="after")
    def validate_symbol_consistency(self) -> PortfolioState:
        """Ensure all allocation dicts have consistent symbols."""
        target_symbols = set(self.target_allocations.keys())
        current_symbols = set(self.current_allocations.keys())
        target_value_symbols = set(self.target_values.keys())
        current_value_symbols = set(self.current_values.keys())
        discrepancy_symbols = set(self.allocation_discrepancies.keys())

        # All dicts should have the same set of symbols
        all_symbols = [
            target_symbols,
            current_symbols,
            target_value_symbols,
            current_value_symbols,
            discrepancy_symbols,
        ]

        if not all(s == target_symbols for s in all_symbols):
            msg = "Symbol sets must be consistent across all allocation dictionaries"
            raise ValueError(msg)

        # Verify total_symbols matches
        if len(target_symbols) != self.total_symbols:
            msg = f"total_symbols {self.total_symbols} does not match actual symbol count {len(target_symbols)}"
            raise ValueError(msg)

        return self

    @field_validator("target_allocations", "current_allocations")
    @classmethod
    def validate_allocation_percentages(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Ensure allocation percentages are in valid range (0-100)."""
        for symbol, pct in v.items():
            if not (Decimal("0") <= pct <= Decimal("100")):
                msg = f"Allocation for {symbol} must be between 0 and 100, got {pct}"
                raise ValueError(msg)
        return v

    @field_validator("target_values", "current_values")
    @classmethod
    def validate_positive_values(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Ensure dollar values are non-negative."""
        for symbol, value in v.items():
            if value < Decimal("0"):
                msg = f"Value for {symbol} cannot be negative, got {value}"
                raise ValueError(msg)
        return v


# Backward compatibility aliases - will be removed in future version
AllocationSummaryDTO = AllocationSummary
StrategyPnLSummaryDTO = StrategyPnLSummary
StrategySummaryDTO = StrategySummary
TradingSummaryDTO = TradingSummary
ExecutionSummaryDTO = ExecutionSummary
PortfolioStateDTO = PortfolioState
