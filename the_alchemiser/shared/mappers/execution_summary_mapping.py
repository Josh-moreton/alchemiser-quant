#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Mapping functions for execution summary DTOs.

This module provides mapping utilities to convert between dict structures
and TradeExecutionSummary/PortfolioSnapshot, supporting the migration from
Any/dict types to structured DTOs.

Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.shared.schemas.execution.execution_summary import (
    AllocationSummary,
    ExecutionSummary,
    StrategyPnLSummary,
    StrategySummary,
    TradingSummary,
)
from the_alchemiser.shared.schemas.portfolio.state import PortfolioSnapshot


def dict_to_allocation_summary_dto(data: dict[str, Any]) -> AllocationSummary:
    """Convert allocation summary dict to AllocationSummary."""
    return AllocationSummary(
        total_allocation=Decimal(str(data.get("total_allocation", 0.0))),
        num_positions=data.get("num_positions", 0),
        largest_position_pct=Decimal(str(data.get("largest_position_pct", 0.0))),
    )


def dict_to_strategy_pnl_summary_dto(data: dict[str, Any]) -> StrategyPnLSummary:
    """Convert strategy P&L summary dict to StrategyPnLSummary."""
    return StrategyPnLSummary(
        total_pnl=Decimal(str(data.get("total_pnl", 0.0))),
        best_performer=data.get("best_performer"),
        worst_performer=data.get("worst_performer"),
        num_profitable=data.get("num_profitable", 0),
    )


def dict_to_strategy_summary_dto(data: dict[str, Any]) -> StrategySummary:
    """Convert individual strategy summary dict to StrategySummary."""
    return StrategySummary(
        strategy_name=data.get("strategy_name", "unknown"),
        allocation_pct=Decimal(str(data.get("allocation_pct", 0.0))),
        signal_strength=Decimal(str(data.get("signal_strength", 0.0))),
        pnl=Decimal(str(data.get("pnl", 0.0))),
    )


def dict_to_trading_summary_dto(data: dict[str, Any]) -> TradingSummary:
    """Convert trading summary dict to TradingSummary."""
    return TradingSummary(
        total_orders=data.get("total_orders", 0),
        orders_executed=data.get("orders_executed", 0),
        success_rate=Decimal(str(data.get("success_rate", 0.0))),
        total_value=Decimal(str(data.get("total_value", 0.0))),
    )


def dict_to_execution_summary_dto(data: dict[str, Any]) -> ExecutionSummary:
    """Convert execution summary dict to ExecutionSummary."""
    # Handle allocation summary
    allocations_data = data.get("allocations", {})
    allocations = dict_to_allocation_summary_dto(allocations_data)

    # Handle strategy summaries
    strategy_summary_data = data.get("strategy_summary", {})
    strategy_summary = {}
    for strategy_name, strategy_data in strategy_summary_data.items():
        if isinstance(strategy_data, dict):
            # Ensure strategy_name is in the data
            strategy_data_with_name = {**strategy_data, "strategy_name": strategy_name}
            strategy_summary[strategy_name] = dict_to_strategy_summary_dto(
                strategy_data_with_name
            )

    # Handle trading summary
    trading_summary_data = data.get("trading_summary", {})
    trading_summary = dict_to_trading_summary_dto(trading_summary_data)

    # Handle P&L summary
    pnl_summary_data = data.get("pnl_summary", {})
    pnl_summary = dict_to_strategy_pnl_summary_dto(pnl_summary_data)

    # Extract account info (should already be proper AccountInfo types)
    account_info_before = data.get("account_info_before", {})
    account_info_after = data.get("account_info_after", {})

    return ExecutionSummary(
        allocations=allocations,
        strategy_summary=strategy_summary,
        trading_summary=trading_summary,
        pnl_summary=pnl_summary,
        account_info_before=account_info_before,
        account_info_after=account_info_after,
        mode=data.get("mode", "unknown"),
        engine_mode=data.get("engine_mode"),
        error=data.get("error"),
    )


def dict_to_portfolio_state_dto(data: dict[str, Any]) -> PortfolioSnapshot:
    """Convert portfolio state dict to PortfolioSnapshot.

    Maps from actual portfolio data structure (from build_portfolio_state_data)
    to the required PortfolioSnapshot schema.
    """
    from datetime import UTC, datetime

    from the_alchemiser.shared.schemas.portfolio.state import PortfolioMetrics

    # Generate required correlation fields
    correlation_id = f"portfolio_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

    # Extract portfolio value from allocations data
    portfolio_value = Decimal("0")
    allocations_data = data.get("allocations", {})

    if allocations_data:
        # Sum up current values from allocations
        total_current_value = sum(
            alloc.get("current_value", 0) for alloc in allocations_data.values()
        )
        portfolio_value = Decimal(str(total_current_value))

    # Create portfolio metrics from available data
    metrics = PortfolioMetrics(
        total_value=portfolio_value,
        cash_value=Decimal("0"),  # Not available in current data structure
        equity_value=portfolio_value,
        buying_power=portfolio_value,  # Assume full value as buying power
        day_pnl=Decimal("0"),  # Not calculated in current data structure
        day_pnl_percent=Decimal("0"),
        total_pnl=Decimal("0"),
        total_pnl_percent=Decimal("0"),
    )

    return PortfolioSnapshot(
        correlation_id=correlation_id,
        causation_id=correlation_id,
        timestamp=datetime.now(UTC),
        portfolio_id="main_portfolio",
        metrics=metrics,
    )


def allocation_comparison_to_dict(
    allocation_comparison: dict[str, Any] | AllocationSummary,
) -> dict[str, Any]:
    """Convert allocation comparison DTO to dictionary format.

    Args:
        allocation_comparison: Allocation comparison DTO or dictionary object

    Returns:
        Dictionary with target_values, current_values, and deltas keys

    """
    # Handle case where allocation_comparison is already a dict
    if isinstance(allocation_comparison, dict):
        return allocation_comparison

    # Handle DTO objects with attributes
    try:
        return {
            "target_values": getattr(allocation_comparison, "target_values", {}),
            "current_values": getattr(allocation_comparison, "current_values", {}),
            "deltas": getattr(allocation_comparison, "deltas", {}),
        }
    except Exception:
        # Fallback for unexpected types
        return {
            "target_values": {},
            "current_values": {},
            "deltas": {},
        }
