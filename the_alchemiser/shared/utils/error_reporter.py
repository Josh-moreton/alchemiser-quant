#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Centralized Error Reporter for Production Monitoring.

This module provides structured error reporting for hands-off operation
according to the error handling improvement plan.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from the_alchemiser.shared.types.exceptions import (
    InsufficientFundsError,
    MarketClosedError,
    OrderExecutionError,
    SecurityError,
)

if TYPE_CHECKING:
    pass

# Type alias for notification manager and error context
NotificationManager = object | None
ErrorContext = dict[str, str | int | float | bool | None]

logger = logging.getLogger(__name__)


class ErrorReporter:
    """Centralized error reporting for production monitoring."""

    def __init__(self, notification_manager: NotificationManager = None) -> None:
        """Initialize error reporter.

        Args:
            notification_manager: Optional notification manager for alerts

        """
        self.notification_manager = notification_manager
        self.error_counts: dict[str, int] = defaultdict(int)
        self.critical_errors: list[ErrorContext] = []
        self.error_rate_threshold = 10  # Max errors per operation type before alerting

    def report_error(
        self,
        error: Exception,
        context: ErrorContext | None = None,
        *,
        is_critical: bool = False,
    ) -> None:
        """Report an error with context for monitoring."""
        error_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
            "context": context or {},
            "is_critical": is_critical,
        }

        # Add exception-specific context if available
        if hasattr(error, "to_dict"):
            error_data.update(error.to_dict())

        # Log structured error
        logger.error("Error reported", extra={"error_data": error_data})

        # Track error frequency
        error_key = f"{error.__class__.__name__}:{context.get('operation', 'unknown') if context else 'unknown'}"
        self.error_counts[error_key] += 1

        # Handle critical errors
        if is_critical or self._is_critical_error(error):
            self.critical_errors.append(error_data)
            self._handle_critical_error(error_data)

        # Check for error rate thresholds
        self._check_error_rates()

    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if an error is critical based on type."""
        return isinstance(
            error,
            InsufficientFundsError
            | SecurityError
            | OrderExecutionError
            | MarketClosedError,
        )

    def _handle_critical_error(self, error_data: ErrorContext) -> None:
        """Handle critical errors with immediate notification."""
        if self.notification_manager:
            self.notification_manager.send_critical_alert(
                f"Critical Error: {error_data['error_type']}", error_data
            )

    def _check_error_rates(self) -> None:
        """Check for high error rates and alert."""
        for error_key, count in self.error_counts.items():
            if count >= self.error_rate_threshold:
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

    def get_error_summary(self) -> dict[str, str | int | list[ErrorContext]]:
        """Get summary of recent errors for dashboard."""
        return {
            "error_counts": dict(self.error_counts),
            "critical_errors": len(self.critical_errors),
            "last_critical": self.critical_errors[-1] if self.critical_errors else None,
        }

    def clear_errors(self) -> None:
        """Clear error tracking (for testing/reset)."""
        self.error_counts.clear()
        self.critical_errors.clear()


# Singleton instance for global use
_global_error_reporter: ErrorReporter | None = None


def get_error_reporter(notification_manager: NotificationManager = None) -> ErrorReporter:
    """Get the global error reporter instance.

    Args:
        notification_manager: Optional notification manager for alerts

    Returns:
        Global ErrorReporter instance

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
    """Report errors globally."""
    reporter = get_error_reporter()
    reporter.report_error(error, context, is_critical=is_critical)
