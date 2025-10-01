#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error types, categories, and type definitions.

This module provides core type definitions for error handling including
severity levels, categories, and TypedDict schemas.
"""

from __future__ import annotations

from typing import Any, TypedDict

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


# Error schema types
class ErrorDetailInfo(TypedDict):
    """Error detail information."""

    error_type: str
    error_message: str


class ErrorSummaryData(TypedDict):
    """Error summary data."""

    count: int
    errors: list[dict[str, Any]]


class ErrorReportSummary(TypedDict):
    """Error report summary."""

    critical: dict[str, Any] | None
    trading: dict[str, Any] | None


class ErrorNotificationData(TypedDict):
    """Error notification data."""

    severity: str
    priority: str
    title: str
    error_report: str
    html_content: str
    success: bool
    email_sent: bool
    correlation_id: str | None
    event_id: str | None
