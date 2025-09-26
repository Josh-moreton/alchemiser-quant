#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Main error handler for The Alchemiser Trading System.

This module provides the single facade TradingSystemErrorHandler for all error handling,
categorization, and detailed error reporting via email notifications.
"""

from __future__ import annotations

import logging
import time
import traceback
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    # Forward reference type aliases for type checking
    from .context import ErrorContextData

# Type aliases for error handler data structures
ErrorData = dict[str, str | int | float | bool | None]
ErrorList = list[ErrorData]
ContextDict = dict[str, str | int | float | bool | None]


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


# Import exceptions
try:
    from the_alchemiser.shared.types.exceptions import (
        AlchemiserError,
        ConfigurationError,
        DataProviderError,
        InsufficientFundsError,
        MarketDataError,
        NotificationError,
        OrderExecutionError,
        PositionValidationError,
        TradingClientError,
    )
except ImportError:
    # Minimal fallback stubs (to avoid circular imports)
    class AlchemiserError(Exception):  # type: ignore[no-redef]
        """Fallback AlchemiserError."""

    class ConfigurationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback ConfigurationError."""

    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback DataProviderError."""

    class InsufficientFundsError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback InsufficientFundsError."""

    class MarketDataError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback MarketDataError."""

    class NotificationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback NotificationError."""

    class OrderExecutionError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback OrderExecutionError."""

    class PositionValidationError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback PositionValidationError."""

    class TradingClientError(AlchemiserError):  # type: ignore[no-redef]
        """Fallback TradingClientError."""


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

    def classify_exception(exception: Exception) -> str:
        """Fallback classify_exception."""
        return exception.__class__.__name__


def _is_strategy_execution_error(err: Exception) -> bool:
    """Detect strategy execution errors without cross-module imports.

    We avoid importing from `strategy_v2` inside `shared` to respect
    module boundaries. Instead, we detect by class name to categorize.
    """
    return err.__class__.__name__ == "StrategyExecutionError"


try:
    from .context import ErrorContextData
except ImportError:

    class ErrorContextData:  # type: ignore[no-redef]
        """Fallback ErrorContextData class."""

        def __init__(
            self,
            module: str | None = None,
            function: str | None = None,
            operation: str | None = None,
            correlation_id: str | None = None,
            additional_data: dict[str, Any] | None = None,
        ) -> None:
            """Initialize ErrorContextData."""
            self.module = module
            self.function = function
            self.operation = operation
            self.correlation_id = correlation_id
            self.additional_data = additional_data

        def to_dict(self) -> dict[str, Any]:
            """Convert to dictionary."""
            return {
                "module": self.module,
                "function": self.function,
                "operation": self.operation,
                "correlation_id": self.correlation_id,
                "additional_data": self.additional_data or {},
            }


# Define FlexibleContext after ErrorContextData is available
FlexibleContext = ErrorContextData | ErrorData | None


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


class ErrorDetails:
    """Detailed error information for reporting."""

    def __init__(
        self,
        error: Exception,
        category: str,
        context: str,
        component: str,
        additional_data: dict[str, Any] | None = None,
        suggested_action: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Store detailed error information."""
        self.error = error
        self.category = category
        self.context = context
        self.component = component
        self.additional_data = additional_data or {}
        self.suggested_action = suggested_action
        self.error_code = error_code
        self.timestamp = datetime.now(UTC)
        self.traceback = traceback.format_exc()

    def to_dict(self) -> dict[str, Any]:
        """Convert error details to dictionary for serialization."""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "category": self.category,
            "context": self.context,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback,
            "additional_data": self.additional_data,
            "suggested_action": self.suggested_action,
            "error_code": self.error_code,
        }


class EnhancedAlchemiserError(AlchemiserError):
    """Enhanced base exception with production monitoring support."""

    def __init__(
        self,
        message: str,
        context: FlexibleContext = None,
        severity: str = ErrorSeverity.MEDIUM,
        *,
        recoverable: bool = True,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> None:
        """Initialize enhanced base error with context and retry metadata."""
        super().__init__(message)
        if context is not None:
            if isinstance(context, ErrorContextData):
                self.context = context.to_dict()
            elif isinstance(context, dict):
                self.context = context
            else:
                # For any other object that might have a to_dict method (backward compatibility)
                self.context = context.to_dict() if hasattr(context, "to_dict") else {}
        else:
            self.context = {}
        self.severity = severity
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.error_id = str(uuid.uuid4())
        self.original_message = message

        # Set error_id in context for logging
        try:
            from the_alchemiser.shared.logging.logging_utils import set_error_id

            set_error_id(self.error_id)
        except ImportError:
            # Avoid circular import issues during module initialization
            pass

    def should_retry(self) -> bool:
        """Determine if error should be retried."""
        return self.recoverable and self.retry_count < self.max_retries

    def get_retry_delay(self) -> float:
        """Get exponential backoff delay for retries."""
        return min(2.0**self.retry_count, 60.0)  # Max 60 seconds

    def increment_retry(self) -> EnhancedAlchemiserError:
        """Create a new instance with incremented retry count."""
        return self.__class__(
            message=self.original_message,
            context=self.context,
            severity=self.severity,
            recoverable=self.recoverable,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured data for logging/reporting."""
        base_dict = super().to_dict()

        # Handle context conversion - it's always a dict now
        context_dict = self.context if self.context else None

        base_dict.update(
            {
                "error_id": self.error_id,
                "severity": self.severity,
                "recoverable": self.recoverable,
                "retry_count": self.retry_count,
                "max_retries": self.max_retries,
                "context": context_dict,
            }
        )
        return base_dict


class TradingSystemErrorHandler:
    """Enhanced error handler for autonomous trading operations."""

    def __init__(self) -> None:
        """Create a new error handler with empty history."""
        self.errors: list[ErrorDetails] = []
        self.logger = logging.getLogger(__name__)

    def _categorize_by_exception_type(self, error: Exception) -> str | None:
        """Categorize error based purely on exception type."""
        if isinstance(
            error,
            InsufficientFundsError | OrderExecutionError | PositionValidationError,
        ):
            return ErrorCategory.TRADING
        if isinstance(error, MarketDataError | DataProviderError):
            return ErrorCategory.DATA
        if _is_strategy_execution_error(error):
            return ErrorCategory.STRATEGY
        if isinstance(error, ConfigurationError):
            return ErrorCategory.CONFIGURATION
        if isinstance(error, NotificationError):
            return ErrorCategory.NOTIFICATION
        if isinstance(error, AlchemiserError):
            return ErrorCategory.CRITICAL
        return None

    def _categorize_by_context(self, context: str) -> str:
        """Categorize error based on context keywords."""
        context_lower = context.lower()
        if "trading" in context_lower or "order" in context_lower:
            return ErrorCategory.TRADING
        if "data" in context_lower or "price" in context_lower:
            return ErrorCategory.DATA
        if "strategy" in context_lower or "signal" in context_lower:
            return ErrorCategory.STRATEGY
        if "config" in context_lower or "auth" in context_lower:
            return ErrorCategory.CONFIGURATION
        return ErrorCategory.CRITICAL

    def categorize_error(self, error: Exception, context: str = "") -> str:
        """Categorize error based on type and context."""
        # First try categorization by exception type
        category = self._categorize_by_exception_type(error)
        if category:
            return category

        # Handle TradingClientError with context dependency
        if isinstance(error, TradingClientError):
            context_lower = context.lower()
            if "order" in context_lower or "position" in context_lower:
                return ErrorCategory.TRADING
            return ErrorCategory.DATA

        # For non-Alchemiser exceptions, categorize by context
        return self._categorize_by_context(context)

    def get_suggested_action(self, error: Exception, category: str) -> str:
        """Get suggested action based on error type and category."""
        if isinstance(error, InsufficientFundsError):
            return "Check account balance and reduce position sizes or add funds"
        if isinstance(error, OrderExecutionError):
            return "Verify market hours, check symbol validity, and ensure order parameters are correct"
        if isinstance(error, PositionValidationError):
            return "Check current positions and ensure selling quantities don't exceed holdings"
        if isinstance(error, MarketDataError):
            return "Check API connectivity and data provider status"
        if isinstance(error, ConfigurationError):
            return "Verify configuration settings and API credentials"
        if _is_strategy_execution_error(error):
            return "Review strategy logic and input data for calculation errors"
        if category == ErrorCategory.DATA:
            return "Check market data sources, API limits, and network connectivity"
        if category == ErrorCategory.TRADING:
            return "Verify trading permissions, account status, and market hours"
        if category == ErrorCategory.CRITICAL:
            return "Review system logs, check AWS permissions, and verify deployment configuration"
        return "Review logs for detailed error information and contact support if needed"

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

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all errors by category."""
        # Initialize summary with all categories as None
        summary: dict[str, Any] = {
            "critical": None,
            "trading": None,
            "data": None,
            "strategy": None,
            "configuration": None,
            "notification": None,
            "warning": None,
        }

        # Handle each category explicitly
        critical_errors = [e for e in self.errors if e.category == ErrorCategory.CRITICAL]
        if critical_errors:
            summary["critical"] = {
                "count": len(critical_errors),
                "errors": [e.to_dict() for e in critical_errors],
            }

        trading_errors = [e for e in self.errors if e.category == ErrorCategory.TRADING]
        if trading_errors:
            summary["trading"] = {
                "count": len(trading_errors),
                "errors": [e.to_dict() for e in trading_errors],
            }

        data_errors = [e for e in self.errors if e.category == ErrorCategory.DATA]
        if data_errors:
            summary["data"] = {
                "count": len(data_errors),
                "errors": [e.to_dict() for e in data_errors],
            }

        strategy_errors = [e for e in self.errors if e.category == ErrorCategory.STRATEGY]
        if strategy_errors:
            summary["strategy"] = {
                "count": len(strategy_errors),
                "errors": [e.to_dict() for e in strategy_errors],
            }

        config_errors = [e for e in self.errors if e.category == ErrorCategory.CONFIGURATION]
        if config_errors:
            summary["configuration"] = {
                "count": len(config_errors),
                "errors": [e.to_dict() for e in config_errors],
            }

        notification_errors = [e for e in self.errors if e.category == ErrorCategory.NOTIFICATION]
        if notification_errors:
            summary["notification"] = {
                "count": len(notification_errors),
                "errors": [e.to_dict() for e in notification_errors],
            }

        warning_errors = [e for e in self.errors if e.category == ErrorCategory.WARNING]
        if warning_errors:
            summary["warning"] = {
                "count": len(warning_errors),
                "errors": [e.to_dict() for e in warning_errors],
            }

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


# Enhanced Trading-Specific Exceptions


class EnhancedTradingError(EnhancedAlchemiserError):
    """Enhanced trading error with position and order context."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize trading error with optional symbol/order/quantity/price."""
        super().__init__(message, **kwargs)
        self.symbol = symbol
        self.order_id = order_id
        self.quantity = quantity
        self.price = price

    def to_dict(self) -> dict[str, Any]:
        """Include trading-specific context in serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "symbol": self.symbol,
                "order_id": self.order_id,
                "quantity": self.quantity,
                "price": self.price,
            }
        )
        return base_dict


class EnhancedDataError(EnhancedAlchemiserError):
    """Enhanced data error with data source context."""

    def __init__(
        self,
        message: str,
        data_source: str | None = None,
        data_type: str | None = None,
        symbol: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize data error with optional source/type/symbol context."""
        super().__init__(message, **kwargs)
        self.data_source = data_source
        self.data_type = data_type
        self.symbol = symbol

    def to_dict(self) -> dict[str, Any]:
        """Include data-specific context in serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "data_source": self.data_source,
                "data_type": self.data_type,
                "symbol": self.symbol,
            }
        )
        return base_dict


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


def send_error_notification_if_needed() -> ErrorNotificationData | None:
    """Send error notification email if there are errors that warrant it."""
    if not _error_handler.should_send_error_email():
        return None

    try:
        from the_alchemiser.shared.notifications.client import send_email_notification
        from the_alchemiser.shared.notifications.templates import EmailTemplates

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

        # Build subject with error code if available
        if primary_error_code:
            subject = f"[FAILURE][{priority}][{primary_error_code}] The Alchemiser - {severity} Error Report"
        else:
            subject = f"[FAILURE][{priority}] The Alchemiser - {severity} Error Report"

        # Build HTML email
        html_content = EmailTemplates.build_error_report(
            title=f"{severity} Alert - Trading System Errors",
            error_message=error_report,
        )

        # Send notification
        success = send_email_notification(
            subject=subject,
            html_content=html_content,
            text_content=error_report,
        )

        # Create notification data
        notification_data: ErrorNotificationData = {
            "severity": severity,
            "priority": priority,
            "title": f"[{priority}] The Alchemiser - {severity} Error Report",
            "error_report": error_report,
            "html_content": html_content,
        }

        if success:
            logging.info("Error notification email sent successfully")
            return notification_data
        logging.error("Failed to send error notification email")
        return notification_data

    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")
        return None


# Enhanced Error Handling Utilities for Production Resilience


def _calculate_jitter_factor(attempt: int) -> float:
    """Calculate jitter factor for retry delay."""
    return 0.5 + (hash(str(attempt) + str(int(time.time() * 1000))) % 500) / 1000


def _calculate_retry_delay(
    attempt: int, base_delay: float, backoff_factor: float, max_delay: float, *, jitter: bool
) -> float:
    """Calculate retry delay with exponential backoff and optional jitter."""
    delay = min(base_delay * (backoff_factor**attempt), max_delay)
    if jitter:
        delay *= _calculate_jitter_factor(attempt)
    return delay


def _handle_final_retry_attempt(exception: Exception, max_retries: int, func_name: str) -> None:
    """Handle the final retry attempt by adding context and logging."""
    if hasattr(exception, "retry_count"):
        exception.retry_count = max_retries
    logging.error(f"Function {func_name} failed after {max_retries} retries: {exception}")


def retry_with_backoff(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    *,
    jitter: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Retry decorator with exponential backoff and jitter.

    Args:
        exceptions: Tuple of exception types to catch and retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds before first retry
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Whether to add random jitter to delays

    Returns:
        Decorated function with retry logic

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        _handle_final_retry_attempt(e, max_retries, func.__name__)
                        raise

                    delay = _calculate_retry_delay(attempt, base_delay, backoff_factor, max_delay, jitter=jitter)
                    
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


class CircuitBreakerOpenError(AlchemiserError):
    """Raised when circuit breaker is open."""


class CircuitBreaker:
    """Circuit breaker pattern for external service calls.

    Prevents cascading failures by temporarily stopping calls to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds before trying to close circuit
            expected_exception: Exception type that counts as failure

        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply circuit breaker pattern to a function.

        Returns a wrapper that tracks failures and prevents calls when threshold is exceeded.
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if self.state == "OPEN":
                if self.last_failure_time and time.time() - self.last_failure_time < self.timeout:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN for {func.__name__}. "
                        f"Retry after {self.timeout}s timeout."
                    )
                self.state = "HALF_OPEN"
                logging.info(f"Circuit breaker moving to HALF_OPEN for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logging.info(f"Circuit breaker CLOSED for {func.__name__}")
                return result
            except self.expected_exception:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logging.warning(
                        f"Circuit breaker OPENED for {func.__name__} after "
                        f"{self.failure_count} failures"
                    )

                raise

        return wrapper


def categorize_error_severity(error: Exception) -> str:
    """Categorize error severity for monitoring."""
    if isinstance(error, InsufficientFundsError | (OrderExecutionError | PositionValidationError)):
        return ErrorSeverity.HIGH
    if isinstance(error, MarketDataError | DataProviderError) or _is_strategy_execution_error(
        error
    ):
        return ErrorSeverity.MEDIUM
    if isinstance(error, ConfigurationError):
        return ErrorSeverity.HIGH
    if isinstance(error, NotificationError):
        return ErrorSeverity.LOW
    if isinstance(error, AlchemiserError):
        return ErrorSeverity.CRITICAL
    return ErrorSeverity.MEDIUM


def create_enhanced_error(
    error_type: type[EnhancedAlchemiserError],
    message: str,
    context: ErrorContextData | None = None,
    severity: str | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> EnhancedAlchemiserError:
    """Create enhanced errors with proper context."""
    if severity is None:
        # Auto-determine severity based on error type
        temp_error = error_type(message)
        severity = categorize_error_severity(temp_error)

    return error_type(
        message=message,
        context=context,
        severity=severity,
        **kwargs,
    )


class EnhancedErrorReporter:
    """Enhanced error reporting with rate monitoring and aggregation.

    Extends the existing error handler with production-ready features.
    """

    def __init__(self) -> None:
        """Initialize enhanced error reporter."""
        self.error_counts: dict[str, int] = defaultdict(int)
        self.critical_errors: list[dict[str, Any]] = []
        self.error_rate_window = 300  # 5 minutes
        self.recent_errors: list[dict[str, Any]] = []

    def report_error_with_context(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        *,
        is_critical: bool = False,
        operation: str | None = None,
    ) -> None:
        """Report an error with enhanced context tracking.

        Args:
            error: The exception that occurred
            context: Additional context about the error
            is_critical: Whether this is a critical error
            operation: Name of the operation that failed

        """
        error_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
            "context": context or {},
            "is_critical": is_critical,
            "operation": operation,
        }

        # Use existing error handler for notifications
        if is_critical:
            # Use the global error handler to process the error
            get_error_handler().handle_error(
                error=error,
                context=operation or "unknown",
                component="enhanced_reporter",
                additional_data=context,
            )

        # Track for rate monitoring
        error_key = f"{error.__class__.__name__}:{operation or 'unknown'}"
        self.error_counts[error_key] += 1

        # Add to recent errors
        self.recent_errors.append(error_data)
        self._cleanup_old_errors()

        # Check error rates
        self._check_error_rates()

    def _cleanup_old_errors(self) -> None:
        """Remove errors older than the monitoring window."""
        current_time = datetime.now(UTC)
        cutoff_time = current_time.timestamp() - self.error_rate_window

        self.recent_errors = [
            error
            for error in self.recent_errors
            if datetime.fromisoformat(error["timestamp"]).timestamp() > cutoff_time
        ]

    def _check_error_rates(self) -> None:
        """Check for high error rates and alert."""
        error_rate = len(self.recent_errors) / (self.error_rate_window / 60)  # errors per minute

        if error_rate > 10:  # More than 10 errors per minute
            logging.warning(f"High error rate detected: {error_rate:.1f} errors/minute")

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of recent errors for dashboard."""
        return {
            "total_error_types": len(self.error_counts),
            "error_counts": dict(self.error_counts),
            "recent_errors_count": len(self.recent_errors),
            "error_rate_per_minute": len(self.recent_errors) / (self.error_rate_window / 60),
            "most_common_errors": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }


# Factory function for enhanced error reporter
def get_enhanced_error_reporter() -> EnhancedErrorReporter:
    """Create a new EnhancedErrorReporter instance."""
    return EnhancedErrorReporter()


# Global enhanced error reporter instance (for backward compatibility)
# Consider using get_enhanced_error_reporter() in new code for better testability
_global_enhanced_error_reporter: EnhancedErrorReporter | None = None


def get_global_error_reporter() -> EnhancedErrorReporter:
    """Get the global error handler instance, creating it if needed."""
    global _global_enhanced_error_reporter
    if _global_enhanced_error_reporter is None:
        _global_enhanced_error_reporter = EnhancedErrorReporter()
    return _global_enhanced_error_reporter


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
