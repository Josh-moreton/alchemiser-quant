#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Main error handler for The Alchemiser Trading System.

This module provides the single facade TradingSystemErrorHandler for all error handling,
categorization, and detailed error reporting via email notifications.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.logging import get_logger

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
    ErrorNotificationData,
)
from .error_utils import (
    retry_with_backoff,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.events.bus import EventBus

if TYPE_CHECKING:
    # Forward reference type aliases for type checking
    from .context import ErrorContextData

# Import additional error types
try:
    from the_alchemiser.shared.types.trading_errors import (
        OrderError,
        classify_exception,
    )
except ImportError:

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
    from the_alchemiser.shared.types.exceptions import (
        AlchemiserError,
        DataProviderError,
        TradingClientError,
    )
except ImportError:

    class AlchemiserError(Exception):  # type: ignore[no-redef]
        """Fallback AlchemiserError."""

    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback DataProviderError."""

    class TradingClientError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback TradingClientError."""


# Module-level logger
logger = get_logger(__name__)


class TradingSystemErrorHandler:
    """Enhanced error handler for autonomous trading operations."""

    def __init__(self) -> None:
        """Create a new error handler with empty history."""
        self.errors: list[ErrorDetails] = []
        self.logger = get_logger(__name__)

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
    ) -> ErrorDetails:
        """Handle an error with detailed logging and categorization."""
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
            additional_data=additional_data,
            suggested_action=suggested_action,
            error_code=error_code,
        )

        self.errors.append(error_details)

        # Log with appropriate level and include error_code
        log_extra = {"error_code": error_code} if error_code else {}

        if category == ErrorCategory.CRITICAL:
            self.logger.critical(
                f"CRITICAL ERROR in {component}: {error}",
                exc_info=True,
                extra={"extra_fields": log_extra},
            )
        elif category in [
            ErrorCategory.TRADING,
            ErrorCategory.DATA,
            ErrorCategory.STRATEGY,
        ]:
            self.logger.error(
                f"{category.upper()} ERROR in {component}: {error}",
                exc_info=True,
                extra={"extra_fields": log_extra},
            )
        elif category == ErrorCategory.CONFIGURATION:
            self.logger.error(
                f"CONFIGURATION ERROR in {component}: {error}",
                exc_info=True,
                extra={"extra_fields": log_extra},
            )
        else:
            self.logger.warning(
                f"{category.upper()} in {component}: {error}", extra={"extra_fields": log_extra}
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

    def _format_error_entry(self, error: dict[str, Any]) -> str:
        """Format a single error entry for the report."""
        entry = f"**Component:** {error['component']}\n"
        entry += f"**Context:** {error['context']}\n"
        entry += f"**Error:** {error['error_message']}\n"
        entry += f"**Action:** {error['suggested_action']}\n"
        if error["additional_data"]:
            entry += f"**Additional Data:** {error['additional_data']}\n"
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
            except (ValueError, TypeError):
                # If conversion fails, keep as None and include in additional_context
                if additional_context is None:
                    additional_context = {}
                additional_context["raw_order_id"] = order_id

        # Use the domain error classifier
        error_classification = classify_exception(error)

        # Log the classified error for monitoring
        self.logger.info(
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


def send_error_notification_if_needed(event_bus: EventBus) -> ErrorNotificationData | None:
    """Send error notification via event bus if there are errors that warrant it.

    Args:
        event_bus: Event bus for event-driven notifications.

    """
    if not _error_handler.should_send_error_email():
        return None

    return _send_error_notification_via_events(event_bus)


def _send_error_notification_via_events(event_bus: EventBus) -> ErrorNotificationData | None:
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
        severity = "🚨 CRITICAL"
        priority = "URGENT"
    elif _error_handler.has_trading_errors():
        severity = "💰 TRADING"
        priority = "HIGH"
    else:
        severity = "⚠️ SYSTEM"
        priority = "MEDIUM"

    # Find primary error code for subject (first non-None error code)
    primary_error_code = None
    for error_detail in _error_handler.errors:
        if error_detail.error_code:
            primary_error_code = error_detail.error_code
            break

    # Build error title for notification
    error_title = f"{severity} Alert - Trading System Errors"

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
    notification_data: ErrorNotificationData = {
        "severity": severity,
        "priority": priority,
        "title": f"[{priority}] The Alchemiser - {severity} Error Report",
        "error_report": error_report,
        "html_content": "(Generated by notification service)",
        "success": True,  # Event was published successfully
        "email_sent": True,
        "correlation_id": error_event.correlation_id,
        "event_id": error_event.event_id,
    }

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
