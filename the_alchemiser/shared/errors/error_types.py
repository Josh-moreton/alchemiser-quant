#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error types, categories, and type definitions.

This module serves as the central registry for error type definitions in a three-layer
architecture:
    1. Constants Layer (this file): ErrorSeverity and ErrorCategory enums
    2. Schema Layer (schemas/errors.py): Validated, immutable DTOs
    3. Handler Layer (error_handler.py, error_reporter.py): Business logic

The module provides:
    - ErrorSeverity: Severity level constants (LOW, MEDIUM, HIGH, CRITICAL)
    - ErrorCategory: Error classification categories (CRITICAL, TRADING, DATA, etc.)
    - Type aliases: ErrorData, ErrorList, ContextDict for flexible error metadata
    - Re-exports: ErrorDetailInfo, ErrorSummaryData, ErrorReportSummary, ErrorNotificationData

Usage:
    Severity levels::

        from the_alchemiser.shared.errors.error_types import ErrorSeverity

        if error_count > threshold:
            severity = ErrorSeverity.HIGH
        else:
            severity = ErrorSeverity.LOW

    Error categories::

        from the_alchemiser.shared.errors.error_types import ErrorCategory

        category = ErrorCategory.TRADING if is_order_error else ErrorCategory.DATA

    Error schemas (canonical import location)::

        from the_alchemiser.shared.schemas.errors import (
            ErrorDetailInfo,
            ErrorSummaryData,
            ErrorReportSummary,
            ErrorNotificationData,
        )

Note:
    ErrorSeverity and ErrorCategory values are designed to match the corresponding
    Literal types in shared.schemas.errors (SeverityType and ErrorCategoryType)
    for compile-time type safety.

"""

from __future__ import annotations

from enum import StrEnum

# Re-export canonical schemas from shared.schemas.errors
try:
    from the_alchemiser.shared.schemas.errors import (
        ErrorDetailInfo,
        ErrorNotificationData,
        ErrorReportSummary,
        ErrorSummaryData,
    )
except ImportError as e:
    # Provide clear error message if schemas are unavailable
    raise ImportError(
        "Failed to import error schemas from shared.schemas.errors. "
        "This likely indicates a circular import or missing dependency. "
        f"Original error: {e}"
    ) from e

# Explicit re-exports for backward compatibility
__all__ = [
    "ContextDict",
    "ErrorCategory",
    "ErrorData",
    "ErrorDetailInfo",
    "ErrorList",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSeverity",
    "ErrorSummaryData",
]

# Type aliases for error handler data structures

#: ErrorData represents flexible error metadata as a dictionary with primitive values.
#: Used throughout error handling code to attach context information to errors.
#: Keys are strings, values can be str, int, float, bool, or None.
#: Example: {"order_id": "12345", "retry_count": 3, "success": False}
ErrorData = dict[str, str | int | float | bool | None]

#: ErrorList is a list of ErrorData dictionaries, used to aggregate multiple errors.
#: Commonly used in error reporting to collect errors from batch operations.
#: Example: [{"error": "timeout", "code": 503}, {"error": "invalid", "code": 400}]
ErrorList = list[ErrorData]

#: ContextDict provides error context information with the same structure as ErrorData.
#: Used to pass contextual information about the operation when an error occurred.
#: Example: {"module": "execution_v2", "function": "place_order", "line": 123}
ContextDict = dict[str, str | int | float | bool | None]


class ErrorSeverity(StrEnum):
    """Error severity levels for production monitoring and alerting.

    This enum defines four severity levels used throughout the error handling
    system to prioritize errors and determine appropriate responses.

    Values:
        LOW: Minor issues that don't impact functionality (e.g., warnings, info messages).
        MEDIUM: Issues requiring attention but not urgent (e.g., degraded performance).
        HIGH: Serious issues requiring prompt attention (e.g., failed orders, data gaps).
        CRITICAL: System-level failures requiring immediate action (e.g., authentication
            failure, complete system outage).

    Examples:
        Basic severity assignment::

            from the_alchemiser.shared.errors.error_types import ErrorSeverity

            if connection_lost:
                severity = ErrorSeverity.CRITICAL
            elif retries_exhausted:
                severity = ErrorSeverity.HIGH
            elif slow_response:
                severity = ErrorSeverity.MEDIUM
            else:
                severity = ErrorSeverity.LOW

        Using in error notification::

            notification = ErrorNotificationData(
                severity=ErrorSeverity.HIGH,
                title="Trading Error",
                # ... other fields
            )

        Severity-based filtering::

            critical_errors = [
                e for e in errors
                if e.severity == ErrorSeverity.CRITICAL
            ]

    Note:
        Values match SeverityType Literal in shared.schemas.errors for type consistency.

    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(StrEnum):
    """Error categories for classification and routing.

    This enum defines seven categories used to classify errors by their origin
    and nature, enabling targeted error handling and reporting.

    Values:
        CRITICAL: System-level failures that stop all operations (e.g., authentication
            failure, database connection lost, critical infrastructure issues).
        TRADING: Order execution and position validation issues (e.g., order rejected,
            insufficient funds, position limit exceeded).
        DATA: Market data and API connectivity issues (e.g., missing price data, API
            rate limit, stale quotes, connection timeout).
        STRATEGY: Strategy calculation and signal generation issues (e.g., indicator
            calculation failure, signal generation error, invalid parameters).
        CONFIGURATION: Config, authentication, and setup issues (e.g., missing API key,
            invalid config value, environment variable not set).
        NOTIFICATION: Email and alert delivery issues (e.g., SMTP failure, webhook
            timeout, notification template error).
        WARNING: Non-critical issues that don't stop execution (e.g., minor data gaps,
            performance warnings, deprecation notices).

    Examples:
        Basic category assignment::

            from the_alchemiser.shared.errors.error_types import ErrorCategory

            if isinstance(error, OrderExecutionError):
                category = ErrorCategory.TRADING
            elif isinstance(error, MarketDataError):
                category = ErrorCategory.DATA
            elif isinstance(error, ConfigurationError):
                category = ErrorCategory.CONFIGURATION
            else:
                category = ErrorCategory.CRITICAL

        Using in error details::

            error_detail = ErrorDetailInfo(
                error_type="OrderExecutionError",
                error_message="Insufficient funds",
                category=ErrorCategory.TRADING,
                # ... other fields
            )

        Category-based routing::

            if error.category == ErrorCategory.CRITICAL:
                send_immediate_alert(error)
            elif error.category == ErrorCategory.TRADING:
                log_trading_issue(error)
            elif error.category == ErrorCategory.WARNING:
                log_warning(error)

    Note:
        Values match ErrorCategoryType Literal in shared.schemas.errors for type consistency.

    """

    CRITICAL = "critical"
    TRADING = "trading"
    DATA = "data"
    STRATEGY = "strategy"
    CONFIGURATION = "configuration"
    NOTIFICATION = "notification"
    WARNING = "warning"
