#!/usr/bin/env python3
"""
Portfolio Rebalancing DTOs for The Alchemiser Trading System.

This module provides Pydantic v2 DTOs for portfolio rebalancing operations,
replacing dict/Any usage in portfolio services with strongly typed boundaries.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Integration with domain RebalancePlan objects
- Comprehensive rebalancing metrics and analysis
- Type safety for portfolio rebalancing operations

Part of the Pydantic v2 migration to eliminate dict/Any boundaries.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.domain.portfolio.rebalancing.rebalance_plan import RebalancePlan
from the_alchemiser.interfaces.schemas.base import ResultDTO


class RebalancePlanDTO(BaseModel):
    """
    DTO for individual symbol rebalance plan.
    
    Wraps the domain RebalancePlan object for service layer boundaries.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    current_weight: Decimal = Field(..., ge=0, le=1, description="Current portfolio weight (0-1)")
    target_weight: Decimal = Field(..., ge=0, le=1, description="Target portfolio weight (0-1)")
    weight_diff: Decimal = Field(..., description="Weight difference (target - current)")
    target_value: Decimal = Field(..., ge=0, description="Target dollar value")
    current_value: Decimal = Field(..., ge=0, description="Current dollar value")
    trade_amount: Decimal = Field(..., description="Dollar amount to trade (positive=buy, negative=sell)")
    needs_rebalance: bool = Field(..., description="Whether rebalancing is needed for this symbol")
    trade_direction: str = Field(..., description="Trade direction: BUY, SELL, or HOLD")
    trade_amount_abs: Decimal = Field(..., ge=0, description="Absolute trade amount")
    weight_change_bps: int = Field(..., description="Weight change in basis points")

    @classmethod
    def from_domain(cls, plan: RebalancePlan) -> RebalancePlanDTO:
        """Create DTO from domain RebalancePlan object."""
        return cls(
            symbol=plan.symbol,
            current_weight=plan.current_weight,
            target_weight=plan.target_weight,
            weight_diff=plan.weight_diff,
            target_value=plan.target_value,
            current_value=plan.current_value,
            trade_amount=plan.trade_amount,
            needs_rebalance=plan.needs_rebalance,
            trade_direction=plan.trade_direction,
            trade_amount_abs=plan.trade_amount_abs,
            weight_change_bps=plan.weight_change_bps,
        )


class RebalancePlanCollectionDTO(ResultDTO):
    """
    DTO for collection of rebalance plans by symbol.
    
    Replaces dict[str, RebalancePlan] returns from portfolio services.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    plans: dict[str, RebalancePlanDTO] = Field(
        ..., description="Rebalance plans by symbol"
    )
    total_symbols: int = Field(..., ge=0, description="Total number of symbols")
    symbols_needing_rebalance: int = Field(..., ge=0, description="Number of symbols needing rebalancing")
    total_trade_value: Decimal = Field(..., ge=0, description="Total absolute trade value")


class RebalancingSummaryDTO(ResultDTO):
    """
    DTO for rebalancing summary analysis.
    
    Replaces dict[str, Any] returns from get_rebalancing_summary.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    total_portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    total_symbols: int = Field(..., ge=0, description="Total number of symbols")
    symbols_needing_rebalance: int = Field(..., ge=0, description="Symbols requiring rebalancing")
    total_trade_value: Decimal = Field(..., ge=0, description="Total trade value required")
    largest_trade_symbol: str | None = Field(None, description="Symbol with largest trade requirement")
    largest_trade_value: Decimal = Field(Decimal("0"), ge=0, description="Largest trade value")
    rebalance_threshold_pct: Decimal = Field(..., ge=0, description="Rebalancing threshold percentage")
    execution_feasible: bool = Field(..., description="Whether rebalancing is feasible")
    estimated_costs: Decimal = Field(Decimal("0"), ge=0, description="Estimated transaction costs")


class RebalancingImpactDTO(ResultDTO):
    """
    DTO for rebalancing impact estimation.
    
    Replaces dict[str, Any] returns from estimate_rebalancing_impact.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Risk metrics
    portfolio_risk_change: Decimal = Field(..., description="Expected portfolio risk change")
    concentration_risk_change: Decimal = Field(..., description="Change in concentration risk")

    # Trading metrics
    estimated_transaction_costs: Decimal = Field(..., ge=0, description="Estimated total transaction costs")
    estimated_slippage: Decimal = Field(..., ge=0, description="Estimated market impact/slippage")
    total_estimated_costs: Decimal = Field(..., ge=0, description="Total estimated execution costs")

    # Execution analysis
    execution_complexity: str = Field(..., description="Execution complexity: LOW, MEDIUM, HIGH")
    recommended_execution_time: int = Field(..., gt=0, description="Recommended execution time in minutes")
    market_impact_risk: str = Field(..., description="Market impact risk: LOW, MEDIUM, HIGH")

    # Summary
    net_benefit_estimate: Decimal = Field(..., description="Estimated net benefit after costs")
    recommendation: str = Field(..., description="Overall recommendation: EXECUTE, DEFER, CANCEL")


class RebalanceInstructionDTO(BaseModel):
    """
    DTO for individual rebalancing instruction.
    
    Used in rebalancing execution workflows.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    action: str = Field(..., description="Action: BUY, SELL, HOLD")
    quantity: Decimal = Field(..., gt=0, description="Quantity to trade")
    estimated_price: Decimal = Field(..., gt=0, description="Estimated execution price")
    order_type: str = Field(..., description="Order type: MARKET, LIMIT")
    priority: int = Field(..., ge=1, le=5, description="Execution priority (1=highest)")
    reasoning: str = Field(..., min_length=1, description="Reasoning for this instruction")


class RebalanceExecutionResultDTO(ResultDTO):
    """
    DTO for rebalancing execution results.
    
    Provides comprehensive execution tracking and results.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    execution_id: str = Field(..., min_length=1, description="Unique execution identifier")
    instructions_planned: int = Field(..., ge=0, description="Number of instructions planned")
    instructions_executed: int = Field(..., ge=0, description="Number of instructions executed")
    instructions_failed: int = Field(..., ge=0, description="Number of failed instructions")

    # Financial results
    total_value_traded: Decimal = Field(..., ge=0, description="Total value traded")
    actual_transaction_costs: Decimal = Field(..., ge=0, description="Actual transaction costs")
    execution_efficiency: Decimal = Field(..., ge=0, le=1, description="Execution efficiency (0-1)")

    # Execution details
    executed_instructions: list[RebalanceInstructionDTO] = Field(
        default_factory=list, description="Successfully executed instructions"
    )
    failed_instructions: list[RebalanceInstructionDTO] = Field(
        default_factory=list, description="Failed instructions"
    )

    # Portfolio impact
    portfolio_drift_before: Decimal = Field(..., ge=0, description="Portfolio drift before rebalancing")
    portfolio_drift_after: Decimal = Field(..., ge=0, description="Portfolio drift after rebalancing")
    rebalancing_effectiveness: Decimal = Field(..., ge=0, le=1, description="Rebalancing effectiveness (0-1)")

    # Timing
    execution_duration_seconds: int = Field(..., ge=0, description="Total execution time in seconds")
    average_fill_time_seconds: Decimal = Field(..., ge=0, description="Average order fill time")
