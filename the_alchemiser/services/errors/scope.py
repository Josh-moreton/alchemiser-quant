#!/usr/bin/env python3
"""
Error scope context manager for The Alchemiser Trading System.

This module provides context managers for error handling with automatic logging.
Renamed from ErrorContext to avoid naming collision.
"""

import logging
from typing import Any

from .error_handling import ErrorHandler


class ErrorScope:
    """Context manager for error handling with automatic logging."""

    def __init__(
        self,
        error_handler: ErrorHandler,
        context: dict[str, Any] | None = None,
        reraise: bool = True,
    ) -> None:
        """
        Initialize error scope.

        Args:
            error_handler: Error handler instance
            context: Logging context
            reraise: Whether to reraise exceptions
        """
        self.error_handler = error_handler
        self.context = context or {}
        self.reraise = reraise

    def __enter__(self) -> "ErrorScope":
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
            else:
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
    error_handler = ErrorHandler(logger)
    return ErrorScope(error_handler, context, reraise)
