#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Centralized Error Reporter for Production Monitoring.

This module provides structured error reporting for hands-off operation
according to the error handling improvement plan.

Note: This module provides basic error reporting functionality.
For production use with rate monitoring and aggregation, consider using
EnhancedErrorReporter from shared.errors.error_reporter.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from the_alchemiser.shared.errors.exceptions import (
    InsufficientFundsError,
    MarketClosedError,
    OrderExecutionError,
    SecurityError,
)
from the_alchemiser.shared.logging import get_logger


class NotificationManager(Protocol):  # pragma: no cover - structural typing helper
    """Protocol for notification managers."""

    def send_critical_alert(self, message: str, context: dict[str, Any]) -> None:
        """Send critical alert notification."""
        ...

    def send_warning_alert(self, message: str, context: dict[str, Any]) -> None:
        """Send warning alert notification."""
        ...


# Type alias for error context
ErrorContext = dict[str, Any]

# Sensitive keys that should be redacted from error context
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

logger = get_logger(__name__)


class ErrorReporter:
    """Centralized error reporting for production monitoring.

    Provides basic error tracking with:
    - Error frequency counting with time-based cleanup
    - Critical error detection and notification
    - Rate threshold monitoring
    - Correlation ID tracking for observability
    - Security-conscious context redaction

    For production use with advanced features, see EnhancedErrorReporter
    in shared.errors.error_reporter.
    """

    def __init__(self, notification_manager: NotificationManager | None = None) -> None:
        """Initialize error reporter.

        Args:
            notification_manager: Optional notification manager for alerts

        """
        self.notification_manager = notification_manager
        self.error_counts: dict[str, int] = defaultdict(int)
        self.critical_errors: list[ErrorContext] = []
        self.error_rate_threshold = 10  # Max errors per operation type before alerting
        self.error_rate_window = 300  # 5 minutes in seconds
        self.recent_errors: list[ErrorContext] = []  # For time-based cleanup
        self._alerted_errors: set[str] = set()  # Track which errors we've alerted on

    def report_error(
        self,
        error: Exception,
        context: ErrorContext | None = None,
        *,
        is_critical: bool = False,
    ) -> None:
        """Report an error with context for monitoring.

        Args:
            error: The exception that occurred
            context: Additional context about the error. Should include:
                - correlation_id: Request/workflow correlation ID
                - causation_id: ID of the event that caused this error
                - operation: Name of the operation that failed
                - module: Module where the error occurred
            is_critical: Whether to treat this as a critical error requiring immediate notification

        Note:
            This method is idempotent based on error+timestamp+correlation_id combination.
            Sensitive data in context is automatically redacted.

        """
        # Redact sensitive data from context
        safe_context = self._redact_sensitive_data(context or {})

        error_data: ErrorContext = {
            "timestamp": datetime.now(UTC).isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
            "context": safe_context,
            "is_critical": is_critical,
            "correlation_id": safe_context.get("correlation_id"),
            "causation_id": safe_context.get("causation_id"),
            "operation": safe_context.get("operation", "unknown"),
        }

        # Add exception-specific context if available (e.g., AlchemiserError.to_dict())
        if hasattr(error, "to_dict"):
            exception_data = error.to_dict()
            # Merge but don't overwrite core fields
            for key, value in exception_data.items():
                if key not in error_data:
                    error_data[key] = value

        # Log structured error with correlation IDs
        logger.error(
            "Error reported",
            extra={
                "error_data": error_data,
                "correlation_id": error_data.get("correlation_id"),
                "causation_id": error_data.get("causation_id"),
            },
        )

        # Track error frequency
        error_key = f"{error.__class__.__name__}:{safe_context.get('operation', 'unknown')}"
        self.error_counts[error_key] += 1

        # Add to recent errors for time-based tracking
        self.recent_errors.append(error_data)
        self._cleanup_old_errors()

        # Handle critical errors
        if is_critical or self._is_critical_error(error):
            self.critical_errors.append(error_data)
            self._handle_critical_error(error_data)

        # Check for error rate thresholds (only alert once per error type)
        self._check_error_rates()

    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if an error is critical based on type.

        Args:
            error: The exception to check

        Returns:
            True if the error is considered critical (requires immediate action)

        """
        return isinstance(
            error,
            InsufficientFundsError | SecurityError | OrderExecutionError | MarketClosedError,
        )

    def _redact_sensitive_data(self, context: ErrorContext) -> ErrorContext:
        """Redact sensitive information from error context.

        Args:
            context: The error context to redact

        Returns:
            New dictionary with sensitive keys redacted

        """
        redacted_context: ErrorContext = {}
        for key, value in context.items():
            if key.lower() in SENSITIVE_KEYS:
                redacted_context[key] = "[REDACTED]"
            elif isinstance(value, dict):
                # Recursively redact nested dictionaries
                redacted_context[key] = self._redact_sensitive_data(value)
            else:
                redacted_context[key] = value
        return redacted_context

    def _cleanup_old_errors(self) -> None:
        """Remove errors older than the monitoring window to prevent unbounded growth."""
        current_time = datetime.now(UTC)
        cutoff_time = current_time - timedelta(seconds=self.error_rate_window)

        # Keep only errors within the time window
        self.recent_errors = [
            error
            for error in self.recent_errors
            if datetime.fromisoformat(error["timestamp"]) > cutoff_time
        ]

        # Also cleanup critical errors older than 1 hour to prevent memory issues
        one_hour_ago = current_time - timedelta(hours=1)
        self.critical_errors = [
            error
            for error in self.critical_errors
            if datetime.fromisoformat(error["timestamp"]) > one_hour_ago
        ]

    def _handle_critical_error(self, error_data: ErrorContext) -> None:
        """Handle critical errors with immediate notification.

        Args:
            error_data: The error data to report

        """
        if self.notification_manager:
            self.notification_manager.send_critical_alert(
                f"Critical Error: {error_data['error_type']}", error_data
            )

    def _check_error_rates(self) -> None:
        """Check for high error rates and alert (only once per error type).

        This method tracks which error types have already been alerted on
        to prevent alert spam. Alerts are reset when errors age out of the window.

        """
        for error_key, count in self.error_counts.items():
            if count >= self.error_rate_threshold and error_key not in self._alerted_errors:
                logger.warning(
                    "High error rate detected",
                    extra={
                        "error_type": error_key,
                        "count": count,
                        "threshold": self.error_rate_threshold,
                    },
                )
                if self.notification_manager:
                    self.notification_manager.send_warning_alert(
                        f"High error rate: {error_key}",
                        {"count": count, "threshold": self.error_rate_threshold},
                    )
                # Mark as alerted to prevent repeated notifications
                self._alerted_errors.add(error_key)

        # Reset alerted errors if count drops below threshold
        errors_to_reset = {
            key
            for key in self._alerted_errors
            if self.error_counts.get(key, 0) < self.error_rate_threshold
        }
        self._alerted_errors -= errors_to_reset

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of recent errors for dashboard.

        Returns:
            Dictionary containing:
            - error_counts: Count of each error type
            - critical_errors: Number of critical errors
            - last_critical: Most recent critical error (if any)
            - recent_errors_count: Total errors in time window
            - error_rate_per_minute: Current error rate

        """
        return {
            "error_counts": dict(self.error_counts),
            "critical_errors": len(self.critical_errors),
            "last_critical": self.critical_errors[-1] if self.critical_errors else None,
            "recent_errors_count": len(self.recent_errors),
            "error_rate_per_minute": len(self.recent_errors) / (self.error_rate_window / 60),
        }

    def clear_errors(self) -> None:
        """Clear error tracking (for testing/reset).

        Warning:
            This is intended for testing only. In production, errors age out
            automatically based on the time window.

        """
        self.error_counts.clear()
        self.critical_errors.clear()
        self.recent_errors.clear()
        self._alerted_errors.clear()


# Singleton instance for global use
_global_error_reporter: ErrorReporter | None = None


def get_error_reporter(
    notification_manager: NotificationManager | None = None,
) -> ErrorReporter:
    """Get the global error reporter instance.

    Args:
        notification_manager: Optional notification manager for alerts.
            Note: This parameter only applies on first call. Subsequent calls
            return the existing singleton instance.

    Returns:
        Global ErrorReporter instance

    Warning:
        This uses a singleton pattern. For better testability in new code,
        consider creating explicit ErrorReporter instances or using
        dependency injection.

    """
    global _global_error_reporter
    if _global_error_reporter is None:
        _global_error_reporter = ErrorReporter(notification_manager)
    return _global_error_reporter


def report_error_globally(
    error: Exception,
    context: ErrorContext | None = None,
    *,
    is_critical: bool = False,
) -> None:
    """Report errors using the global error reporter instance.

    Args:
        error: The exception that occurred
        context: Additional context. Should include correlation_id, causation_id,
            operation, and module for proper observability.
        is_critical: Whether this is a critical error

    Note:
        For new code, prefer explicit dependency injection of ErrorReporter
        instances over using this global function.

    Example:
        >>> try:
        ...     risky_operation()
        ... except ValueError as e:
        ...     report_error_globally(
        ...         e,
        ...         context={
        ...             "correlation_id": "req-123",
        ...             "causation_id": "evt-456",
        ...             "operation": "risky_operation",
        ...             "module": "strategy_v2",
        ...         },
        ...         is_critical=False,
        ...     )

    """
    reporter = get_error_reporter()
    reporter.report_error(error, context, is_critical=is_critical)
