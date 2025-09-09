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

from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioStateDTO
from the_alchemiser.shared.schemas.execution_summary import (
    AllocationSummary as AllocationSummaryDTO,
)
from the_alchemiser.shared.schemas.execution_summary import (
    ExecutionSummary as ExecutionSummaryDTO,
)
from the_alchemiser.shared.schemas.execution_summary import (
    StrategyPnLSummary as StrategyPnLSummaryDTO,
)
from the_alchemiser.shared.schemas.execution_summary import (
    StrategySummary as StrategySummaryDTO,
)
from the_alchemiser.shared.schemas.execution_summary import (
    TradingSummary as TradingSummaryDTO,
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
    from datetime import UTC, datetime
    
    from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioMetricsDTO
    
    # Generate required correlation fields if not present
    correlation_id = data.get("correlation_id", f"portfolio_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}")
    causation_id = data.get("causation_id", correlation_id)
    portfolio_id = data.get("portfolio_id", "main_portfolio")
    
    # Create timestamp if not present
    timestamp = data.get("timestamp")
    if timestamp is None:
        timestamp = datetime.now(UTC)
    elif isinstance(timestamp, str):
        from datetime import datetime as dt
        timestamp = dt.fromisoformat(timestamp.replace("Z", "+00:00"))
    
    # Extract portfolio value from allocations data if present
    portfolio_value = Decimal("0")
    allocations_data = data.get("allocations", {})
    
    if allocations_data:
        # Sum up current values from allocations
        total_current_value = sum(
            alloc.get("current_value", 0) for alloc in allocations_data.values()
        )
        portfolio_value = Decimal(str(total_current_value))
    
    # Create minimal portfolio metrics
    metrics = PortfolioMetricsDTO(
        total_value=portfolio_value,
        cash_value=Decimal(str(data.get("cash_value", 0))),
        equity_value=portfolio_value,
        buying_power=Decimal(str(data.get("buying_power", portfolio_value))),
        day_pnl=Decimal("0"),
        day_pnl_percent=Decimal("0"),
        total_pnl=Decimal("0"),
        total_pnl_percent=Decimal("0"),
    )
    
    return PortfolioStateDTO(
        correlation_id=correlation_id,
        causation_id=causation_id,
        timestamp=timestamp,
        portfolio_id=portfolio_id,
        account_id=data.get("account_id"),
        positions=[],  # Empty positions for now, could be enhanced later
        metrics=metrics,
        strategy_allocations={},  # Empty strategy allocations for now
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
        from datetime import UTC, datetime
        
        from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioMetricsDTO
        
        return PortfolioStateDTO(
            correlation_id=f"fallback_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            causation_id=f"fallback_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(UTC),
            portfolio_id="error_portfolio",
            metrics=PortfolioMetricsDTO(
                total_value=Decimal("0"),
                cash_value=Decimal("0"),
                equity_value=Decimal("0"),
                buying_power=Decimal("0"),
                day_pnl=Decimal("0"),
                day_pnl_percent=Decimal("0"),
                total_pnl=Decimal("0"),
                total_pnl_percent=Decimal("0"),
            ),
        )
