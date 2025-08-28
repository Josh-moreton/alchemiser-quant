#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Error scope context manager for The Alchemiser Trading System.

This module provides context managers for error handling with automatic logging.
Renamed from ErrorContext to avoid naming collision.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any


class _ScopeErrorHandler:
    """Minimal error handler for ErrorScope logging needs."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize with logger."""
        self.logger = logger or logging.getLogger(__name__)

    def log_and_handle(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        default_return: Any = None,
    ) -> Any:
        """Log error and return default value instead of raising.

        Args:
            error: Exception that occurred
            context: Additional context for logging
            default_return: Value to return instead of raising

        Returns:
            Default return value

        """
        context = context or {}

        # Log with context
        log_message = f"Handled error: {error}"
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            log_message += f" [Context: {context_str}]"

        self.logger.error(log_message)
        self.logger.debug(f"Traceback: {traceback.format_exc()}")

        return default_return


class ErrorScope:
    """Context manager for error handling with automatic logging."""

    def __init__(
        self,
        error_handler: _ScopeErrorHandler,
        context: dict[str, Any] | None = None,
        reraise: bool = True,
    ) -> None:
        """Initialize error scope.

        Args:
            error_handler: Error handler instance
            context: Logging context
            reraise: Whether to reraise exceptions

        """
        self.error_handler = error_handler
        self.context = context or {}
        self.reraise = reraise

    def __enter__(self) -> ErrorScope:
        """Enter context manager."""
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> bool:
        """Exit context manager and handle any exceptions."""
        if exc_type is not None and exc_val is not None:
            if self.reraise:
                # Log and reraise
                if isinstance(exc_val, Exception):
                    self.error_handler.log_and_handle(exc_val, self.context)
                return False  # Let exception propagate
            # Log and suppress
            if isinstance(exc_val, Exception):
                self.error_handler.log_and_handle(exc_val, self.context)
            return True  # Suppress exception

        return False  # No exception occurred


def create_error_scope(
    logger: logging.Logger | None = None,
    context: dict[str, Any] | None = None,
    reraise: bool = True,
) -> ErrorScope:
    """Factory function to create an error scope with default error handler."""
    error_handler = _ScopeErrorHandler(logger)
    return ErrorScope(error_handler, context, reraise)
