#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade result factory utilities for creating DTOs.

Provides utility functions for creating TradeRunResult instances from
various trading execution scenarios and outcomes.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.protocols.orchestrator import TradingModeProvider
from the_alchemiser.shared.schemas.trade_run_result import (
    ExecutionStatus,
    ExecutionSummary,
    OrderAction,
    OrderResultSummary,
    TradeRunResult,
    TradingMode,
)

# Module-level constants for order status validation
ORDER_STATUS_SUCCESS = frozenset(["FILLED", "COMPLETE"])
TRADING_MODE_UNKNOWN = "UNKNOWN"
TRADING_MODE_LIVE = "LIVE"
TRADING_MODE_PAPER = "PAPER"

logger = get_logger(__name__)


def create_failure_result(
    error_message: str,
    started_at: datetime,
    correlation_id: str,
    warnings: list[str],
    *,
    completed_at: datetime | None = None,
) -> TradeRunResult:
    """Create a failure result DTO.

    Args:
        error_message: Description of the failure
        started_at: When the execution started (MUST be timezone-aware UTC datetime)
        correlation_id: Correlation ID for tracking
        warnings: List of warning messages
        completed_at: When the execution completed (defaults to now if None)

    Returns:
        TradeRunResult representing a failed execution

    Raises:
        ValueError: If started_at is timezone-naive

    """
    from datetime import UTC

    # Validate timezone-aware datetime
    if started_at.tzinfo is None:
        logger.error(
            "Timezone-naive datetime provided to create_failure_result",
            extra={"correlation_id": correlation_id},
        )
        raise ValueError("started_at must be timezone-aware datetime")

    if completed_at is None:
        completed_at = datetime.now(UTC)
    elif completed_at.tzinfo is None:
        logger.error(
            "Timezone-naive datetime provided for completed_at",
            extra={"correlation_id": correlation_id},
        )
        raise ValueError("completed_at must be timezone-aware datetime")

    logger.info(
        "Creating failure result DTO",
        extra={
            "correlation_id": correlation_id,
            "error_message": error_message,
            "warnings_count": len(warnings),
        },
    )

    return TradeRunResult(
        status="FAILURE",
        success=False,
        execution_summary=ExecutionSummary(
            orders_total=0,
            orders_succeeded=0,
            orders_failed=0,
            total_value=Decimal("0"),
            success_rate=0.0,  # Display metric, not financial calculation
            execution_duration_seconds=(completed_at - started_at).total_seconds(),
        ),
        orders=[],
        warnings=[*warnings, error_message],
        trading_mode=cast(
            TradingMode, TRADING_MODE_PAPER
        ),  # Default to PAPER when trading mode unknown
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
        started_at: When the execution started (MUST be timezone-aware UTC datetime)
        completed_at: When the execution completed (MUST be timezone-aware UTC datetime)
        correlation_id: Correlation ID for tracking
        warnings: List of warning messages
        success: Whether the execution was successful

    Returns:
        TradeRunResult representing a successful execution

    Raises:
        ValueError: If datetime parameters are timezone-naive or trading_result is invalid

    """
    # Validate timezone-aware datetimes
    if started_at.tzinfo is None:
        logger.error(
            "Timezone-naive datetime provided for started_at",
            extra={"correlation_id": correlation_id},
        )
        raise ValueError("started_at must be timezone-aware datetime")

    if completed_at.tzinfo is None:
        logger.error(
            "Timezone-naive datetime provided for completed_at",
            extra={"correlation_id": correlation_id},
        )
        raise ValueError("completed_at must be timezone-aware datetime")

    # Validate trading_result structure
    if not isinstance(trading_result, dict):
        logger.error(
            "Invalid trading_result type",
            extra={
                "correlation_id": correlation_id,
                "type": type(trading_result).__name__,
            },
        )
        raise ValueError(f"trading_result must be dict, got {type(trading_result).__name__}")

    logger.info(
        "Creating trade result DTO",
        extra={
            "correlation_id": correlation_id,
            "orders_count": len(trading_result.get("orders_executed", [])),
            "success": success,
        },
    )

    orders_executed = trading_result.get("orders_executed", [])
    if not isinstance(orders_executed, list):
        logger.error(
            "Invalid orders_executed type",
            extra={
                "correlation_id": correlation_id,
                "type": type(orders_executed).__name__,
            },
        )
        raise ValueError(f"orders_executed must be list, got {type(orders_executed).__name__}")

    order_results = _convert_orders_to_results(orders_executed, completed_at, correlation_id)
    execution_summary = _calculate_execution_summary(order_results, started_at, completed_at)
    status = _determine_execution_status(success=success, execution_summary=execution_summary)
    trading_mode = _determine_trading_mode(orchestrator)

    logger.info(
        "Trade result DTO created",
        extra={
            "correlation_id": correlation_id,
            "status": status,
            "orders_total": execution_summary.orders_total,
            "orders_succeeded": execution_summary.orders_succeeded,
            "orders_failed": execution_summary.orders_failed,
        },
    )

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
    orders_executed: list[dict[str, Any]], completed_at: datetime, correlation_id: str
) -> list[OrderResultSummary]:
    """Convert executed orders to OrderResultSummary instances.

    Args:
        orders_executed: List of executed order dictionaries
        completed_at: Fallback timestamp for orders without filled_at
        correlation_id: Correlation ID for tracking

    Returns:
        List of OrderResultSummary instances

    Raises:
        ValueError: If any order cannot be converted (with index in message)

    """
    order_results: list[OrderResultSummary] = []

    for idx, order in enumerate(orders_executed):
        try:
            order_result = _create_single_order_result(order, completed_at)
            order_results.append(order_result)
        except (ValueError, TypeError, KeyError) as e:
            logger.error(
                "Failed to convert order",
                extra={
                    "correlation_id": correlation_id,
                    "order_index": idx,
                    "error": str(e),
                },
            )
            raise ValueError(f"Failed to convert order at index {idx}: {e}") from e

    return order_results


def _create_single_order_result(
    order: dict[str, Any], completed_at: datetime
) -> OrderResultSummary:
    """Create a single OrderResultSummary from order data.

    Args:
        order: Order dictionary with execution details
        completed_at: Fallback timestamp (MUST be timezone-aware UTC datetime)

    Returns:
        OrderResultSummary instance

    Raises:
        ValueError: If order dict is missing required fields or has invalid types

    """
    # Validate input is a dict
    if not isinstance(order, dict):
        raise ValueError(f"Order must be dict, got {type(order).__name__}")

    # Validate timezone-aware datetime
    if completed_at.tzinfo is None:
        raise ValueError("completed_at must be timezone-aware datetime")

    # Safe order_id handling with type validation
    order_id = order.get("order_id", "")
    if not isinstance(order_id, str):
        order_id = str(order_id) if order_id else ""
    # Extract ONLY last 6 chars (no prefix) to match schema validation (exactly 6 chars)
    order_id_redacted = order_id[-6:] if len(order_id) >= 6 else None

    # Validate and convert qty
    qty_raw = order.get("qty", 0)
    try:
        qty = Decimal(str(qty_raw))
    except (ValueError, TypeError, Exception) as e:
        raise ValueError(f"Invalid qty in order: {qty_raw}") from e

    # Validate filled_price if present
    filled_price = order.get("filled_avg_price")
    if filled_price is not None and not isinstance(filled_price, (int, float, Decimal)):
        raise ValueError(f"Invalid filled_avg_price type: {type(filled_price).__name__}")

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
        success=order.get("status", "").upper() in ORDER_STATUS_SUCCESS,
        error_message=order.get("error_message"),
        timestamp=order.get("filled_at") or completed_at,
    )


def _calculate_trade_amount(
    order: dict[str, Any], qty: Decimal, filled_price: int | float | Decimal | None
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
    # Float division for success_rate is acceptable - this is a display metric, not a financial calculation
    success_rate = orders_succeeded / orders_total if orders_total > 0 else 1.0

    return ExecutionSummary(
        orders_total=orders_total,
        orders_succeeded=orders_succeeded,
        orders_failed=orders_failed,
        total_value=total_value,
        success_rate=success_rate,
        execution_duration_seconds=(completed_at - started_at).total_seconds(),
    )


def _determine_execution_status(
    *, success: bool, execution_summary: ExecutionSummary
) -> ExecutionStatus:
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
    mode_str = (
        TRADING_MODE_LIVE if getattr(orchestrator, "live_trading", False) else TRADING_MODE_PAPER
    )
    return cast(TradingMode, mode_str)
