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


def is_structlog_enabled() -> bool:
    """Check if structlog is currently enabled.

    Returns:
        True if structlog is enabled, False if using stdlib logging

    """
    return _USE_STRUCTLOG
