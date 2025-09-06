#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Mapping functions for execution summary DTOs.

This module provides mapping utilities to convert between dict structures
and ExecutionSummaryDTO/PortfolioStateDTO, supporting the migration from
Any/dict types to structured DTOs.

Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations


from decimal import Decimal
from typing import Any

from the_alchemiser.execution.core.execution_schemas_summary import (
    AllocationSummaryDTO,
    ExecutionSummaryDTO,
    PortfolioStateDTO,
    StrategyPnLSummaryDTO,
    StrategySummaryDTO,
    TradingSummaryDTO,
)


def dict_to_allocation_summary_dto(data: dict[str, Any]) -> AllocationSummaryDTO:
    """Convert allocation summary dict to AllocationSummaryDTO."""
    return AllocationSummaryDTO(
        total_allocation=Decimal(str(data.get("total_allocation", 0.0))),
        num_positions=data.get("num_positions", 0),
        largest_position_pct=Decimal(str(data.get("largest_position_pct", 0.0))),
    )


def dict_to_strategy_pnl_summary_dto(data: dict[str, Any]) -> StrategyPnLSummaryDTO:
    """Convert strategy P&L summary dict to StrategyPnLSummaryDTO."""
    return StrategyPnLSummaryDTO(
        total_pnl=Decimal(str(data.get("total_pnl", 0.0))),
        best_performer=data.get("best_performer"),
        worst_performer=data.get("worst_performer"),
        num_profitable=data.get("num_profitable", 0),
    )


def dict_to_strategy_summary_dto(data: dict[str, Any]) -> StrategySummaryDTO:
    """Convert individual strategy summary dict to StrategySummaryDTO."""
    return StrategySummaryDTO(
        strategy_name=data.get("strategy_name", "unknown"),
        allocation_pct=Decimal(str(data.get("allocation_pct", 0.0))),
        signal_strength=Decimal(str(data.get("signal_strength", 0.0))),
        pnl=Decimal(str(data.get("pnl", 0.0))),
    )


def dict_to_trading_summary_dto(data: dict[str, Any]) -> TradingSummaryDTO:
    """Convert trading summary dict to TradingSummaryDTO."""
    return TradingSummaryDTO(
        total_orders=data.get("total_orders", 0),
        orders_executed=data.get("orders_executed", 0),
        success_rate=Decimal(str(data.get("success_rate", 0.0))),
        total_value=Decimal(str(data.get("total_value", 0.0))),
    )


def dict_to_execution_summary_dto(data: dict[str, Any]) -> ExecutionSummaryDTO:
    """Convert execution summary dict to ExecutionSummaryDTO."""
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
            strategy_summary[strategy_name] = dict_to_strategy_summary_dto(strategy_data_with_name)

    # Handle trading summary
    trading_summary_data = data.get("trading_summary", {})
    trading_summary = dict_to_trading_summary_dto(trading_summary_data)

    # Handle P&L summary
    pnl_summary_data = data.get("pnl_summary", {})
    pnl_summary = dict_to_strategy_pnl_summary_dto(pnl_summary_data)

    # Extract account info (should already be proper AccountInfo types)
    account_info_before = data.get("account_info_before", {})
    account_info_after = data.get("account_info_after", {})

    return ExecutionSummaryDTO(
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


def dict_to_portfolio_state_dto(data: dict[str, Any]) -> PortfolioStateDTO:
    """Convert portfolio state dict to PortfolioStateDTO."""

    # Convert decimal fields
    def to_decimal_dict(source: dict[str, Any]) -> dict[str, Decimal]:
        return {k: Decimal(str(v)) for k, v in source.items()}

    target_allocations = to_decimal_dict(data.get("target_allocations", {}))
    current_allocations = to_decimal_dict(data.get("current_allocations", {}))
    target_values = to_decimal_dict(data.get("target_values", {}))
    current_values = to_decimal_dict(data.get("current_values", {}))
    allocation_discrepancies = to_decimal_dict(data.get("allocation_discrepancies", {}))

    largest_discrepancy = data.get("largest_discrepancy")
    if largest_discrepancy is not None:
        largest_discrepancy = Decimal(str(largest_discrepancy))

    return PortfolioStateDTO(
        total_portfolio_value=Decimal(str(data.get("total_portfolio_value", 0.0))),
        target_allocations=target_allocations,
        current_allocations=current_allocations,
        target_values=target_values,
        current_values=current_values,
        allocation_discrepancies=allocation_discrepancies,
        largest_discrepancy=largest_discrepancy,
        total_symbols=data.get("total_symbols", 0),
        rebalance_needed=data.get("rebalance_needed", False),
    )


def safe_dict_to_execution_summary_dto(data: dict[str, Any]) -> ExecutionSummaryDTO:
    """Safely convert execution summary dict to DTO with fallbacks.

    Provides backward compatibility for incomplete dict structures.
    """
    try:
        return dict_to_execution_summary_dto(data)
    except (KeyError, ValueError, TypeError) as e:
        # Create minimal AccountInfo for fallback
        default_account_info = {
            "account_id": "error",
            "equity": 0.0,
            "cash": 0.0,
            "buying_power": 0.0,
            "day_trades_remaining": 0,
            "portfolio_value": 0.0,
            "last_equity": 0.0,
            "daytrading_buying_power": 0.0,
            "regt_buying_power": 0.0,
            "status": "INACTIVE",
        }

        # Create minimal fallback DTO for error cases
        return ExecutionSummaryDTO(
            allocations=AllocationSummaryDTO(
                total_allocation=Decimal("0"),
                num_positions=0,
                largest_position_pct=Decimal("0"),
            ),
            strategy_summary={},
            trading_summary=TradingSummaryDTO(
                total_orders=0,
                orders_executed=0,
                success_rate=Decimal("0"),
                total_value=Decimal("0"),
            ),
            pnl_summary=StrategyPnLSummaryDTO(
                total_pnl=Decimal("0"),
                best_performer=None,
                worst_performer=None,
                num_profitable=0,
            ),
            account_info_before=data.get("account_info_before", default_account_info),
            account_info_after=data.get("account_info_after", default_account_info),
            mode=data.get("mode", "error"),
            engine_mode=data.get("engine_mode"),
            error=f"Failed to parse execution summary: {e}",
        )


def safe_dict_to_portfolio_state_dto(data: dict[str, Any] | None) -> PortfolioStateDTO | None:
    """Safely convert portfolio state dict to DTO with fallbacks.

    Returns None if data is None or invalid.
    """
    if data is None:
        return None

    try:
        return dict_to_portfolio_state_dto(data)
    except (KeyError, ValueError, TypeError):
        # Return minimal empty portfolio state for error cases
        return PortfolioStateDTO(
            total_portfolio_value=Decimal("0"),
            target_allocations={},
            current_allocations={},
            target_values={},
            current_values={},
            allocation_discrepancies={},
            largest_discrepancy=None,
            total_symbols=0,
            rebalance_needed=False,
        )
