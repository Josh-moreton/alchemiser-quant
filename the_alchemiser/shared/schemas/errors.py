#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Error reporting and notification DTOs for The Alchemiser Trading System.

This module contains Pydantic models for error handling, reporting, and notification
systems. Migrated from TypedDict to Pydantic for runtime validation and consistent
serialization with the event-driven architecture.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# Error Detail Types
class ErrorDetailInfo(BaseModel):
    """Detailed error information for reporting.

    Contains comprehensive information about a single error for
    detailed reporting and debugging.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    error_type: str = Field(description="Exception class name")
    error_message: str = Field(description="Human-readable error message")
    category: str = Field(description="Error category (CRITICAL, TRADING, DATA, etc.)")
    context: str = Field(description="Serialized context information")
    component: str = Field(description="Component where error occurred")
    timestamp: str = Field(description="ISO 8601 timestamp")
    traceback: str = Field(description="Full Python traceback")
    additional_data: dict[str, Any] = Field(
        default_factory=dict, description="Additional error metadata"
    )
    suggested_action: str | None = Field(default=None, description="Recommended remediation action")


class ErrorSummaryData(BaseModel):
    """Summary of errors by category.

    Aggregates multiple errors of the same category for reporting.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    count: int = Field(description="Number of errors in this category", ge=0)
    errors: list[ErrorDetailInfo] = Field(default_factory=list, description="List of error details")


class ErrorReportSummary(BaseModel):
    """Comprehensive error report summary.

    Top-level aggregation of all error categories for system-wide
    error reporting.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    critical: ErrorSummaryData | None = Field(default=None, description="Critical system errors")
    trading: ErrorSummaryData | None = Field(default=None, description="Trading execution errors")
    data: ErrorSummaryData | None = Field(
        default=None, description="Data provider/market data errors"
    )
    strategy: ErrorSummaryData | None = Field(default=None, description="Strategy execution errors")
    configuration: ErrorSummaryData | None = Field(default=None, description="Configuration errors")
    notification: ErrorSummaryData | None = Field(
        default=None, description="Notification system errors"
    )
    warning: ErrorSummaryData | None = Field(default=None, description="Warning-level issues")


# Error Notification Types
class ErrorNotificationData(BaseModel):
    """Data for error notifications.

    Contains formatted error information for sending via
    email, Slack, or other notification channels.

    Extended with workflow tracking fields for event-driven architecture:
    - success: Whether the notification was successfully delivered
    - email_sent: Whether the email was actually sent
    - correlation_id: Event correlation ID for tracing
    - event_id: Specific event identifier
    """

    model_config = ConfigDict(strict=True, frozen=True)

    severity: str = Field(description="Error severity level")
    priority: str = Field(description="Notification priority")
    title: str = Field(description="Notification title")
    error_report: str = Field(description="Plain text error report")
    html_content: str = Field(description="HTML-formatted error content")
    success: bool = Field(description="Whether notification succeeded")
    email_sent: bool = Field(description="Whether email was sent")
    correlation_id: str | None = Field(default=None, description="Event correlation ID")
    event_id: str | None = Field(default=None, description="Event identifier")


# NOTE: ErrorContextData now lives in shared/errors/context.py
# The TypedDict version here is deprecated and will be removed in v3.0.0
# Import from shared.errors.context instead:
#   from the_alchemiser.shared.errors.context import ErrorContextData
