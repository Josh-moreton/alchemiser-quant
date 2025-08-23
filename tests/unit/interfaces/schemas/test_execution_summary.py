#!/usr/bin/env python3
"""
Test execution summary DTOs and mapping functions.
"""

import pytest
from decimal import Decimal

from the_alchemiser.interfaces.schemas.execution_summary import (
    ExecutionSummaryDTO,
    PortfolioStateDTO,
    AllocationSummaryDTO,
    StrategySummaryDTO,
    TradingSummaryDTO,
    StrategyPnLSummaryDTO,
)
from the_alchemiser.application.mapping.execution_summary_mapping import (
    dict_to_execution_summary_dto,
    dict_to_portfolio_state_dto,
    safe_dict_to_execution_summary_dto,
    safe_dict_to_portfolio_state_dto,
)


def test_allocation_summary_dto_creation():
    """Test AllocationSummaryDTO validation."""
    dto = AllocationSummaryDTO(
        total_allocation=Decimal("95.5"),
        num_positions=3,
        largest_position_pct=Decimal("45.2"),
    )
    assert dto.total_allocation == Decimal("95.5")
    assert dto.num_positions == 3
    assert dto.largest_position_pct == Decimal("45.2")


def test_execution_summary_dto_mapping():
    """Test mapping dict to ExecutionSummaryDTO."""
    # Create complete AccountInfo structures
    account_before = {
        "account_id": "test_account",
        "equity": 100000.0,
        "cash": 10000.0,
        "buying_power": 200000.0,
        "day_trades_remaining": 3,
        "portfolio_value": 100000.0,
        "last_equity": 99500.0,
        "daytrading_buying_power": 200000.0,
        "regt_buying_power": 100000.0,
        "status": "ACTIVE",
    }
    
    account_after = {
        "account_id": "test_account",
        "equity": 101250.25,
        "cash": 11250.25,
        "buying_power": 202500.5,
        "day_trades_remaining": 3,
        "portfolio_value": 101250.25,
        "last_equity": 100000.0,
        "daytrading_buying_power": 202500.5,
        "regt_buying_power": 101250.25,
        "status": "ACTIVE",
    }

    data = {
        "allocations": {
            "total_allocation": 98.5,
            "num_positions": 2,
            "largest_position_pct": 55.0,
        },
        "strategy_summary": {
            "NUCLEAR": {
                "allocation_pct": 30.0,
                "signal_strength": 0.8,
                "pnl": 1500.50,
            },
            "TECL": {
                "allocation_pct": 60.0,
                "signal_strength": 0.6,
                "pnl": -250.25,
            },
        },
        "trading_summary": {
            "total_orders": 5,
            "orders_executed": 4,
            "success_rate": 0.8,
            "total_value": 10000.0,
        },
        "pnl_summary": {
            "total_pnl": 1250.25,
            "best_performer": "NUCLEAR",
            "worst_performer": "TECL",
            "num_profitable": 1,
        },
        "account_info_before": account_before,
        "account_info_after": account_after,
        "mode": "paper",
        "engine_mode": "test",
    }

    dto = dict_to_execution_summary_dto(data)
    
    assert dto.mode == "paper"
    assert dto.engine_mode == "test"
    assert dto.allocations.total_allocation == Decimal("98.5")
    assert dto.allocations.num_positions == 2
    assert "NUCLEAR" in dto.strategy_summary
    assert "TECL" in dto.strategy_summary
    assert dto.strategy_summary["NUCLEAR"].strategy_name == "NUCLEAR"
    assert dto.strategy_summary["NUCLEAR"].allocation_pct == Decimal("30.0")
    assert dto.trading_summary.total_orders == 5
    assert dto.trading_summary.success_rate == Decimal("0.8")
    assert dto.pnl_summary.total_pnl == Decimal("1250.25")
    assert dto.pnl_summary.best_performer == "NUCLEAR"


def test_portfolio_state_dto_mapping():
    """Test mapping dict to PortfolioStateDTO."""
    data = {
        "total_portfolio_value": 100000.0,
        "target_allocations": {"AAPL": 0.4, "TSLA": 0.6},
        "current_allocations": {"AAPL": 0.35, "TSLA": 0.65},
        "target_values": {"AAPL": 40000.0, "TSLA": 60000.0},
        "current_values": {"AAPL": 35000.0, "TSLA": 65000.0},
        "allocation_discrepancies": {"AAPL": -0.05, "TSLA": 0.05},
        "largest_discrepancy": 0.05,
        "total_symbols": 2,
        "rebalance_needed": True,
    }

    dto = dict_to_portfolio_state_dto(data)
    
    assert dto.total_portfolio_value == Decimal("100000.0")
    assert dto.target_allocations["AAPL"] == Decimal("0.4")
    assert dto.current_allocations["TSLA"] == Decimal("0.65")
    assert dto.largest_discrepancy == Decimal("0.05")
    assert dto.total_symbols == 2
    assert dto.rebalance_needed is True


def test_safe_execution_summary_dto_with_invalid_data():
    """Test safe mapping with invalid data."""
    invalid_data = {"invalid": "data"}
    
    dto = safe_dict_to_execution_summary_dto(invalid_data)
    
    assert dto.mode == "error"
    assert dto.error is not None
    assert "Failed to parse execution summary" in dto.error
    assert dto.allocations.total_allocation == Decimal("0")
    assert dto.trading_summary.total_orders == 0


def test_safe_portfolio_state_dto_with_none():
    """Test safe mapping with None data."""
    dto = safe_dict_to_portfolio_state_dto(None)
    assert dto is None


def test_safe_portfolio_state_dto_with_invalid_data():
    """Test safe mapping with invalid portfolio data."""
    invalid_data = {"bad": "data"}
    
    dto = safe_dict_to_portfolio_state_dto(invalid_data)
    
    assert dto is not None
    assert dto.total_portfolio_value == Decimal("0")
    assert dto.total_symbols == 0
    assert dto.rebalance_needed is False