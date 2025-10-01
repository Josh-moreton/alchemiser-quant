"""Business Unit: shared | Status: current.

Migration bridge supporting both stdlib and structlog during transition.

This module provides a feature flag controlled migration path that allows
both logging systems to coexist during the gradual migration to structlog.
"""

from __future__ import annotations

import logging
import os
from typing import Any

# Feature flag for gradual migration
_USE_STRUCTLOG = os.getenv("ALCHEMISER_USE_STRUCTLOG", "false").lower() in (
    "true",
    "1",
    "yes",
)

if _USE_STRUCTLOG:
    from .structlog_config import configure_structlog, get_structlog_logger
    from .structlog_trading import (
        log_data_integrity_checkpoint as log_data_checkpoint_structlog,
    )
    from .structlog_trading import (
        log_order_flow as log_order_flow_structlog,
    )
    from .structlog_trading import (
        log_repeg_operation as log_repeg_operation_structlog,
    )
    from .structlog_trading import (
        log_trade_event as log_trade_event_structlog,
    )
else:
    from .core import get_logger as get_stdlib_logger
    from .trading import (
        log_data_transfer_checkpoint as log_data_checkpoint_stdlib,
    )
    from .trading import (
        log_trade_event as log_trade_event_stdlib,
    )


def get_logger(name: str) -> Any:  # noqa: ANN401
    """Get a logger instance - structlog or stdlib based on feature flag.

    Args:
        name: Logger name, typically __name__ for module-level logging

    Returns:
        Logger instance (structlog or stdlib depending on feature flag)

    """
    if _USE_STRUCTLOG:
        return get_structlog_logger(name)
    return get_stdlib_logger(name)


def log_trade_event(
    logger: Any,  # noqa: ANN401
    event_type: str,
    symbol: str,
    **details: Any,  # noqa: ANN401
) -> None:
    """Log trade event - delegates to appropriate implementation.

    Args:
        logger: Logger instance (structlog or stdlib)
        event_type: Type of event (order_placed, order_filled, etc.)
        symbol: Trading symbol
        **details: Additional event details

    """
    if _USE_STRUCTLOG and hasattr(logger, "bind"):  # structlog logger
        log_trade_event_structlog(logger, event_type, symbol, **details)
    else:
        log_trade_event_stdlib(logger, event_type, symbol, **details)


def log_data_transfer_checkpoint(
    logger: Any,  # noqa: ANN401
    stage: str,
    data: dict[str, Any] | None,
    context: str = "",
) -> None:
    """Log data transfer checkpoint - delegates to appropriate implementation.

    Args:
        logger: Logger instance (structlog or stdlib)
        stage: Current processing stage
        data: Data to validate and log
        context: Additional context description

    """
    if _USE_STRUCTLOG and hasattr(logger, "bind"):  # structlog logger
        log_data_checkpoint_structlog(logger, stage, data, context)
    else:
        log_data_checkpoint_stdlib(logger, stage, data, context)


def setup_application_logging(**kwargs: Any) -> None:  # noqa: ANN401
    """Set up logging using appropriate system based on feature flag.

    Args:
        **kwargs: Configuration parameters passed to the logging setup

    """
    if _USE_STRUCTLOG:
        # Extract relevant parameters for structlog
        structured_format = kwargs.get("structured_format", True)
        log_level = kwargs.get("log_level", logging.INFO)
        configure_structlog(structured_format=structured_format, log_level=log_level)
    else:
        from .config import configure_application_logging

        configure_application_logging()


def log_order_flow(
    logger: Any,  # noqa: ANN401
    stage: str,
    symbol: str,
    quantity: Any,  # noqa: ANN401
    price: Any = None,  # noqa: ANN401
    order_id: str | None = None,
    **context: Any,  # noqa: ANN401
) -> None:
    """Log order flow - delegates to appropriate implementation.

    Args:
        logger: Logger instance (structlog or stdlib)
        stage: Stage of order flow (e.g., 'submission', 'filled', 'cancelled')
        symbol: Trading symbol
        quantity: Order quantity
        price: Order price (optional)
        order_id: Order ID (optional)
        **context: Additional context information

    """
    if _USE_STRUCTLOG and hasattr(logger, "bind"):  # structlog logger
        log_order_flow_structlog(
            logger,
            stage=stage,
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_id=order_id,
            **context,
        )
    else:
        # Fallback to stdlib logging with similar structure
        log_data = f"Order flow: stage={stage} symbol={symbol} quantity={quantity}"
        if price is not None:
            log_data += f" price={price}"
        if order_id:
            log_data += f" order_id={order_id}"
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            log_data += f" {context_str}"
        logger.info(log_data)


def log_repeg_operation(
    logger: Any,  # noqa: ANN401
    operation: str,
    symbol: str,
    old_price: Any,  # noqa: ANN401
    new_price: Any,  # noqa: ANN401
    quantity: Any,  # noqa: ANN401
    reason: str,
    **context: Any,  # noqa: ANN401
) -> None:
    """Log repeg operation - delegates to appropriate implementation.

    Args:
        logger: Logger instance (structlog or stdlib)
        operation: Type of operation ('replace_order' or 'cancel_and_resubmit')
        symbol: Trading symbol
        old_price: Previous order price
        new_price: New order price
        quantity: Order quantity
        reason: Reason for repeg operation
        **context: Additional context information

    """
    if _USE_STRUCTLOG and hasattr(logger, "bind"):  # structlog logger
        log_repeg_operation_structlog(
            logger,
            operation=operation,
            symbol=symbol,
            old_price=old_price,
            new_price=new_price,
            quantity=quantity,
            reason=reason,
            **context,
        )
    else:
        # Fallback to stdlib logging with price improvement calculation
        price_improvement = float(new_price) - float(old_price)
        log_data = (
            f"Repeg operation: operation={operation} symbol={symbol} "
            f"old_price={old_price} new_price={new_price} "
            f"price_improvement={price_improvement} quantity={quantity} reason={reason}"
        )
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            log_data += f" {context_str}"
        logger.info(log_data)


def is_structlog_enabled() -> bool:
    """Check if structlog is currently enabled.

    Returns:
        True if structlog is enabled, False if using stdlib logging

    """
    return _USE_STRUCTLOG
