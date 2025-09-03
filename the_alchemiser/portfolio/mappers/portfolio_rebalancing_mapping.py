#!/usr/bin/env python3
"""Business Unit: portfolio assessment & management; Status: current.

Mapping functions for portfolio rebalancing DTOs.

This module provides mapping utilities to convert between dict structures,
domain objects, and portfolio rebalancing DTOs, supporting the migration from
Any/dict types to structured DTOs.

Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations

import decimal
from decimal import Decimal
from typing import Any

from the_alchemiser.portfolio.allocation.rebalance_plan import RebalancePlan
from the_alchemiser.portfolio.schemas.rebalancing import (
    RebalanceExecutionResultDTO,
    RebalanceInstructionDTO,
    RebalancePlanCollectionDTO,
    RebalancePlanDTO,
    RebalancingImpactDTO,
    RebalancingSummaryDTO,
)

__all__ = [
    "dto_plans_to_domain",
    "dto_to_domain_rebalance_plan",
    "rebalance_execution_result_dict_to_dto",
    "rebalance_instruction_dict_to_dto",
    "rebalance_plans_dict_to_collection_dto",
    "rebalancing_impact_dict_to_dto",
    "rebalancing_summary_dict_to_dto",
    "safe_rebalancing_impact_dict_to_dto",
    "safe_rebalancing_summary_dict_to_dto",
]


def dto_to_domain_rebalance_plan(dto: RebalancePlanDTO) -> RebalancePlan:
    """Convert RebalancePlanDTO to domain RebalancePlan object.

    Derived attributes (trade_direction, trade_amount_abs, weight_change_bps) are not
    copied; they are computed lazily via RebalancePlan properties to ensure domain
    invariants remain the single source of truth.
    """
    return RebalancePlan(
        symbol=dto.symbol,
        current_weight=dto.current_weight,
        target_weight=dto.target_weight,
        weight_diff=dto.weight_diff,
        target_value=dto.target_value,
        current_value=dto.current_value,
        trade_amount=dto.trade_amount,
        needs_rebalance=dto.needs_rebalance,
    )


def dto_plans_to_domain(dto_plans: dict[str, RebalancePlanDTO]) -> dict[str, RebalancePlan]:
    """Convert dict of RebalancePlanDTO to dict of domain RebalancePlan objects."""
    return {symbol: dto_to_domain_rebalance_plan(plan) for symbol, plan in dto_plans.items()}


def rebalance_plans_dict_to_collection_dto(
    plans: dict[str, RebalancePlan],
) -> RebalancePlanCollectionDTO:
    """Convert dict of RebalancePlan domain objects to RebalancePlanCollectionDTO."""
    plan_dtos = {}
    symbols_needing_rebalance = 0
    total_trade_value = Decimal("0")

    for symbol, plan in plans.items():
        plan_dto = RebalancePlanDTO.from_domain(plan)
        plan_dtos[symbol] = plan_dto

        if plan.needs_rebalance:
            symbols_needing_rebalance += 1
            total_trade_value += plan.trade_amount_abs

    return RebalancePlanCollectionDTO(
        success=True,
        plans=plan_dtos,
        total_symbols=len(plans),
        symbols_needing_rebalance=symbols_needing_rebalance,
        total_trade_value=total_trade_value,
    )


def rebalancing_summary_dict_to_dto(data: dict[str, Any]) -> RebalancingSummaryDTO:
    """Convert rebalancing summary dict to RebalancingSummaryDTO."""
    return RebalancingSummaryDTO(
        success=data.get("success", True),
        total_portfolio_value=Decimal(str(data.get("total_portfolio_value", 0))),
        total_symbols=data.get("total_symbols", 0),
        symbols_needing_rebalance=data.get("symbols_needing_rebalance", 0),
        total_trade_value=Decimal(str(data.get("total_trade_value", 0))),
        largest_trade_symbol=data.get("largest_trade_symbol"),
        largest_trade_value=Decimal(str(data.get("largest_trade_value", 0))),
        rebalance_threshold_pct=Decimal(str(data.get("rebalance_threshold_pct", 0))),
        execution_feasible=data.get("execution_feasible", False),
        estimated_costs=Decimal(str(data.get("estimated_costs", 0))),
        error=data.get("error"),
    )


def rebalancing_impact_dict_to_dto(data: dict[str, Any]) -> RebalancingImpactDTO:
    """Convert rebalancing impact dict to RebalancingImpactDTO."""
    return RebalancingImpactDTO(
        success=data.get("success", True),
        portfolio_risk_change=Decimal(str(data.get("portfolio_risk_change", 0))),
        concentration_risk_change=Decimal(str(data.get("concentration_risk_change", 0))),
        estimated_transaction_costs=Decimal(str(data.get("estimated_transaction_costs", 0))),
        estimated_slippage=Decimal(str(data.get("estimated_slippage", 0))),
        total_estimated_costs=Decimal(str(data.get("total_estimated_costs", 0))),
        execution_complexity=data.get("execution_complexity", "MEDIUM"),
        recommended_execution_time=data.get("recommended_execution_time", 30),
        market_impact_risk=data.get("market_impact_risk", "MEDIUM"),
        net_benefit_estimate=Decimal(str(data.get("net_benefit_estimate", 0))),
        recommendation=data.get("recommendation", "DEFER"),
        error=data.get("error"),
    )


def rebalance_instruction_dict_to_dto(data: dict[str, Any]) -> RebalanceInstructionDTO:
    """Convert rebalance instruction dict to RebalanceInstructionDTO."""
    return RebalanceInstructionDTO(
        symbol=data["symbol"],
        action=data["action"],
        quantity=Decimal(str(data["quantity"])),
        estimated_price=Decimal(str(data["estimated_price"])),
        order_type=data.get("order_type", "MARKET"),
        priority=data.get("priority", 3),
        reasoning=data.get("reasoning", "Rebalancing requirement"),
    )


def rebalance_execution_result_dict_to_dto(data: dict[str, Any]) -> RebalanceExecutionResultDTO:
    """Convert rebalance execution result dict to RebalanceExecutionResultDTO."""
    executed_instructions = []
    for instr_data in data.get("executed_instructions", []):
        executed_instructions.append(rebalance_instruction_dict_to_dto(instr_data))

    failed_instructions = []
    for instr_data in data.get("failed_instructions", []):
        failed_instructions.append(rebalance_instruction_dict_to_dto(instr_data))

    return RebalanceExecutionResultDTO(
        success=data.get("success", True),
        execution_id=data.get("execution_id", "unknown"),
        instructions_planned=data.get("instructions_planned", 0),
        instructions_executed=data.get("instructions_executed", 0),
        instructions_failed=data.get("instructions_failed", 0),
        total_value_traded=Decimal(str(data.get("total_value_traded", 0))),
        actual_transaction_costs=Decimal(str(data.get("actual_transaction_costs", 0))),
        execution_efficiency=Decimal(str(data.get("execution_efficiency", 0))),
        executed_instructions=executed_instructions,
        failed_instructions=failed_instructions,
        portfolio_drift_before=Decimal(str(data.get("portfolio_drift_before", 0))),
        portfolio_drift_after=Decimal(str(data.get("portfolio_drift_after", 0))),
        rebalancing_effectiveness=Decimal(str(data.get("rebalancing_effectiveness", 0))),
        execution_duration_seconds=data.get("execution_duration_seconds", 0),
        average_fill_time_seconds=Decimal(str(data.get("average_fill_time_seconds", 0))),
        error=data.get("error"),
    )


def safe_rebalancing_summary_dict_to_dto(data: dict[str, Any]) -> RebalancingSummaryDTO:
    """Safely convert rebalancing summary dict to DTO with fallbacks.

    Provides backward compatibility for incomplete dict structures.
    """
    try:
        return rebalancing_summary_dict_to_dto(data)
    except (KeyError, ValueError, TypeError, decimal.InvalidOperation) as e:
        # Create minimal fallback DTO for error cases
        return RebalancingSummaryDTO(
            success=False,
            total_portfolio_value=Decimal("0"),
            total_symbols=0,
            symbols_needing_rebalance=0,
            total_trade_value=Decimal("0"),
            largest_trade_symbol=None,
            largest_trade_value=Decimal("0"),
            rebalance_threshold_pct=Decimal("0"),
            execution_feasible=False,
            estimated_costs=Decimal("0"),
            error=f"Failed to parse rebalancing summary: {e}",
        )


def safe_rebalancing_impact_dict_to_dto(data: dict[str, Any]) -> RebalancingImpactDTO:
    """Safely convert rebalancing impact dict to DTO with fallbacks.

    Provides backward compatibility for incomplete dict structures.
    """
    try:
        return rebalancing_impact_dict_to_dto(data)
    except (KeyError, ValueError, TypeError, decimal.InvalidOperation) as e:
        # Create minimal fallback DTO for error cases
        return RebalancingImpactDTO(
            success=False,
            portfolio_risk_change=Decimal("0"),
            concentration_risk_change=Decimal("0"),
            estimated_transaction_costs=Decimal("0"),
            estimated_slippage=Decimal("0"),
            total_estimated_costs=Decimal("0"),
            execution_complexity="UNKNOWN",
            recommended_execution_time=1,  # Must be > 0
            market_impact_risk="UNKNOWN",
            net_benefit_estimate=Decimal("0"),
            recommendation="CANCEL",
            error=f"Failed to parse rebalancing impact: {e}",
        )
