#!/usr/bin/env python3
"""
Test portfolio rebalancing DTOs and mapping functions.
"""

import pytest
from decimal import Decimal

from the_alchemiser.interfaces.schemas.portfolio_rebalancing import (
    RebalancePlanDTO,
    RebalancePlanCollectionDTO,
    RebalancingSummaryDTO,
    RebalancingImpactDTO,
)
from the_alchemiser.application.mapping.portfolio_rebalancing_mapping import (
    rebalancing_summary_dict_to_dto,
    rebalancing_impact_dict_to_dto,
    safe_rebalancing_summary_dict_to_dto,
    safe_rebalancing_impact_dict_to_dto,
)


def test_rebalance_plan_dto_creation():
    """Test RebalancePlanDTO validation."""
    dto = RebalancePlanDTO(
        symbol="AAPL",
        current_weight=Decimal("0.3"),
        target_weight=Decimal("0.4"),
        weight_diff=Decimal("0.1"),
        target_value=Decimal("40000"),
        current_value=Decimal("30000"),
        trade_amount=Decimal("10000"),
        needs_rebalance=True,
        trade_direction="BUY",
        trade_amount_abs=Decimal("10000"),
        weight_change_bps=1000,
    )
    assert dto.symbol == "AAPL"
    assert dto.current_weight == Decimal("0.3")
    assert dto.trade_direction == "BUY"
    assert dto.needs_rebalance is True


def test_rebalancing_summary_dto_mapping():
    """Test mapping dict to RebalancingSummaryDTO."""
    data = {
        "success": True,
        "total_portfolio_value": 100000.0,
        "total_symbols": 5,
        "symbols_needing_rebalance": 3,
        "total_trade_value": 15000.0,
        "largest_trade_symbol": "AAPL",
        "largest_trade_value": 8000.0,
        "rebalance_threshold_pct": 0.05,
        "execution_feasible": True,
        "estimated_costs": 150.0,
    }

    dto = rebalancing_summary_dict_to_dto(data)
    
    assert dto.success is True
    assert dto.total_portfolio_value == Decimal("100000.0")
    assert dto.total_symbols == 5
    assert dto.symbols_needing_rebalance == 3
    assert dto.largest_trade_symbol == "AAPL"
    assert dto.execution_feasible is True


def test_rebalancing_impact_dto_mapping():
    """Test mapping dict to RebalancingImpactDTO."""
    data = {
        "success": True,
        "portfolio_risk_change": 0.02,
        "concentration_risk_change": -0.01,
        "estimated_transaction_costs": 200.0,
        "estimated_slippage": 100.0,
        "total_estimated_costs": 300.0,
        "execution_complexity": "MEDIUM",
        "recommended_execution_time": 30,
        "market_impact_risk": "LOW",
        "net_benefit_estimate": -300.0,
        "recommendation": "EXECUTE",
    }

    dto = rebalancing_impact_dict_to_dto(data)
    
    assert dto.success is True
    assert dto.portfolio_risk_change == Decimal("0.02")
    assert dto.concentration_risk_change == Decimal("-0.01")
    assert dto.execution_complexity == "MEDIUM"
    assert dto.recommended_execution_time == 30
    assert dto.recommendation == "EXECUTE"


def test_safe_rebalancing_summary_dto_with_invalid_data():
    """Test safe mapping with invalid data."""
    # Create data that will actually cause a TypeError in conversion
    invalid_data = {"total_portfolio_value": "not_a_number", "success": "invalid"}
    
    dto = safe_rebalancing_summary_dict_to_dto(invalid_data)
    
    assert dto.success is False
    assert dto.error is not None
    assert "Failed to parse rebalancing summary" in dto.error
    assert dto.total_portfolio_value == Decimal("0")
    assert dto.execution_feasible is False


def test_safe_rebalancing_impact_dto_with_invalid_data():
    """Test safe mapping with invalid data."""
    # Create data that will actually cause a TypeError in conversion  
    invalid_data = {"portfolio_risk_change": "not_a_number", "success": "invalid"}
    
    dto = safe_rebalancing_impact_dict_to_dto(invalid_data)
    
    assert dto.success is False
    assert dto.error is not None
    assert "Failed to parse rebalancing impact" in dto.error
    assert dto.recommendation == "CANCEL"
    assert dto.execution_complexity == "UNKNOWN"


def test_rebalance_plan_collection_dto():
    """Test RebalancePlanCollectionDTO structure."""
    plans = {
        "AAPL": RebalancePlanDTO(
            symbol="AAPL",
            current_weight=Decimal("0.3"),
            target_weight=Decimal("0.4"),
            weight_diff=Decimal("0.1"),
            target_value=Decimal("40000"),
            current_value=Decimal("30000"),
            trade_amount=Decimal("10000"),
            needs_rebalance=True,
            trade_direction="BUY",
            trade_amount_abs=Decimal("10000"),
            weight_change_bps=1000,
        )
    }
    
    dto = RebalancePlanCollectionDTO(
        success=True,
        plans=plans,
        total_symbols=1,
        symbols_needing_rebalance=1,
        total_trade_value=Decimal("10000"),
    )
    
    assert dto.success is True
    assert len(dto.plans) == 1
    assert "AAPL" in dto.plans
    assert dto.total_symbols == 1
    assert dto.symbols_needing_rebalance == 1