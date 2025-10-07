#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade result factory utilities for creating DTOs.

Provides utility functions for creating TradeRunResult instances from
various trading execution scenarios and outcomes.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.protocols.orchestrator import TradingModeProvider
from the_alchemiser.shared.schemas.trade_run_result import (
    ExecutionStatus,
    ExecutionSummary,
    OrderAction,
    OrderResultSummary,
    TradeRunResult,
    TradingMode,
)


def create_failure_result(
    error_message: str,
    started_at: datetime,
    correlation_id: str,
    warnings: list[str],
) -> TradeRunResult:
    """Create a failure result DTO.

    Args:
        error_message: Description of the failure
        started_at: When the execution started
        correlation_id: Correlation ID for tracking
        warnings: List of warning messages

    Returns:
        TradeRunResult representing a failed execution

    """
    from datetime import UTC, datetime

    completed_at = datetime.now(UTC)

    return TradeRunResult(
        status="FAILURE",
        success=False,
        execution_summary=ExecutionSummary(
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
    orchestrator: TradingModeProvider,
    started_at: datetime,
    completed_at: datetime,
    correlation_id: str,
    warnings: list[str],
    *,
    success: bool,
) -> TradeRunResult:
    """Create a success result from trading results.

    Args:
        trading_result: Dictionary containing execution results
        orchestrator: Trading orchestrator instance
        started_at: When the execution started
        completed_at: When the execution completed
        correlation_id: Correlation ID for tracking
        warnings: List of warning messages
        success: Whether the execution was successful

    Returns:
        TradeRunResult representing a successful execution

    """
    orders_executed = trading_result.get("orders_executed", [])
    order_results = _convert_orders_to_results(orders_executed, completed_at)
    execution_summary = _calculate_execution_summary(order_results, started_at, completed_at)
    status = _determine_execution_status(success=success, execution_summary=execution_summary)
    trading_mode = _determine_trading_mode(orchestrator)

    return TradeRunResult(
        status=status,
        success=success,
        execution_summary=execution_summary,
        orders=order_results,
        warnings=warnings,
        trading_mode=trading_mode,
        started_at=started_at,
        completed_at=completed_at,
        correlation_id=correlation_id,
    )


def _convert_orders_to_results(
    orders_executed: list[dict[str, Any]], completed_at: datetime
) -> list[OrderResultSummary]:
    """Convert executed orders to OrderResultSummary instances.

    Args:
        orders_executed: List of executed order dictionaries
        completed_at: Fallback timestamp for orders without filled_at

    Returns:
        List of OrderResultSummary instances

    """
    order_results: list[OrderResultSummary] = []

    for order in orders_executed:
        order_result = _create_single_order_result(order, completed_at)
        order_results.append(order_result)

    return order_results


def _create_single_order_result(
    order: dict[str, Any], completed_at: datetime
) -> OrderResultSummary:
    """Create a single OrderResultSummary from order data.

    Args:
        order: Order dictionary with execution details
        completed_at: Fallback timestamp

    Returns:
        OrderResultSummary instance

    """
    order_id = order.get("order_id", "")
    order_id_redacted = f"...{order_id[-6:]}" if len(order_id) > 6 else order_id

    qty = Decimal(str(order.get("qty", 0)))
    filled_price = order.get("filled_avg_price")
    trade_amount = _calculate_trade_amount(order, qty, filled_price)
    
    # Map action to OrderAction Literal type
    side = order.get("side", "").upper()
    action: OrderAction = "BUY" if side == "BUY" else "SELL"

    return OrderResultSummary(
        symbol=order.get("symbol", ""),
        action=action,
        trade_amount=trade_amount,
        shares=qty,
        price=(Decimal(str(filled_price)) if filled_price else None),
        order_id_redacted=order_id_redacted,
        order_id_full=order_id,
        success=order.get("status", "").upper() in ["FILLED", "COMPLETE"],
        error_message=order.get("error_message"),
        timestamp=order.get("filled_at") or completed_at,
    )


def _calculate_trade_amount(
    order: dict[str, Any], qty: Decimal, filled_price: float | None
) -> Decimal:
    """Calculate trade amount from order data.

    Args:
        order: Order dictionary
        qty: Quantity as Decimal
        filled_price: Filled price (may be None)

    Returns:
        Trade amount as Decimal

    """
    if order.get("notional"):
        return Decimal(str(order.get("notional")))
    if filled_price and qty:
        return qty * Decimal(str(filled_price))
    return Decimal("0")


def _calculate_execution_summary(
    order_results: list[OrderResultSummary],
    started_at: datetime,
    completed_at: datetime,
) -> ExecutionSummary:
    """Calculate execution summary metrics from order DTOs.

    Args:
        order_results: List of order result DTOs
        started_at: Execution start time
        completed_at: Execution completion time

    Returns:
        ExecutionSummary with calculated metrics

    """
    orders_total = len(order_results)
    orders_succeeded = sum(1 for order in order_results if order.success)
    orders_failed = orders_total - orders_succeeded
    total_value = sum((order.trade_amount for order in order_results), Decimal("0"))
    success_rate = orders_succeeded / orders_total if orders_total > 0 else 1.0

    return ExecutionSummary(
        orders_total=orders_total,
        orders_succeeded=orders_succeeded,
        orders_failed=orders_failed,
        total_value=total_value,
        success_rate=success_rate,
        execution_duration_seconds=(completed_at - started_at).total_seconds(),
    )


def _determine_execution_status(*, success: bool, execution_summary: ExecutionSummary) -> ExecutionStatus:
    """Determine execution status based on success flag and summary.

    Args:
        success: Whether execution was successful
        execution_summary: Execution summary with order counts

    Returns:
        Status string: "SUCCESS", "PARTIAL", or "FAILURE"

    """
    if success and execution_summary.orders_failed == 0:
        return "SUCCESS"
    if execution_summary.orders_succeeded > 0:
        return "PARTIAL"
    return "FAILURE"


def _determine_trading_mode(orchestrator: TradingModeProvider) -> TradingMode:
    """Determine trading mode from orchestrator.

    Args:
        orchestrator: Trading orchestrator instance

    Returns:
        Trading mode string: "LIVE" or "PAPER"

    """
    return "LIVE" if getattr(orchestrator, "live_trading", False) else "PAPER"
