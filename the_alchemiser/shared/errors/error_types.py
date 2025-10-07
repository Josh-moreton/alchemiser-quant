#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error types, categories, and type definitions.

This module provides core type definitions for error handling including
severity levels and categories. Schema classes are now re-exported from
shared.schemas.errors for consistency.

For error schemas, import from the canonical location:
    from the_alchemiser.shared.schemas.errors import (
        ErrorDetailInfo,
        ErrorSummaryData,
        ErrorReportSummary,
        ErrorNotificationData,
    )
"""

from __future__ import annotations

# Re-export canonical schemas from shared.schemas.errors
from the_alchemiser.shared.schemas.errors import (
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)

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
ErrorData = dict[str, str | int | float | bool | None]
ErrorList = list[ErrorData]
ContextDict = dict[str, str | int | float | bool | None]


class ErrorSeverity:
    """Error severity levels for production monitoring."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory:
    """Error categories for classification and handling."""

    CRITICAL = "critical"  # System-level failures that stop all operations
    TRADING = "trading"  # Order execution, position validation issues
    DATA = "data"  # Market data, API connectivity issues
    STRATEGY = "strategy"  # Strategy calculation, signal generation issues
    CONFIGURATION = "configuration"  # Config, authentication, setup issues
    NOTIFICATION = "notification"  # Email, alert delivery issues
    WARNING = "warning"  # Non-critical issues that don't stop execution


# NOTE: Schema classes (ErrorDetailInfo, ErrorSummaryData, ErrorReportSummary,
# ErrorNotificationData) are re-exported from shared.schemas.errors above.
# Use those imports instead of defining duplicates here.
