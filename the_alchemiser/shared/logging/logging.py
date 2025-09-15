"""Logging utilities for the modular architecture.

Legacy compatibility module that delegates to the centralized logging utilities.
All new code should import directly from logging_utils.py.
"""

from __future__ import annotations

import logging

# Import from the centralized utilities using relative imports to avoid circular dependency
from .logging_utils import get_logger as _get_logger
from .logging_utils import log_with_context as _log_with_context
from .logging_utils import setup_logging as _setup_logging


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Delegates to centralized logging utilities.

    Args:
        name: Logger name

    Returns:
        Logger instance

    """
    return _get_logger(name)


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration.

    Delegates to centralized logging utilities with human-readable format.

    Args:
        level: Logging level

    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    _setup_logging(
        log_level=log_level,
        structured_format=False,  # Use human-readable format for compatibility
        suppress_third_party=True,
    )


def log_with_context(
    logger: logging.Logger, level: str, message: str, **context: object
) -> None:
    """Log a message with additional context.

    Delegates to centralized logging utilities.

    Args:
        logger: Logger instance
        level: Log level as string
        message: Log message
        **context: Additional context

    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    _log_with_context(logger, log_level, message, **context)
