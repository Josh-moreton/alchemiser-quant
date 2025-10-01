"""Business Unit: shared | Status: current.

Trading-specific logging functions.

This module provides specialized logging functions for trading operations including
trade event logging, data transfer checkpoints, and expectation vs reality validation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import cast

from .core import log_with_context
from .formatters import AlchemiserLoggerAdapter


def get_trading_logger(
    module_name: str, **context: object
) -> logging.Logger | AlchemiserLoggerAdapter:
    """Get a logger specifically configured for trading operations.

    Args:
        module_name: Name of the module/component
        **context: Additional context to include in all log messages

    Returns:
        Logger instance with trading-specific configuration

    """
    logger = logging.getLogger(module_name)
    if context:
        # Create adapter with default context
        return AlchemiserLoggerAdapter(logger, context)
    return logger


def log_trade_event(
    logger: logging.Logger, event_type: str, symbol: str, **details: object
) -> None:
    """Log a trading event with standardized structure.

    Args:
        logger: Logger instance
        event_type: Type of event (order_placed, order_filled, etc.)
        symbol: Trading symbol
        **details: Additional event details

    """
    context = {
        "event_type": event_type,
        "symbol": symbol,
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        **details,
    }
    log_with_context(logger, logging.INFO, f"Trading event: {event_type} for {symbol}", **context)


def log_error_with_context(
    logger: logging.Logger, error: Exception, operation: str, **context: object
) -> None:
    """Log an error with full context and traceback.

    Args:
        logger: Logger instance
        error: Exception that occurred
        operation: Description of the operation that failed
        **context: Additional context information

    """
    context.update(
        {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
    )
    log_with_context(logger, logging.ERROR, f"Error in {operation}: {error}", **context)
    logger.exception(f"Full traceback for {operation} error:")


def log_data_transfer_checkpoint(
    logger: logging.Logger,
    stage: str,
    data: dict[str, object] | None,
    context: str = "",
) -> None:
    """Log a data transfer checkpoint with integrity validation.

    This function provides standardized logging for data transfer points
    in the trade pipeline to help trace where data might be lost.

    Args:
        logger: Logger instance to use
        stage: Name of the pipeline stage (e.g., "ExecutionManager→Engine")
        data: The data being transferred (typically portfolio allocation dict)
        context: Additional context description

    """
    if data is None:
        logger.error(f"🚨 DATA_TRANSFER_CHECKPOINT[{stage}]: NULL DATA DETECTED")
        logger.error(f"🚨 Context: {context}")
        return

    # Calculate data integrity metrics
    data_count = len(data) if data else 0
    data_checksum: float = 0.0
    if data and all(isinstance(v, int | float) for v in data.values()):
        numeric_values: list[float] = []
        for v in data.values():
            numeric_values.append(float(cast(int | float, v)))
        data_checksum = sum(numeric_values)
    data_type = type(data).__name__

    # Log checkpoint info
    logger.info(f"=== DATA_TRANSFER_CHECKPOINT[{stage}] ===")
    logger.info(f"STAGE: {stage}")
    logger.info(f"CONTEXT: {context}")
    logger.info(f"DATA_TYPE: {data_type}")
    logger.info(f"DATA_COUNT: {data_count}")
    logger.info(f"DATA_CHECKSUM: {data_checksum:.6f}")

    # Log detailed content for small datasets
    if data_count <= 10:
        logger.info(f"DATA_CONTENT: {data}")
    else:
        # Log first few items for large datasets
        items = list(data.items())[:5] if hasattr(data, "items") else []
        logger.info(f"DATA_SAMPLE: {dict(items)} (showing first 5 of {data_count})")

    # Data validation warnings
    if data_count == 0:
        logger.warning(f"⚠️ CHECKPOINT[{stage}]: Empty data detected")

    if (
        isinstance(data, dict)
        and all(isinstance(v, int | float) for v in data.values())
        and abs(data_checksum - 1.0) > 0.05
    ):
        # Portfolio allocation validation
        logger.warning(
            f"⚠️ CHECKPOINT[{stage}]: Portfolio allocation sum={data_checksum:.4f}, expected~1.0"
        )

    logger.info(f"=== END_CHECKPOINT[{stage}] ===")


def _format_trade_details(trade: dict[str, object], index: int) -> str:
    """Format trade details for logging."""
    symbol = trade.get("symbol", "UNKNOWN")
    action = trade.get("action", "UNKNOWN")
    amount = trade.get("amount", 0)
    return f"  Expected_{index + 1}: {action} {symbol} ${amount:.2f}"


def _format_order_details(order: object, index: int) -> str:
    """Format order details for logging."""
    if hasattr(order, "symbol") and hasattr(order, "side") and hasattr(order, "qty"):
        return f"  Actual_{index + 1}: {order.side} {order.symbol} qty={order.qty}"
    if isinstance(order, dict):
        symbol = order.get("symbol", "UNKNOWN")
        side = order.get("side", "UNKNOWN")
        qty = order.get("qty", 0)
        return f"  Actual_{index + 1}: {side} {symbol} qty={qty}"
    return f"  Actual_{index + 1}: {order}"


def _log_trade_mismatches(
    logger: logging.Logger,
    expected_trades: list[dict[str, object]],
    expected_count: int,
    actual_count: int,
    stage: str,
) -> None:
    """Log trade count mismatches and lost trades."""
    if expected_count > 0 and actual_count == 0:
        logger.error(
            f"🚨 TRADE_LOSS_DETECTED[{stage}]: Expected {expected_count} trades but got 0 orders"
        )
        for trade in expected_trades:
            symbol = trade.get("symbol", "UNKNOWN")
            action = trade.get("action", "UNKNOWN")
            amount = trade.get("amount", 0)
            logger.error(f"🚨 LOST_TRADE: {action} {symbol} ${amount:.2f}")
    elif expected_count != actual_count:
        logger.warning(
            f"⚠️ TRADE_COUNT_MISMATCH[{stage}]: Expected {expected_count} ≠ Actual {actual_count}"
        )


def log_trade_expectation_vs_reality(
    logger: logging.Logger,
    expected_trades: list[dict[str, object]],
    actual_orders: list[object],
    stage: str = "Unknown",
) -> None:
    """Log comparison between expected trades and actual orders created.

    Args:
        logger: Logger instance
        expected_trades: List of expected trade calculations
        actual_orders: List of actual orders created
        stage: Pipeline stage where this comparison is being made

    """
    expected_count = len(expected_trades) if expected_trades else 0
    actual_count = len(actual_orders) if actual_orders else 0

    logger.info(f"=== TRADE_EXPECTATION_VS_REALITY[{stage}] ===")
    logger.info(f"EXPECTED_TRADES: {expected_count}")
    logger.info(f"ACTUAL_ORDERS: {actual_count}")
    logger.info(f"MATCH: {expected_count == actual_count}")

    if expected_count > 0:
        logger.info("EXPECTED_TRADE_DETAILS:")
        for i, trade in enumerate(expected_trades):
            logger.info(_format_trade_details(trade, i))

    if actual_count > 0:
        logger.info("ACTUAL_ORDER_DETAILS:")
        for i, order in enumerate(actual_orders):
            logger.info(_format_order_details(order, i))

    # Flag mismatches
    _log_trade_mismatches(logger, expected_trades, expected_count, actual_count, stage)

    logger.info(f"=== END_EXPECTATION_VS_REALITY[{stage}] ===")
