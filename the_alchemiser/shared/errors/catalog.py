#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Central Error Catalogue for The Alchemiser Trading System.

This module provides a single, authoritative source for error codes, categories,
severity levels, and remediation guidance. It enables consistent error handling,
filtering, and routing throughout the system.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ErrorCode(Enum):
    """Enumeration of standardized error codes for the trading system."""

    # Trading execution errors
    TRD_MARKET_CLOSED = "TRD_MARKET_CLOSED"
    TRD_INSUFFICIENT_FUNDS = "TRD_INSUFFICIENT_FUNDS"
    TRD_ORDER_TIMEOUT = "TRD_ORDER_TIMEOUT"
    TRD_BUYING_POWER = "TRD_BUYING_POWER"

    # Data provider errors
    DATA_RATE_LIMIT = "DATA_RATE_LIMIT"
    DATA_PROVIDER_FAILURE = "DATA_PROVIDER_FAILURE"

    # Configuration errors
    CONF_MISSING_ENV = "CONF_MISSING_ENV"
    CONF_INVALID_VALUE = "CONF_INVALID_VALUE"

    # Notification errors
    NOTIF_SMTP_FAILURE = "NOTIF_SMTP_FAILURE"


class ErrorSpec(BaseModel):
    """Specification for an error code with metadata and guidance.

    Provides categorization, severity, retry guidance, and remediation hints
    for consistent error handling across the system.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    code: ErrorCode = Field(..., description="The error code")
    category: str = Field(..., description="Error category for classification")
    default_severity: str = Field(..., description="Default severity level")
    retryable: bool = Field(..., description="Whether this error can be retried")
    message_template: str = Field(..., description="Template for error messages")
    suggested_action: str = Field(..., description="Recommended remediation action")
    doc_url: str | None = Field(default=None, description="Link to documentation")


# Central error catalogue mapping codes to specifications
ERROR_CATALOG: dict[ErrorCode, ErrorSpec] = {
    ErrorCode.TRD_MARKET_CLOSED: ErrorSpec(
        code=ErrorCode.TRD_MARKET_CLOSED,
        category="trading",
        default_severity="medium",
        retryable=True,
        message_template="Cannot execute trades while market is closed",
        suggested_action="Wait for market open or check trading hours",
        doc_url=None,
    ),
    ErrorCode.TRD_INSUFFICIENT_FUNDS: ErrorSpec(
        code=ErrorCode.TRD_INSUFFICIENT_FUNDS,
        category="trading",
        default_severity="high",
        retryable=False,
        message_template="Insufficient funds for order execution",
        suggested_action="Check account balance and reduce position sizes",
        doc_url=None,
    ),
    ErrorCode.TRD_ORDER_TIMEOUT: ErrorSpec(
        code=ErrorCode.TRD_ORDER_TIMEOUT,
        category="trading",
        default_severity="medium",
        retryable=True,
        message_template="Order execution timed out",
        suggested_action="Check market conditions and retry with adjusted parameters",
        doc_url=None,
    ),
    ErrorCode.TRD_BUYING_POWER: ErrorSpec(
        code=ErrorCode.TRD_BUYING_POWER,
        category="trading",
        default_severity="high",
        retryable=False,
        message_template="Insufficient buying power for order",
        suggested_action="Reduce order size or wait for settlement",
        doc_url=None,
    ),
    ErrorCode.DATA_RATE_LIMIT: ErrorSpec(
        code=ErrorCode.DATA_RATE_LIMIT,
        category="data",
        default_severity="medium",
        retryable=True,
        message_template="API rate limit exceeded",
        suggested_action="Wait for rate limit reset and reduce request frequency",
        doc_url=None,
    ),
    ErrorCode.DATA_PROVIDER_FAILURE: ErrorSpec(
        code=ErrorCode.DATA_PROVIDER_FAILURE,
        category="data",
        default_severity="high",
        retryable=True,
        message_template="Data provider service failure",
        suggested_action="Check provider status and retry with exponential backoff",
        doc_url=None,
    ),
    ErrorCode.CONF_MISSING_ENV: ErrorSpec(
        code=ErrorCode.CONF_MISSING_ENV,
        category="configuration",
        default_severity="critical",
        retryable=False,
        message_template="Required environment variable not set",
        suggested_action="Set missing environment variables and restart application",
        doc_url=None,
    ),
    ErrorCode.CONF_INVALID_VALUE: ErrorSpec(
        code=ErrorCode.CONF_INVALID_VALUE,
        category="configuration",
        default_severity="high",
        retryable=False,
        message_template="Configuration value is invalid",
        suggested_action="Correct configuration value and restart application",
        doc_url=None,
    ),
    ErrorCode.NOTIF_SMTP_FAILURE: ErrorSpec(
        code=ErrorCode.NOTIF_SMTP_FAILURE,
        category="notification",
        default_severity="low",
        retryable=True,
        message_template="Email notification failed to send",
        suggested_action="Check SMTP configuration and network connectivity",
        doc_url=None,
    ),
}


def map_exception_to_error_code(exc: Exception) -> ErrorCode | None:
    """Map a known exception to its corresponding error code.

    Maps domain exceptions from shared/types/exceptions.py to standardized
    error codes for consistent handling and reporting.

    Args:
        exc: The exception to map

    Returns:
        The corresponding ErrorCode if known, None otherwise

    """
    # Import here to avoid circular imports
    from the_alchemiser.shared.errors.exceptions import (
        BuyingPowerError,
        ConfigurationError,
        DataProviderError,
        EnvironmentError,
        InsufficientFundsError,
        MarketClosedError,
        MarketDataError,
        NotificationError,
        OrderTimeoutError,
        RateLimitError,
    )

    # Trading execution errors
    if isinstance(exc, MarketClosedError):
        return ErrorCode.TRD_MARKET_CLOSED
    if isinstance(exc, InsufficientFundsError):
        return ErrorCode.TRD_INSUFFICIENT_FUNDS
    if isinstance(exc, OrderTimeoutError):
        return ErrorCode.TRD_ORDER_TIMEOUT
    if isinstance(exc, BuyingPowerError):
        return ErrorCode.TRD_BUYING_POWER

    # Data provider errors
    if isinstance(exc, RateLimitError):
        return ErrorCode.DATA_RATE_LIMIT
    if isinstance(exc, (DataProviderError, MarketDataError)):
        return ErrorCode.DATA_PROVIDER_FAILURE

    # Configuration errors
    if isinstance(exc, EnvironmentError):
        return ErrorCode.CONF_MISSING_ENV
    if isinstance(exc, ConfigurationError):
        return ErrorCode.CONF_INVALID_VALUE

    # Notification errors
    if isinstance(exc, NotificationError):
        return ErrorCode.NOTIF_SMTP_FAILURE

    # Return None for unknown exception types
    return None


def get_error_spec(error_code: ErrorCode) -> ErrorSpec:
    """Get the error specification for a given error code.

    Args:
        error_code: The error code to look up

    Returns:
        The ErrorSpec for the given code

    Raises:
        KeyError: If the error code is not found in the catalogue

    """
    return ERROR_CATALOG[error_code]


def get_suggested_action(error_code: ErrorCode) -> str:
    """Get the suggested remediation action for an error code.

    Args:
        error_code: The error code to get action for

    Returns:
        Suggested action string

    """
    return ERROR_CATALOG[error_code].suggested_action
