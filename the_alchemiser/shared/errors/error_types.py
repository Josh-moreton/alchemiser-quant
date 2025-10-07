#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Error types, categories, and type definitions.

This module provides core type definitions for error handling including
severity levels, categories, and Pydantic schemas.

NOTE: The TypedDict definitions here are deprecated and will be removed in v3.0.0.
Use the canonical Pydantic models from shared.schemas.errors instead:
    from the_alchemiser.shared.schemas.errors import (
        ErrorDetailInfo,
        ErrorSummaryData,
        ErrorReportSummary,
        ErrorNotificationData,
    )
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

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


# Minimal error schema types (prefer importing from shared.schemas.errors)
class ErrorDetailInfo(BaseModel):
    """Error detail information (minimal version).

    DEPRECATED: Use the_alchemiser.shared.schemas.errors.ErrorDetailInfo instead.
    This simplified version exists for backward compatibility.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    error_type: str = Field(description="Exception class name")
    error_message: str = Field(description="Human-readable error message")


class ErrorSummaryData(BaseModel):
    """Error summary data (minimal version).

    DEPRECATED: Use the_alchemiser.shared.schemas.errors.ErrorSummaryData instead.
    This simplified version exists for backward compatibility.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    count: int = Field(description="Number of errors", ge=0)
    errors: list[dict[str, Any]] = Field(default_factory=list, description="List of error details")


class ErrorReportSummary(BaseModel):
    """Error report summary (minimal version).

    DEPRECATED: Use the_alchemiser.shared.schemas.errors.ErrorReportSummary instead.
    This simplified version exists for backward compatibility.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    critical: dict[str, Any] | None = Field(default=None, description="Critical errors")
    trading: dict[str, Any] | None = Field(default=None, description="Trading errors")


class ErrorNotificationData(BaseModel):
    """Error notification data (extended version).

    NOTE: This version includes extra fields (success, email_sent, correlation_id, event_id)
    not present in shared.schemas.errors.ErrorNotificationData.
    Consider using the canonical version for new code.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    severity: str = Field(description="Error severity level")
    priority: str = Field(description="Notification priority")
    title: str = Field(description="Notification title")
    error_report: str = Field(description="Plain text error report")
    html_content: str = Field(description="HTML-formatted content")
    success: bool = Field(description="Whether notification succeeded")
    email_sent: bool = Field(description="Whether email was sent")
    correlation_id: str | None = Field(default=None, description="Event correlation ID")
    event_id: str | None = Field(default=None, description="Event identifier")
