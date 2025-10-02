#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error details and categorization logic.

This module provides the ErrorDetails class for structured error information
and categorization logic for different error types.
"""

from __future__ import annotations

import traceback
from datetime import UTC, datetime
from typing import Any

from .error_types import ErrorCategory

# Import exceptions
try:
    from the_alchemiser.shared.types.exceptions import (
        AlchemiserError,
        ConfigurationError,
        DataProviderError,
        InsufficientFundsError,
        MarketDataError,
        NotificationError,
        OrderExecutionError,
        PositionValidationError,
        TradingClientError,
    )
except ImportError:
    # Minimal fallback stubs (to avoid circular imports)
    class AlchemiserError(Exception):  # type: ignore[no-redef]
        """Fallback AlchemiserError."""

    class ConfigurationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback ConfigurationError."""

    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback DataProviderError."""

    class InsufficientFundsError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback InsufficientFundsError."""

    class MarketDataError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback MarketDataError."""

    class NotificationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback NotificationError."""

    class OrderExecutionError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback OrderExecutionError."""

    class PositionValidationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback PositionValidationError."""

    class TradingClientError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback TradingClientError."""


def _is_strategy_execution_error(err: Exception) -> bool:
    """Detect strategy execution errors without cross-module imports.

    We avoid importing from `strategy_v2` inside `shared` to respect
    module boundaries. Instead, we detect by class name to categorize.
    """
    return err.__class__.__name__ == "StrategyExecutionError"


class ErrorDetails:
    """Detailed error information for reporting."""

    def __init__(
        self,
        error: Exception,
        category: str,
        context: str,
        component: str,
        additional_data: dict[str, Any] | None = None,
        suggested_action: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Store detailed error information."""
        self.error = error
        self.category = category
        self.context = context
        self.component = component
        self.additional_data = additional_data or {}
        self.suggested_action = suggested_action
        self.error_code = error_code
        self.timestamp = datetime.now(UTC)
        self.traceback = traceback.format_exc()

    def to_dict(self) -> dict[str, Any]:
        """Convert error details to dictionary for serialization."""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "category": self.category,
            "context": self.context,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback,
            "additional_data": self.additional_data,
            "suggested_action": self.suggested_action,
            "error_code": self.error_code,
        }


def categorize_by_exception_type(error: Exception) -> str | None:
    """Categorize error based purely on exception type."""
    if isinstance(
        error,
        InsufficientFundsError | OrderExecutionError | PositionValidationError,
    ):
        return ErrorCategory.TRADING
    if isinstance(error, MarketDataError | DataProviderError):
        return ErrorCategory.DATA
    if _is_strategy_execution_error(error):
        return ErrorCategory.STRATEGY
    if isinstance(error, ConfigurationError):
        return ErrorCategory.CONFIGURATION
    if isinstance(error, NotificationError):
        return ErrorCategory.NOTIFICATION
    if isinstance(error, AlchemiserError):
        return ErrorCategory.CRITICAL
    return None


def categorize_by_context(context: str) -> str:
    """Categorize error based on context keywords."""
    context_lower = context.lower()
    if "trading" in context_lower or "order" in context_lower:
        return ErrorCategory.TRADING
    if "data" in context_lower or "price" in context_lower:
        return ErrorCategory.DATA
    if "strategy" in context_lower or "signal" in context_lower:
        return ErrorCategory.STRATEGY
    if "config" in context_lower or "auth" in context_lower:
        return ErrorCategory.CONFIGURATION
    return ErrorCategory.CRITICAL


def categorize_error(error: Exception, context: str = "") -> str:
    """Categorize error based on type and context."""
    # First try categorization by exception type
    category = categorize_by_exception_type(error)
    if category:
        return category

    # Handle TradingClientError with context dependency
    if isinstance(error, TradingClientError):
        context_lower = context.lower()
        if "order" in context_lower or "position" in context_lower:
            return ErrorCategory.TRADING
        return ErrorCategory.DATA

    # For non-Alchemiser exceptions, categorize by context
    return categorize_by_context(context)


def get_suggested_action(error: Exception, category: str) -> str:
    """Get suggested action based on error type and category."""
    if isinstance(error, InsufficientFundsError):
        return "Check account balance and reduce position sizes or add funds"
    if isinstance(error, OrderExecutionError):
        return "Verify market hours, check symbol validity, and ensure order parameters are correct"
    if isinstance(error, PositionValidationError):
        return "Check current positions and ensure selling quantities don't exceed holdings"
    if isinstance(error, MarketDataError):
        return "Check API connectivity and data provider status"
    if isinstance(error, ConfigurationError):
        return "Verify configuration settings and API credentials"
    if _is_strategy_execution_error(error):
        return "Review strategy logic and input data for calculation errors"
    if category == ErrorCategory.DATA:
        return "Check market data sources, API limits, and network connectivity"
    if category == ErrorCategory.TRADING:
        return "Verify trading permissions, account status, and market hours"
    if category == ErrorCategory.CRITICAL:
        return "Review system logs, check AWS permissions, and verify deployment configuration"
    return "Review logs for detailed error information and contact support if needed"
