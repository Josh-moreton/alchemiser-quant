#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Mapping functions for execution summary DTOs.

This module provides mapping utilities to convert between dict structures
and ExecutionSummary/PortfolioState, supporting the migration from
Any/dict types to structured DTOs.

Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.execution_summary import (
    AllocationSummary as AllocationSummary,
)
from the_alchemiser.shared.schemas.execution_summary import (
    ExecutionSummary as ExecutionSummary,
)
from the_alchemiser.shared.schemas.execution_summary import (
    StrategyPnLSummary as StrategyPnLSummary,
)
from the_alchemiser.shared.schemas.execution_summary import (
    StrategySummary as StrategySummary,
)
from the_alchemiser.shared.schemas.execution_summary import (
    TradingSummary as TradingSummary,
)
from the_alchemiser.shared.schemas.portfolio_state import (
    PortfolioMetrics,
    PortfolioState,
)

# Module logger for observability
logger = get_logger(__name__)

# Constants for default values
UNKNOWN_STRATEGY = "unknown"
DEFAULT_PORTFOLIO_ID = "main_portfolio"
ZERO_DECIMAL = Decimal("0")

# Exported API
__all__ = [
    "dict_to_allocation_summary",
    "dict_to_execution_summary",
    "dict_to_portfolio_state",
    "dict_to_strategy_pnl_summary",
    "dict_to_strategy_summary",
    "dict_to_trading_summary",
]


def dict_to_allocation_summary(data: dict[str, Any]) -> AllocationSummary:
    """Convert allocation summary dict to AllocationSummary.

    Args:
        data: Dictionary containing allocation summary fields:
            - total_allocation: float/Decimal/str, percentage (0-100)
            - num_positions: int, number of positions
            - largest_position_pct: float/Decimal/str, percentage (0-100)

    Returns:
        AllocationSummary DTO instance

    Raises:
        TypeError: If data is not a dictionary
        ValidationError: If data fails DTO validation

    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict for AllocationSummary, got {type(data).__name__}")

    # Safe extraction with None checks for Decimal conversion
    total_allocation = data.get("total_allocation")
    largest_position_pct = data.get("largest_position_pct")

    return AllocationSummary(
        total_allocation=(
            Decimal(str(total_allocation)) if total_allocation is not None else ZERO_DECIMAL
        ),
        num_positions=data.get("num_positions", 0),
        largest_position_pct=(
            Decimal(str(largest_position_pct)) if largest_position_pct is not None else ZERO_DECIMAL
        ),
    )


def dict_to_strategy_pnl_summary(data: dict[str, Any]) -> StrategyPnLSummary:
    """Convert strategy P&L summary dict to StrategyPnLSummary.

    Args:
        data: Dictionary containing P&L summary fields:
            - total_pnl: float/Decimal/str, total P&L in USD
            - best_performer: str | None, best performing strategy name
            - worst_performer: str | None, worst performing strategy name
            - num_profitable: int, number of profitable strategies

    Returns:
        StrategyPnLSummary DTO instance

    Raises:
        TypeError: If data is not a dictionary
        ValidationError: If data fails DTO validation

    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict for StrategyPnLSummary, got {type(data).__name__}")

    total_pnl = data.get("total_pnl")

    return StrategyPnLSummary(
        total_pnl=Decimal(str(total_pnl)) if total_pnl is not None else ZERO_DECIMAL,
        best_performer=data.get("best_performer"),
        worst_performer=data.get("worst_performer"),
        num_profitable=data.get("num_profitable", 0),
    )


def dict_to_strategy_summary(data: dict[str, Any]) -> StrategySummary:
    """Convert individual strategy summary dict to StrategySummary.

    Args:
        data: Dictionary containing strategy summary fields:
            - strategy_name: str, strategy identifier
            - allocation_pct: float/Decimal/str, allocation percentage (0-100)
            - signal_strength: float/Decimal/str, signal strength (0-1)
            - pnl: float/Decimal/str, P&L in USD

    Returns:
        StrategySummary DTO instance

    Raises:
        TypeError: If data is not a dictionary
        ValidationError: If data fails DTO validation

    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict for StrategySummary, got {type(data).__name__}")

    allocation_pct = data.get("allocation_pct")
    signal_strength = data.get("signal_strength")
    pnl = data.get("pnl")

    return StrategySummary(
        strategy_name=data.get("strategy_name", UNKNOWN_STRATEGY),
        allocation_pct=(
            Decimal(str(allocation_pct)) if allocation_pct is not None else ZERO_DECIMAL
        ),
        signal_strength=(
            Decimal(str(signal_strength)) if signal_strength is not None else ZERO_DECIMAL
        ),
        pnl=Decimal(str(pnl)) if pnl is not None else ZERO_DECIMAL,
    )


def dict_to_trading_summary(data: dict[str, Any]) -> TradingSummary:
    """Convert trading summary dict to TradingSummary.

    Args:
        data: Dictionary containing trading summary fields:
            - total_orders: int, total number of orders
            - orders_executed: int, number of executed orders
            - success_rate: float/Decimal/str, success rate (0-1)
            - total_value: float/Decimal/str, total value in USD

    Returns:
        TradingSummary DTO instance

    Raises:
        TypeError: If data is not a dictionary
        ValidationError: If data fails DTO validation

    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict for TradingSummary, got {type(data).__name__}")

    success_rate = data.get("success_rate")
    total_value = data.get("total_value")

    return TradingSummary(
        total_orders=data.get("total_orders", 0),
        orders_executed=data.get("orders_executed", 0),
        success_rate=Decimal(str(success_rate)) if success_rate is not None else ZERO_DECIMAL,
        total_value=Decimal(str(total_value)) if total_value is not None else ZERO_DECIMAL,
    )


def dict_to_execution_summary(
    data: dict[str, Any],
    correlation_id: str | None = None,
) -> ExecutionSummary:
    """Convert execution summary dict to ExecutionSummary.

    Args:
        data: Dictionary containing execution summary fields:
            - allocations: dict, allocation summary data
            - strategy_summary: dict[str, dict], strategy summaries by name
            - trading_summary: dict, trading execution summary
            - pnl_summary: dict, P&L summary data
            - account_info_before: AccountInfo, account state before execution
            - account_info_after: AccountInfo, account state after execution
            - mode: Literal["paper", "live"], execution mode
            - engine_mode: Literal["full", "signal_only", "execution_only"] | None
            - error: str | None, error message if execution failed
        correlation_id: Optional correlation ID for tracing

    Returns:
        ExecutionSummary DTO instance

    Raises:
        TypeError: If data is not a dictionary or account_info fields are invalid
        ValidationError: If data fails DTO validation
        ValueError: If mode is invalid or required fields are missing

    """
    if not isinstance(data, dict):
        logger.error(
            "dict_to_execution_summary_type_error",
            correlation_id=correlation_id,
            actual_type=type(data).__name__,
        )
        raise TypeError(f"Expected dict for ExecutionSummary, got {type(data).__name__}")

    try:
        # Handle allocation summary
        allocations_data = data.get("allocations", {})
        if not isinstance(allocations_data, dict):
            raise TypeError("allocations must be a dict")
        allocations = dict_to_allocation_summary(allocations_data)

        # Handle strategy summaries
        strategy_summary_data = data.get("strategy_summary", {})
        if not isinstance(strategy_summary_data, dict):
            raise TypeError("strategy_summary must be a dict")

        strategy_summary = {}
        for strategy_name, strategy_data in strategy_summary_data.items():
            if isinstance(strategy_data, dict):
                # Ensure strategy_name is in the data
                strategy_data_with_name = {**strategy_data, "strategy_name": strategy_name}
                strategy_summary[strategy_name] = dict_to_strategy_summary(strategy_data_with_name)
            else:
                logger.warning(
                    "dict_to_execution_summary_skipped_non_dict_strategy",
                    correlation_id=correlation_id,
                    strategy_name=strategy_name,
                    actual_type=type(strategy_data).__name__,
                )

        # Handle trading summary
        trading_summary_data = data.get("trading_summary", {})
        if not isinstance(trading_summary_data, dict):
            raise TypeError("trading_summary must be a dict")
        trading_summary = dict_to_trading_summary(trading_summary_data)

        # Handle P&L summary
        pnl_summary_data = data.get("pnl_summary", {})
        if not isinstance(pnl_summary_data, dict):
            raise TypeError("pnl_summary must be a dict")
        pnl_summary = dict_to_strategy_pnl_summary(pnl_summary_data)

        # Extract and validate account info
        account_info_before = data.get("account_info_before")
        account_info_after = data.get("account_info_after")

        if not isinstance(account_info_before, dict):
            raise TypeError("account_info_before must be a dict")
        if not isinstance(account_info_after, dict):
            raise TypeError("account_info_after must be a dict")

        # Validate mode field - must be "paper" or "live"
        mode = data.get("mode")
        if mode not in ("paper", "live"):
            logger.error(
                "dict_to_execution_summary_invalid_mode",
                correlation_id=correlation_id,
                mode=mode,
            )
            raise ValueError(f"Invalid execution mode: {mode}. Must be 'paper' or 'live'.")

        summary = ExecutionSummary(
            allocations=allocations,
            strategy_summary=strategy_summary,
            trading_summary=trading_summary,
            pnl_summary=pnl_summary,
            account_info_before=account_info_before,  # type: ignore[arg-type]
            account_info_after=account_info_after,  # type: ignore[arg-type]
            mode=mode,  # type: ignore[arg-type]
            engine_mode=data.get("engine_mode"),
            error=data.get("error"),
        )

        logger.info(
            "execution_summary_mapped",
            correlation_id=correlation_id,
            num_strategies=len(strategy_summary),
            mode=mode,
        )

        return summary

    except (TypeError, ValueError) as e:
        logger.error(
            "execution_summary_mapping_failed",
            correlation_id=correlation_id,
            error_type=type(e).__name__,
            error_message=str(e),
            input_keys=list(data.keys()) if isinstance(data, dict) else None,
        )
        raise


def dict_to_portfolio_state(
    data: dict[str, Any],
    correlation_id: str,
    causation_id: str | None = None,
    timestamp: datetime | None = None,
) -> PortfolioState:
    """Convert portfolio state dict to PortfolioState.

    Maps from actual portfolio data structure (from build_portfolio_state_data)
    to the required PortfolioState schema.

    Args:
        data: Portfolio data dictionary containing:
            - allocations: dict, allocation data by symbol
        correlation_id: Unique correlation identifier for tracing
        causation_id: Optional causation identifier (defaults to correlation_id)
        timestamp: Optional timestamp (defaults to current UTC time)

    Returns:
        PortfolioState DTO instance

    Raises:
        TypeError: If data is not a dictionary
        ValidationError: If data fails DTO validation

    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict for PortfolioState, got {type(data).__name__}")

    # Use provided values or defaults
    causation_id = causation_id or correlation_id
    timestamp = timestamp or datetime.now(UTC)

    # Extract portfolio value from allocations data
    portfolio_value = ZERO_DECIMAL
    allocations_data = data.get("allocations", {})

    if allocations_data and isinstance(allocations_data, dict):
        # Sum up current values from allocations
        total_current_value = sum(
            alloc.get("current_value", 0)
            for alloc in allocations_data.values()
            if isinstance(alloc, dict)
        )
        portfolio_value = Decimal(str(total_current_value))

    # Create portfolio metrics from available data
    metrics = PortfolioMetrics(
        total_value=portfolio_value,
        cash_value=ZERO_DECIMAL,  # Not available in current data structure
        equity_value=portfolio_value,
        buying_power=portfolio_value,  # Assume full value as buying power
        day_pnl=ZERO_DECIMAL,  # Not calculated in current data structure
        day_pnl_percent=ZERO_DECIMAL,
        total_pnl=ZERO_DECIMAL,
        total_pnl_percent=ZERO_DECIMAL,
    )

    return PortfolioState(
        correlation_id=correlation_id,
        causation_id=causation_id,
        timestamp=timestamp,
        portfolio_id=DEFAULT_PORTFOLIO_ID,
        metrics=metrics,
    )
