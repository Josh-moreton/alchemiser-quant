"""Business Unit: shared | Status: current.

Trading-specific structlog utilities with enhanced functionality.

This module provides specialized structlog logging functions for trading operations
including order flow logging, repeg operations, and data integrity checkpoints.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import structlog


def log_trade_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    symbol: str,
    **details: Any,  # noqa: ANN401
) -> None:
    """Log a trading event with standardized structure.

    Args:
        logger: Structlog logger instance
        event_type: Type of event (order_placed, order_filled, etc.)
        symbol: Trading symbol
        **details: Additional event details

    """
    logger.info(
        "Trading event",
        event_type=event_type,
        symbol=symbol,
        **details,
    )


def log_order_flow(
    logger: structlog.stdlib.BoundLogger,
    stage: str,
    symbol: str,
    quantity: Decimal,
    price: Decimal | None = None,
    order_id: str | None = None,
    **context: Any,  # noqa: ANN401
) -> None:
    """Log order flow events with consistent structure.

    Args:
        logger: Structlog logger instance
        stage: Stage of order flow (e.g., 'submission', 'filled', 'cancelled')
        symbol: Trading symbol
        quantity: Order quantity
        price: Order price (optional)
        order_id: Order ID (optional)
        **context: Additional context information

    """
    log_data: dict[str, Any] = {
        "stage": stage,
        "symbol": symbol,
        "quantity": quantity,  # structlog handles Decimal automatically
    }

    if price is not None:
        log_data["price"] = price
    if order_id:
        log_data["order_id"] = order_id

    log_data.update(context)

    logger.info("Order flow", **log_data)


def log_repeg_operation(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    symbol: str,
    old_price: Decimal | None,
    new_price: Decimal,
    quantity: Decimal,
    reason: str,
    **context: Any,  # noqa: ANN401
) -> None:
    """Log repeg operations with detailed context.

    Args:
        logger: Structlog logger instance
        operation: Type of operation ('replace_order' or 'cancel_and_resubmit')
        symbol: Trading symbol
        old_price: Previous order price (None if no original price available)
        new_price: New order price
        quantity: Order quantity
        reason: Reason for repeg operation
        **context: Additional context information

    """
    # Calculate price improvement only if old_price is available
    price_improvement = new_price - old_price if old_price is not None else None

    logger.info(
        "Repeg operation",
        operation=operation,
        symbol=symbol,
        old_price=old_price,
        new_price=new_price,
        quantity=quantity,
        reason=reason,
        price_improvement=price_improvement,
        **context,
    )


def bind_trading_context(
    logger: structlog.stdlib.BoundLogger,
    symbol: str | None = None,
    strategy: str | None = None,
    portfolio: str | None = None,
    order_id: str | None = None,
) -> structlog.stdlib.BoundLogger:
    """Bind trading context to a logger for consistent tagging.

    Args:
        logger: Structlog logger instance
        symbol: Trading symbol (optional)
        strategy: Strategy name (optional)
        portfolio: Portfolio name (optional)
        order_id: Order ID (optional)

    Returns:
        Logger with bound context

    """
    context: dict[str, str] = {}
    if symbol:
        context["symbol"] = symbol
    if strategy:
        context["strategy"] = strategy
    if portfolio:
        context["portfolio"] = portfolio
    if order_id:
        context["order_id"] = order_id

    return logger.bind(**context)


def log_data_integrity_checkpoint(
    logger: structlog.stdlib.BoundLogger,
    stage: str,
    data: dict[str, Any] | None,
    context: str = "",
) -> None:
    """Log data transfer checkpoint with integrity validation.

    Args:
        logger: Structlog logger instance
        stage: Current processing stage
        data: Data to validate and log
        context: Additional context description

    """
    if data is None:
        logger.error(
            "Data integrity violation",
            stage=stage,
            issue="null_data_detected",
            context=context,
        )
        return

    data_count = len(data) if data else 0

    # Calculate checksum for numeric data
    data_checksum = 0.0
    if data and isinstance(data, dict):
        numeric_values: list[float] = []
        for v in data.values():
            if isinstance(v, int | float | Decimal):
                numeric_values.append(float(v))
        data_checksum = sum(numeric_values)

    logger.info(
        "Data transfer checkpoint",
        stage=stage,
        context=context,
        data_count=data_count,
        data_checksum=data_checksum,
        data_sample=(dict(list(data.items())[:3]) if data_count > 0 and data_count <= 10 else None),
    )

    # Validation warnings
    if data_count == 0:
        logger.warning("Empty data detected", stage=stage)

    if (
        isinstance(data, dict)
        and all(isinstance(v, int | float | Decimal) for v in data.values())
        and abs(data_checksum - 1.0) > 0.05
    ):
        logger.warning(
            "Portfolio allocation anomaly",
            stage=stage,
            allocation_sum=data_checksum,
            expected_sum=1.0,
        )
