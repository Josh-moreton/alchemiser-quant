#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Error reporting and notification DTOs for The Alchemiser Trading System.

This module contains DTOs for error handling, reporting, and notification
systems, moved from domain/types.py as part of the Pydantic migration.
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


# Error Detail Types
class ErrorDetailInfo(TypedDict):
    """Detailed error information for reporting."""

    error_type: str
    error_message: str
    category: str
    context: str
    component: str
    timestamp: str
    traceback: str
    additional_data: dict[str, Any]
    suggested_action: str | None


class ErrorSummaryData(TypedDict):
    """Summary of errors by category."""

    count: int
    errors: list[ErrorDetailInfo]


class ErrorReportSummary(TypedDict):
    """Comprehensive error report summary."""

    critical: ErrorSummaryData | None
    trading: ErrorSummaryData | None
    data: ErrorSummaryData | None
    strategy: ErrorSummaryData | None
    configuration: ErrorSummaryData | None
    notification: ErrorSummaryData | None
    warning: ErrorSummaryData | None


# Error Notification Types
class ErrorNotificationData(TypedDict):
    """Data for error notifications."""

    severity: str
    priority: str
    title: str
    error_report: str
    html_content: str


class ErrorContextData(TypedDict):
    """Context information for error tracking."""

    operation: str
    component: str
    function_name: str | None
    request_id: str | None
    user_id: str | None
    session_id: str | None
    additional_data: dict[str, Any]
    timestamp: str
