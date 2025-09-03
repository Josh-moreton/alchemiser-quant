from __future__ import annotations

"""Business Unit: shared | Status: current..
"""

#!/usr/bin/env python3
"""Business Unit: shared | Status: current...., ge=0, description="Number of profitable strategies")


class StrategySummary(BaseModel):
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


class TradingSummary(BaseModel):
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


class ExecutionSummary(BaseModel):
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
    mode: str = Field(..., description="Execution mode (paper/live)")
    engine_mode: str | None = Field(None, description="Engine execution mode context")
    error: str | None = Field(None, description="Error message if execution failed")


class PortfolioState(BaseModel):
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


# Backward compatibility aliases - will be removed in future version
AllocationSummaryDTO = AllocationSummary
StrategyPnLSummaryDTO = StrategyPnLSummary
StrategySummaryDTO = StrategySummary
TradingSummaryDTO = TradingSummary
ExecutionSummaryDTO = ExecutionSummary
PortfolioStateDTO = PortfolioState
