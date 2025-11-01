#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Main error handler for The Alchemiser Trading System.

This module provides the single facade TradingSystemErrorHandler for all error handling,
categorization, and detailed error reporting via email notifications.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.errors import ErrorNotificationData

# Import from decomposed modules
from .error_details import (
    ErrorDetails,
    categorize_error,
    get_suggested_action,
)
from .error_reporter import (
    get_global_error_reporter,
)
from .error_types import (
    ErrorCategory,
)
from .error_utils import (
    retry_with_backoff,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.events.bus import EventBus

    from .context import ErrorContextData

# Module-level logger (defined early for use in fallback exception imports)
logger = get_logger(__name__)

# Import additional error types
try:
    from .trading_errors import (
        OrderError,
        classify_exception,
    )
except ImportError:
    logger.warning(
        "Failed to import trading_errors module, using fallback implementations. "
        "This may indicate a circular import or missing dependency.",
        extra={"module": "error_handler", "fallback": "OrderError"},
    )

    class OrderError(Exception):  # type: ignore[no-redef]
        """Fallback OrderError."""

        def __init__(self, message: str = "Unknown order error") -> None:
            """Initialize OrderError."""
            super().__init__(message)
            self.message = message
            self.category = type("Category", (), {"value": "UNKNOWN"})()
            self.code = type("Code", (), {"value": "UNKNOWN"})()
            self.is_transient = False
            self.order_id: str | None = None

    from typing import Literal

    def classify_exception(
        exception: Exception,
    ) -> Literal["order_error", "alchemiser_error", "general_error"]:
        """Fallback classify_exception."""
        return exception.__class__.__name__  # type: ignore[return-value]


# Import AlchemiserError for type checking
try:
    from the_alchemiser.shared.errors.exceptions import (
        AlchemiserError,
        DataProviderError,
        TradingClientError,
    )
except ImportError:
    logger.warning(
        "Failed to import exceptions module, using fallback implementations. "
        "This may indicate a circular import or missing dependency.",
        extra={"module": "error_handler", "fallback": "AlchemiserError"},
    )

    class AlchemiserError(Exception):  # type: ignore[no-redef]
        """Fallback AlchemiserError."""

    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback DataProviderError."""

    class TradingClientError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback TradingClientError."""


# Sensitive keys that should be redacted from error reports
SENSITIVE_KEYS = {
    "password",
    "token",
    "api_key",
    "secret",
    "auth",
    "authorization",
    "credentials",
    "account_id",
}

# Maximum number of errors to store to prevent unbounded memory growth
MAX_ERRORS = 100


class TradingSystemErrorHandler:
    """Enhanced error handler for autonomous trading operations.

    Thread Safety:
        This class maintains mutable state (self.errors list). For single-threaded
        Lambda execution, this is safe. For multi-threaded use, external synchronization
        is required.

    Note:
        The global _error_handler instance is suitable for Lambda functions where
        each invocation gets a fresh process. For long-running processes, consider
        using get_error_handler() to obtain a new instance periodically.

    """

    def __init__(self) -> None:
        """Create a new error handler with empty history."""
        self.errors: list[ErrorDetails] = []
        # Use module-level logger instead of creating a duplicate instance

    def categorize_error(self, error: Exception, context: str = "") -> str:
        """Categorize error based on type and context."""
        return categorize_error(error, context)

    def get_suggested_action(self, error: Exception, category: str) -> str:
        """Get suggested action based on error type and category."""
        return get_suggested_action(error, category)

    def handle_error(
        self,
        error: Exception,
        context: str,
        component: str,
        additional_data: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> ErrorDetails:
        """Handle an error with detailed logging and categorization.

        Args:
            error: The exception that occurred
            context: Context description (e.g., "order execution", "data fetch")
            component: Component name (e.g., "execution_v2", "strategy_v2")
            additional_data: Optional additional context data. Will be redacted for
                sensitive information before logging.
            correlation_id: Request/workflow correlation ID for tracing (optional)
            causation_id: Triggering event ID for event chains (optional)

        Returns:
            ErrorDetails instance with categorization and suggested action

        Note:
            Errors are accumulated in self.errors list up to MAX_ERRORS (100).
            Older errors are dropped when the limit is reached.

            correlation_id and causation_id are extracted from additional_data
            if not explicitly provided, following event-driven architecture patterns.

        """
        from .catalog import map_exception_to_error_code

        category = self.categorize_error(error, context)
        suggested_action = self.get_suggested_action(error, category)

        # Map exception to error code from catalogue
        error_code_enum = map_exception_to_error_code(error)
        error_code = error_code_enum.value if error_code_enum else None

        error_details = ErrorDetails(
            error=error,
            category=category,
            context=context,
            component=component,
            additional_data=additional_data or {},
            suggested_action=suggested_action,
            error_code=error_code,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        # Enforce maximum error count to prevent unbounded memory growth
        if len(self.errors) >= MAX_ERRORS:
            logger.warning(
                f"Error list at maximum capacity ({MAX_ERRORS}), dropping oldest error",
                extra={"extra_fields": {"error_count": len(self.errors)}},
            )
            self.errors.pop(0)  # Remove oldest error

        self.errors.append(error_details)

        # Log with appropriate level and include error_code, correlation_id, causation_id
        log_extra = {
            "error_code": error_code,
            "correlation_id": error_details.correlation_id,
            "causation_id": error_details.causation_id,
        }
        # Remove None values from log_extra
        log_extra = {k: v for k, v in log_extra.items() if v is not None}

        if category == ErrorCategory.CRITICAL:
            logger.critical(
                f"CRITICAL ERROR in {component}: {error}",
                exc_info=True,
                extra={"extra_fields": log_extra},
            )
        elif category in [
            ErrorCategory.TRADING,
            ErrorCategory.DATA,
            ErrorCategory.STRATEGY,
        ]:
            logger.error(
                f"{category.upper()} ERROR in {component}: {error}",
                exc_info=True,
                extra={"extra_fields": log_extra},
            )
        elif category == ErrorCategory.CONFIGURATION:
            logger.error(
                f"CONFIGURATION ERROR in {component}: {error}",
                exc_info=True,
                extra={"extra_fields": log_extra},
            )
        else:
            logger.warning(
                f"{category.upper()} in {component}: {error}",
                extra={"extra_fields": log_extra},
            )

        return error_details

    def handle_error_with_context(
        self,
        error: Exception,
        context: ErrorContextData,
    ) -> ErrorDetails:
        """Handle error with structured context."""
        return self.handle_error(
            error=error,
            context=context.operation or "unknown",
            component=context.module or "unknown",
            additional_data=context.to_dict(),
        )

    def has_critical_errors(self) -> bool:
        """Check if any critical errors occurred."""
        return any(error.category == ErrorCategory.CRITICAL for error in self.errors)

    def has_trading_errors(self) -> bool:
        """Check if any trading-related errors occurred."""
        return any(error.category == ErrorCategory.TRADING for error in self.errors)

    def _get_category_summary(self, category: str) -> dict[str, Any] | None:
        """Get error summary for a specific category.

        Args:
            category: The error category constant to filter by

        Returns:
            Category summary dict with count and errors, or None if no errors

        """
        category_errors = [e for e in self.errors if e.category == category]
        if category_errors:
            return {
                "count": len(category_errors),
                "errors": [e.to_dict() for e in category_errors],
            }
        return None

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all errors by category."""
        # Define category mappings to reduce repetition
        category_mappings = [
            (ErrorCategory.CRITICAL, "critical"),
            (ErrorCategory.TRADING, "trading"),
            (ErrorCategory.DATA, "data"),
            (ErrorCategory.STRATEGY, "strategy"),
            (ErrorCategory.CONFIGURATION, "configuration"),
            (ErrorCategory.NOTIFICATION, "notification"),
            (ErrorCategory.WARNING, "warning"),
        ]

        # Initialize summary with all categories as None
        summary: dict[str, Any] = dict.fromkeys(key for _, key in category_mappings)

        # Process each category using the helper function
        for category, summary_key in category_mappings:
            summary[summary_key] = self._get_category_summary(category)

        return summary

    def should_send_error_email(self) -> bool:
        """Determine if an error email should be sent."""
        # Send email for any errors except pure notification errors
        non_notification_errors = [
            e for e in self.errors if e.category != ErrorCategory.NOTIFICATION
        ]
        return len(non_notification_errors) > 0

    def _redact_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from error context.

        Args:
            data: The data dictionary to redact

        Returns:
            New dictionary with sensitive keys redacted

        """
        redacted_data: dict[str, Any] = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS:
                redacted_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                # Recursively redact nested dictionaries
                redacted_data[key] = self._redact_sensitive_data(value)
            else:
                redacted_data[key] = value
        return redacted_data

    def _format_error_entry(self, error: dict[str, Any]) -> str:
        """Format a single error entry for the report.

        Note:
            Sensitive data in additional_data is redacted before formatting
            to prevent leaking secrets, API keys, or account IDs in email notifications.

        """
        entry = f"**Component:** {error['component']}\n"
        entry += f"**Context:** {error['context']}\n"
        entry += f"**Error:** {error['error_message']}\n"
        entry += f"**Action:** {error['suggested_action']}\n"
        if error["additional_data"]:
            # Redact sensitive data before including in report
            redacted_data = self._redact_sensitive_data(error["additional_data"])
            entry += f"**Additional Data:** {redacted_data}\n"
        entry += "\n"
        return entry

    def _add_error_section(
        self,
        report: str,
        category_data: dict[str, Any] | None,
        title: str,
        description: str = "",
    ) -> str:
        """Add an error section to the report if the category has errors."""
        if category_data is None:
            return report

        section = f"## {title}\n"
        if description:
            section += f"{description}\n\n"

        for error in category_data["errors"]:
            section += self._format_error_entry(error)

        return report + section

    def generate_error_report(self) -> str:
        """Generate a detailed error report for email notification."""
        if not self.errors:
            return "No errors to report."

        summary = self.get_error_summary()

        # Build report header
        report = "# Trading System Error Report\n\n"
        report += f"**Execution Time:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        report += f"**Total Errors:** {len(self.errors)}\n\n"

        # Add error sections in priority order
        report = self._add_error_section(
            report,
            summary["critical"],
            "🚨 CRITICAL ERRORS",
            "These errors stopped system execution and require immediate attention:",
        )
        report = self._add_error_section(
            report,
            summary["trading"],
            "💰 TRADING ERRORS",
            "These errors affected trade execution:",
        )
        report = self._add_error_section(report, summary["data"], "📊 DATA ERRORS")
        report = self._add_error_section(report, summary["strategy"], "🧠 STRATEGY ERRORS")
        return self._add_error_section(report, summary["configuration"], "⚙️ CONFIGURATION ERRORS")

    def classify_order_error(
        self,
        error: Exception,
        order_id: str | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> OrderError:
        """Classify an order-related error using the structured error classification system.

        Args:
            error: The exception to classify
            order_id: Associated order ID if available
            additional_context: Additional context for classification

        Returns:
            Structured OrderError instance with category, code, and remediation info

        """
        from the_alchemiser.shared.value_objects.identifier import Identifier

        # Convert string order_id to Identifier if provided
        typed_order_id = None
        if order_id:
            try:
                typed_order_id = Identifier.from_string(order_id)
            except (ValueError, TypeError) as conv_error:
                # Log conversion failure for debugging
                logger.warning(
                    f"Failed to convert order_id to Identifier: {conv_error}",
                    extra={
                        "raw_order_id": order_id,
                        "error_type": type(conv_error).__name__,
                    },
                )
                # If conversion fails, keep as None and include in additional_context
                if additional_context is None:
                    additional_context = {}
                additional_context["raw_order_id"] = order_id

        # Use the domain error classifier
        error_classification = classify_exception(error)

        # Log the classified error for monitoring
        logger.info(
            f"Classified order error: {error_classification}",
            extra={
                "order_error_category": error_classification,
                "order_error_code": "UNKNOWN",
                "is_transient": False,
                "order_id": typed_order_id,
            },
        )

        # Create a simple OrderError object for return
        order_error = OrderError(str(error))
        order_error.order_id = typed_order_id
        return order_error

    def clear_errors(self) -> None:
        """Clear all recorded errors."""
        self.errors.clear()


# Global error handler instance
_error_handler = TradingSystemErrorHandler()


def get_error_handler() -> TradingSystemErrorHandler:
    """Get the global error handler instance."""
    return _error_handler


def handle_trading_error(
    error: Exception,
    context: str,
    component: str,
    additional_data: dict[str, Any] | None = None,
) -> ErrorDetails:
    """Handle errors in trading operations (convenience wrapper)."""
    return _error_handler.handle_error(error, context, component, additional_data)


def send_error_notification_if_needed(
    event_bus: EventBus,
) -> ErrorNotificationData | None:
    """Send error notification via event bus if there are errors that warrant it.

    Args:
        event_bus: Event bus for event-driven notifications.

    """
    if not _error_handler.should_send_error_email():
        return None

    return _send_error_notification_via_events(event_bus)


def _send_error_notification_via_events(
    event_bus: EventBus,
) -> ErrorNotificationData | None:
    """Send error notification via event bus (preferred method).

    Args:
        event_bus: Event bus instance for publishing events

    """
    from uuid import uuid4

    from the_alchemiser.shared.events.schemas import ErrorNotificationRequested

    # Generate error report
    error_report = _error_handler.generate_error_report()

    # Determine severity for subject
    if _error_handler.has_critical_errors():
        severity_display = "🚨 CRITICAL"
        severity: Literal["low", "medium", "high", "critical"] = "critical"
        priority = "URGENT"
    elif _error_handler.has_trading_errors():
        severity_display = "💰 TRADING"
        severity = "high"
        priority = "HIGH"
    else:
        severity_display = "⚠️ SYSTEM"
        severity = "medium"
        priority = "MEDIUM"

    # Find primary error code for subject (first non-None error code)
    primary_error_code = None
    for error_detail in _error_handler.errors:
        if error_detail.error_code:
            primary_error_code = error_detail.error_code
            break

    # Build error title for notification
    error_title = f"{severity_display} Alert - Trading System Errors"

    # Create and emit error notification event
    error_event = ErrorNotificationRequested(
        correlation_id=str(uuid4()),
        causation_id=f"error-handler-{datetime.now(UTC).isoformat()}",
        event_id=f"error-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="shared.errors.error_handler",
        source_component="TradingSystemErrorHandler",
        error_severity=severity,
        error_priority=priority,
        error_title=error_title,
        error_report=error_report,
        error_code=primary_error_code,
    )

    # Get event bus and emit event
    event_bus.publish(error_event)

    # Create notification data for return value
    notification_data = ErrorNotificationData(
        severity=severity,
        priority=priority,
        title=f"[{priority}] The Alchemiser - {severity} Error Report",
        error_report=error_report,
        html_content="(Generated by notification service)",
        success=True,  # Event was published successfully
        email_sent=True,
        correlation_id=error_event.correlation_id,
        event_id=error_event.event_id,
    )

    logger.info("Error notification event published successfully")
    return notification_data


def handle_errors_with_retry(
    operation: str,
    *,
    critical: bool = False,
    reraise: bool = True,
    max_retries: int = 0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Combine error handling with optional retry logic.

    Args:
        operation: Name of the operation for error context
        critical: Whether errors in this operation are critical
        reraise: Whether to reraise the exception after reporting
        max_retries: Number of retry attempts (0 = no retry)

    Returns:
        Decorated function with error handling and retry

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if max_retries > 0:
                # Apply retry logic
                retry_decorator = retry_with_backoff(
                    exceptions=(AlchemiserError, DataProviderError, TradingClientError),
                    max_retries=max_retries,
                )
                func_with_retry = retry_decorator(func)
            else:
                func_with_retry = func

            try:
                return func_with_retry(*args, **kwargs)
            except AlchemiserError as e:
                # Report known application errors
                get_global_error_reporter().report_error_with_context(
                    e,
                    context={"function": func.__name__, "args_count": len(args)},
                    is_critical=critical,
                    operation=operation,
                )
                if reraise:
                    raise
                return None
            except Exception as e:
                # Report unexpected errors as critical
                get_global_error_reporter().report_error_with_context(
                    e,
                    context={
                        "function": func.__name__,
                        "args_count": len(args),
                        "unexpected_error": True,
                    },
                    is_critical=True,
                    operation=operation,
                )
                if reraise:
                    raise
                return None

        return wrapper

    return decorator
