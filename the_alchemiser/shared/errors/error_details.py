#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error details and categorization logic.

This module provides the ErrorDetails class for structured error information
and categorization logic for different error types.
"""

from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.logging import get_logger

from .error_types import ErrorCategory

logger = get_logger(__name__)

# Import exceptions
try:
    from the_alchemiser.shared.errors.exceptions import (
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
except ImportError as e:
    # Minimal fallback stubs (to avoid circular imports)
    # This is intentional: error_details.py is imported by exceptions.py
    # during exception class definitions, creating a circular dependency.
    # We use fallback stubs that match the interface for categorization.
    if "pytest" not in sys.modules:  # Only log in non-test environments
        logger.debug(
            "using_fallback_exception_stubs",
            reason="circular_import",
            error=str(e),
            module="error_details",
        )

    class AlchemiserError(Exception):  # type: ignore[no-redef]
        """Fallback AlchemiserError."""

        pass  # noqa: PIE790

    class ConfigurationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback ConfigurationError."""

        pass  # noqa: PIE790

    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback DataProviderError."""

        pass  # noqa: PIE790

    class InsufficientFundsError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback InsufficientFundsError."""

        pass  # noqa: PIE790

    class MarketDataError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback MarketDataError."""

        pass  # noqa: PIE790

    class NotificationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback NotificationError."""

        pass  # noqa: PIE790

    class OrderExecutionError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback OrderExecutionError."""

        pass  # noqa: PIE790

    class PositionValidationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback PositionValidationError."""

        pass  # noqa: PIE790

    class TradingClientError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback TradingClientError."""

        pass  # noqa: PIE790


def _is_strategy_execution_error(err: Exception) -> bool:
    """Detect strategy execution errors without cross-module imports.

    We avoid importing from `strategy_v2` inside `shared` to respect
    module boundaries. Instead, we detect by class name to categorize.

    Args:
        err: Exception instance to check

    Returns:
        True if the exception is a StrategyExecutionError, False otherwise
    """
    return err.__class__.__name__ == "StrategyExecutionError"


@dataclass(frozen=True)
class ErrorDetails:
    """Detailed error information for reporting.

    This class captures comprehensive error metadata for structured reporting,
    categorization, and incident response. All instances are immutable to ensure
    error details cannot be modified after creation.

    Attributes:
        error: The exception instance
        category: Error category (from ErrorCategory constants)
        context: Contextual description (e.g., "order placement", "data fetch")
        component: Component where error occurred (e.g., "execution_v2", "strategy")
        additional_data: Extra metadata (symbol, quantity, etc.)
        suggested_action: Recommended remediation action
        error_code: Machine-readable error code (e.g., "TRD_INSUFFICIENT_FUNDS")
        timestamp: UTC timestamp when error was captured
        traceback: Python traceback string

    Examples:
        Basic error::

            details = ErrorDetails(
                error=ValueError("Invalid quantity"),
                category=ErrorCategory.TRADING,
                context="order_validation",
                component="execution_v2",
            )

        With additional data::

            details = ErrorDetails(
                error=InsufficientFundsError("Balance too low"),
                category=ErrorCategory.TRADING,
                context="order_placement",
                component="execution_v2",
                additional_data={"symbol": "AAPL", "required": 1000, "available": 500},
                suggested_action="Deposit funds or reduce order size",
                error_code="TRD_INSUFFICIENT_FUNDS",
            )
    """

    error: Exception
    category: str
    context: str
    component: str
    additional_data: dict[str, Any] = field(default_factory=dict)
    suggested_action: str | None = None
    error_code: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    traceback: str = field(default_factory=traceback.format_exc)

    def to_dict(self) -> dict[str, Any]:
        """Convert error details to dictionary for serialization.

        Returns:
            Dictionary with error details, including schema_version for compatibility.

        Examples:
            >>> details = ErrorDetails(...)
            >>> result = details.to_dict()
            >>> assert result["schema_version"] == "1.0"
        """
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
            "schema_version": "1.0",
        }


def categorize_by_exception_type(error: Exception) -> str | None:
    """Categorize error based purely on exception type.

    This function examines the exception type and maps it to an error category.
    It checks specific exception types first, then falls back to base classes.

    Args:
        error: Exception instance to categorize

    Returns:
        Error category string if type is recognized, None otherwise.
        Returns None for unknown exceptions to allow context-based categorization.

    Examples:
        >>> categorize_by_exception_type(InsufficientFundsError("low balance"))
        'trading'

        >>> categorize_by_exception_type(MarketDataError("API down"))
        'data'

        >>> categorize_by_exception_type(ValueError("unknown"))
        None
    """
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
    """Categorize error based on context keywords.

    This function provides fallback categorization when exception type is unknown.
    It searches for keywords in the context string to infer the error category.

    Args:
        context: Contextual string describing where the error occurred
                 (e.g., "order placement", "data fetch", "strategy calculation")

    Returns:
        Error category string. Defaults to CRITICAL for unknown contexts
        as a fail-safe approach.

    Notes:
        - Keyword matching is case-insensitive
        - Priority order: trading/order → data/price → strategy/signal → config/auth → critical

    Examples:
        >>> categorize_by_context("trading operation failed")
        'trading'

        >>> categorize_by_context("data fetch failed")
        'data'

        >>> categorize_by_context("unknown operation")
        'critical'
    """
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
    """Categorize error based on type and context.

    This is the main entry point for error categorization. It applies a priority-based
    approach: exception type takes precedence over context-based categorization.

    Args:
        error: Exception instance to categorize
        context: Optional contextual string for fallback categorization

    Returns:
        Error category string from ErrorCategory constants

    Notes:
        - Exception type categorization is attempted first
        - TradingClientError is an AlchemiserError subclass and gets CRITICAL by default
        - For unknown exceptions, falls back to context-based categorization
        - Always returns a valid category (never None)

    Examples:
        >>> categorize_error(InsufficientFundsError("low funds"), "data fetch")
        'trading'  # Exception type wins over context

        >>> categorize_error(ValueError("error"), "strategy calculation")
        'strategy'  # Falls back to context

        >>> categorize_error(ValueError("error"), "")
        'critical'  # Default for unknown context
    """
    # First try categorization by exception type
    category = categorize_by_exception_type(error)
    if category:
        logger.debug(
            "error_categorized_by_type",
            error_type=type(error).__name__,
            category=category,
            context=context,
        )
        return category

    # For non-Alchemiser exceptions, categorize by context
    result = categorize_by_context(context)
    logger.debug(
        "error_categorized_by_context",
        error_type=type(error).__name__,
        category=result,
        context=context,
    )
    return result


def get_suggested_action(error: Exception, category: str) -> str:
    """Get suggested action based on error type and category.

    This function provides human-readable remediation guidance for different
    error types and categories. It checks specific exception types first,
    then falls back to category-based suggestions.

    Args:
        error: Exception instance that occurred
        category: Error category from ErrorCategory constants

    Returns:
        Human-readable suggested action string for remediation

    Examples:
        >>> get_suggested_action(InsufficientFundsError("low"), ErrorCategory.TRADING)
        'Check account balance and reduce position sizes or add funds'

        >>> get_suggested_action(ValueError("unknown"), ErrorCategory.DATA)
        'Check market data sources, API limits, and network connectivity'
    """
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
