#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error reporting and notification DTOs for The Alchemiser Trading System.

This module contains Pydantic models for error handling, reporting, and notification
systems. Migrated from TypedDict to Pydantic for runtime validation and consistent
serialization with the event-driven architecture.

Schema Organization:
    - ErrorDetailInfo: Detailed information about a single error
    - ErrorSummaryData: Aggregated errors by category
    - ErrorReportSummary: System-wide error report (all categories)
    - ErrorNotificationData: Notification payload for alerts

Usage:
    Create error details::

        error = ErrorDetailInfo(
            error_type="ValueError",
            error_message="Invalid input",
            category="TRADING",
            context="order_execution",
            component="execution_v2",
            timestamp=datetime.now(UTC).isoformat(),
            traceback=traceback.format_exc(),
            schema_version="1.0"
        )

    Create error report::

        summary = ErrorSummaryData(count=1, errors=[error])
        report = ErrorReportSummary(trading=summary, schema_version="1.0")

    Create notification::

        notification = ErrorNotificationData(
            severity="high",
            priority="urgent",
            title="Trading Error",
            error_report="Error occurred",
            html_content="<p>Error</p>",
            success=True,
            email_sent=True,
            correlation_id="corr-123",
            schema_version="1.0"
        )
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Valid values for error categorization (aligned with ErrorCategory/ErrorSeverity)
ErrorCategoryType = Literal[
    "critical", "trading", "data", "strategy", "configuration", "notification", "warning"
]
SeverityType = Literal["low", "medium", "high", "critical"]

__all__ = [
    "ErrorCategoryType",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "SeverityType",
]


# Error Detail Types
class ErrorDetailInfo(BaseModel):
    r"""Detailed error information for reporting.

    Contains comprehensive information about a single error for
    detailed reporting and debugging.

    Schema Version: 1.0

    Fields:
        error_type: Exception class name (e.g., "ValueError", "OrderExecutionError").
        error_message: Human-readable error message.
        category: Error category for classification. Must be one of: "critical",
            "trading", "data", "strategy", "configuration", "notification", "warning".
        context: Serialized context information describing operation when error occurred.
        component: Component where error occurred (e.g., "execution_v2.executor").
        timestamp: ISO 8601 timestamp when error occurred. String format used for
            JSON serialization compatibility with event-driven architecture.
        traceback: Full Python traceback string for debugging.
        additional_data: Additional error metadata as key-value pairs. Uses dict[str, Any]
            for flexibility in error contexts where structure varies by error type.
        suggested_action: Optional recommended remediation action.
        schema_version: Schema version for compatibility tracking (default: "1.0").

    Examples:
        Basic error::

            error = ErrorDetailInfo(
                error_type="ValueError",
                error_message="Invalid quantity",
                category="trading",
                context="order_validation",
                component="execution_v2",
                timestamp="2025-10-08T12:00:00+00:00",
                traceback="Traceback (most recent call last):\\n...",
            )

        With additional data::

            error = ErrorDetailInfo(
                error_type="InsufficientFundsError",
                error_message="Account balance too low",
                category="trading",
                context="order_placement",
                component="execution_v2.executor",
                timestamp="2025-10-08T12:00:00+00:00",
                traceback="Traceback...",
                additional_data={"symbol": "AAPL", "required": 1000, "available": 500},
                suggested_action="Deposit more funds or reduce order size",
            )

    Pre-conditions:
        - timestamp must be valid ISO 8601 format
        - category must be one of the defined error categories
        - component should follow module.submodule naming convention

    Post-conditions:
        - Instance is immutable (frozen=True)
        - All required fields are validated
        - additional_data is empty dict if not provided

    Raises:
        ValidationError: If required fields are missing or invalid.

    """

    model_config = ConfigDict(strict=True, frozen=True)

    error_type: str = Field(description="Exception class name.")
    error_message: str = Field(description="Human-readable error message.")
    category: ErrorCategoryType = Field(
        description="Error category (critical, trading, data, strategy, configuration, notification, warning)."
    )
    context: str = Field(description="Serialized context information.")
    component: str = Field(description="Component where error occurred.")
    timestamp: str = Field(
        description="ISO 8601 timestamp. String format used for JSON serialization compatibility."
    )
    traceback: str = Field(description="Full Python traceback.")
    additional_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error metadata. Uses dict[str, Any] for flexibility in varying error contexts.",
    )
    suggested_action: str | None = Field(
        default=None, description="Recommended remediation action."
    )
    schema_version: Literal["1.0"] = Field(
        default="1.0", description="Schema version for compatibility tracking."
    )


class ErrorSummaryData(BaseModel):
    """Summary of errors by category.

    Aggregates multiple errors of the same category for reporting.

    Schema Version: 1.0

    Fields:
        count: Number of errors in this category (must be >= 0).
        errors: List of detailed error information for each error.
        schema_version: Schema version for compatibility tracking (default: "1.0").

    Examples:
        Empty summary::

            summary = ErrorSummaryData(count=0)

        With errors::

            error1 = ErrorDetailInfo(...)
            error2 = ErrorDetailInfo(...)
            summary = ErrorSummaryData(count=2, errors=[error1, error2])

    Pre-conditions:
        - count must be non-negative
        - count should match len(errors) for consistency

    Post-conditions:
        - Instance is immutable (frozen=True)
        - errors list is empty if not provided

    Raises:
        ValidationError: If count is negative or other validation fails.

    """

    model_config = ConfigDict(strict=True, frozen=True)

    count: int = Field(description="Number of errors in this category.", ge=0)
    errors: list[ErrorDetailInfo] = Field(
        default_factory=list, description="List of error details."
    )
    schema_version: Literal["1.0"] = Field(
        default="1.0", description="Schema version for compatibility tracking."
    )


class ErrorReportSummary(BaseModel):
    """Comprehensive error report summary.

    Top-level aggregation of all error categories for system-wide
    error reporting.

    Schema Version: 1.0

    Fields:
        critical: Critical system errors that stop all operations.
        trading: Trading execution errors (order placement, validation).
        data: Data provider/market data errors.
        strategy: Strategy execution errors (signal generation).
        configuration: Configuration errors (API keys, settings).
        notification: Notification system errors (email, alerts).
        warning: Warning-level issues (non-critical).
        schema_version: Schema version for compatibility tracking (default: "1.0").

    Examples:
        Report with multiple categories::

            report = ErrorReportSummary(
                trading=ErrorSummaryData(count=2, errors=[...]),
                data=ErrorSummaryData(count=1, errors=[...]),
            )

        Empty report::

            report = ErrorReportSummary()  # All categories None

    Pre-conditions:
        - At least one category should be populated for meaningful reports

    Post-conditions:
        - Instance is immutable (frozen=True)
        - All category fields default to None if not provided

    Raises:
        ValidationError: If validation of nested ErrorSummaryData fails.

    """

    model_config = ConfigDict(strict=True, frozen=True)

    critical: ErrorSummaryData | None = Field(default=None, description="Critical system errors.")
    trading: ErrorSummaryData | None = Field(default=None, description="Trading execution errors.")
    data: ErrorSummaryData | None = Field(
        default=None, description="Data provider/market data errors."
    )
    strategy: ErrorSummaryData | None = Field(
        default=None, description="Strategy execution errors."
    )
    configuration: ErrorSummaryData | None = Field(
        default=None, description="Configuration errors."
    )
    notification: ErrorSummaryData | None = Field(
        default=None, description="Notification system errors."
    )
    warning: ErrorSummaryData | None = Field(default=None, description="Warning-level issues.")
    schema_version: Literal["1.0"] = Field(
        default="1.0", description="Schema version for compatibility tracking."
    )


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

    Schema Version: 1.0

    Fields:
        severity: Error severity level. Must be one of: "low", "medium", "high", "critical".
        priority: Notification priority level (e.g., "urgent", "normal", "low").
        title: Notification title/subject line.
        error_report: Plain text error report content.
        html_content: HTML-formatted error content for rich email clients.
        success: Whether notification was successfully delivered.
        email_sent: Whether email was actually sent (may be False if using other channels).
        correlation_id: Event correlation ID for tracing across services.
        event_id: Specific event identifier for this notification.
        schema_version: Schema version for compatibility tracking (default: "1.0").

    Examples:
        Basic notification::

            notification = ErrorNotificationData(
                severity="high",
                priority="urgent",
                title="Trading Error",
                error_report="Error occurred during order execution",
                html_content="<p>Error details...</p>",
                success=True,
                email_sent=True,
            )

        With event tracing::

            notification = ErrorNotificationData(
                severity="critical",
                priority="urgent",
                title="System Failure",
                error_report="Critical system error",
                html_content="<html>...</html>",
                success=True,
                email_sent=True,
                correlation_id="workflow-123",
                event_id="error-456",
            )

    Pre-conditions:
        - severity must be one of the defined severity levels
        - correlation_id should be provided for event-driven workflows

    Post-conditions:
        - Instance is immutable (frozen=True)
        - All required fields are validated

    Raises:
        ValidationError: If required fields are missing or invalid.

    """

    model_config = ConfigDict(strict=True, frozen=True)

    severity: SeverityType = Field(
        description="Error severity level (low, medium, high, critical)."
    )
    priority: str = Field(description="Notification priority level.")
    title: str = Field(description="Notification title.")
    error_report: str = Field(description="Plain text error report.")
    html_content: str = Field(description="HTML-formatted error content.")
    success: bool = Field(description="Whether notification succeeded.")
    email_sent: bool = Field(description="Whether email was sent.")
    correlation_id: str | None = Field(default=None, description="Event correlation ID.")
    event_id: str | None = Field(default=None, description="Event identifier.")
    schema_version: Literal["1.0"] = Field(
        default="1.0", description="Schema version for compatibility tracking."
    )


# Deprecation notice for ErrorContextData
# NOTE: ErrorContextData now lives in shared/errors/context.py
# The TypedDict version here was deprecated in v2.18.0 and will be removed in v3.0.0
# Import from shared.errors.context instead:
#   from the_alchemiser.shared.errors.context import ErrorContextData
#
# For migration, replace:
#   from the_alchemiser.shared.schemas.errors import ErrorContextData
# With:
#   from the_alchemiser.shared.errors.context import ErrorContextData
