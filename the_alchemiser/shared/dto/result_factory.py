#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade result factory utilities for creating DTOs.

Provides utility functions for creating TradeRunResultDTO instances from
various trading execution scenarios and outcomes.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator

from the_alchemiser.shared.dto.trade_run_result_dto import (
    ExecutionSummaryDTO,
    OrderResultSummaryDTO,
    TradeRunResultDTO,
)


def create_failure_result(
    error_message: str,
    started_at: datetime,
    correlation_id: str,
    warnings: list[str],
) -> TradeRunResultDTO:
    """Create a failure result DTO.
    
    Args:
        error_message: Description of the failure
        started_at: When the execution started
        correlation_id: Correlation ID for tracking
        warnings: List of warning messages
        
    Returns:
        TradeRunResultDTO representing a failed execution
    """
    from datetime import UTC, datetime

    completed_at = datetime.now(UTC)

    return TradeRunResultDTO(
        status="FAILURE",
        success=False,
        execution_summary=ExecutionSummaryDTO(
            orders_total=0,
            orders_succeeded=0,
            orders_failed=0,
            total_value=Decimal("0"),
            success_rate=0.0,
            execution_duration_seconds=(completed_at - started_at).total_seconds(),
        ),
        orders=[],
        warnings=[*warnings, error_message],
        trading_mode="UNKNOWN",
        started_at=started_at,
        completed_at=completed_at,
        correlation_id=correlation_id,
    )


def create_success_result(
    trading_result: dict[str, Any],
    orchestrator: TradingOrchestrator,
    started_at: datetime,
    completed_at: datetime,
    correlation_id: str,
    warnings: list[str],
    *,
    success: bool,
) -> TradeRunResultDTO:
    """Create a success result DTO from trading results.
    
    Args:
        trading_result: Dictionary containing execution results
        orchestrator: Trading orchestrator instance
        started_at: When the execution started
        completed_at: When the execution completed
        correlation_id: Correlation ID for tracking
        warnings: List of warning messages
        success: Whether the execution was successful
        
    Returns:
        TradeRunResultDTO representing a successful execution
    """
    orders_executed = trading_result.get("orders_executed", [])

    # Convert orders to DTOs with ID redaction
    order_dtos: list[OrderResultSummaryDTO] = []
    for order in orders_executed:
        order_id = order.get("order_id", "")
        order_id_redacted = f"...{order_id[-6:]}" if len(order_id) > 6 else order_id

        # Calculate trade amount from qty * price if notional not available
        qty = Decimal(str(order.get("qty", 0)))
        filled_price = order.get("filled_avg_price")

        if order.get("notional"):
            trade_amount = Decimal(str(order.get("notional")))
        elif filled_price and qty:
            trade_amount = qty * Decimal(str(filled_price))
        else:
            trade_amount = Decimal("0")

        order_dtos.append(
            OrderResultSummaryDTO(
                symbol=order.get("symbol", ""),
                action=order.get("side", "").upper(),
                trade_amount=trade_amount,
                shares=qty,
                price=(Decimal(str(filled_price)) if filled_price else None),
                order_id_redacted=order_id_redacted,
                order_id_full=order_id,
                success=order.get("status", "").upper() in ["FILLED", "COMPLETE"],
                error_message=order.get("error_message"),
                timestamp=order.get("filled_at") or completed_at,
            )
        )

    # Calculate summary metrics
    orders_total = len(order_dtos)
    orders_succeeded = sum(1 for order in order_dtos if order.success)
    orders_failed = orders_total - orders_succeeded
    total_value = sum((order.trade_amount for order in order_dtos), Decimal("0"))
    success_rate = orders_succeeded / orders_total if orders_total > 0 else 1.0

    if success and orders_failed == 0:
        status = "SUCCESS"
    elif orders_succeeded > 0:
        status = "PARTIAL"
    else:
        status = "FAILURE"

    return TradeRunResultDTO(
        status=status,
        success=success,
        execution_summary=ExecutionSummaryDTO(
            orders_total=orders_total,
            orders_succeeded=orders_succeeded,
            orders_failed=orders_failed,
            total_value=total_value,
            success_rate=success_rate,
            execution_duration_seconds=(completed_at - started_at).total_seconds(),
        ),
        orders=order_dtos,
        warnings=warnings,
        trading_mode=("LIVE" if getattr(orchestrator, "live_trading", False) else "PAPER"),
        started_at=started_at,
        completed_at=completed_at,
        correlation_id=correlation_id,
    )