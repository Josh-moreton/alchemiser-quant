#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Enhanced error reporting with rate monitoring and aggregation.

This module provides the EnhancedErrorReporter class for production-ready
error tracking, rate monitoring, and aggregation with:
- Sensitive data redaction for security
- Correlation ID tracking for observability
- Time-based cleanup to prevent memory leaks
- Alert deduplication to prevent spam
- Comprehensive structured logging

Usage:
    Basic usage::

        reporter = EnhancedErrorReporter()
        reporter.report_error_with_context(
            ValueError("Invalid input"),
            context={"correlation_id": "req-123", "module": "execution_v2"},
            operation="order_placement"
        )

    Using singleton::

        reporter = get_global_error_reporter()
        reporter.report_error_with_context(error, context, operation="trade")

Architecture:
    This is the production-ready version of error reporting.
    For basic features without rate monitoring, see shared.utils.error_reporter.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

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

# Constants for rate monitoring
ERROR_RATE_WINDOW_SECONDS = 300  # 5 minutes
ERROR_RATE_THRESHOLD_PER_MIN = 10  # Max errors per minute before alerting
ERROR_COUNTS_CLEANUP_WINDOW_SECONDS = 3600  # 1 hour - cleanup old error counts
ALERT_COOLDOWN_SECONDS = 300  # 5 minutes between repeated alerts


class EnhancedErrorReporter:
    """Enhanced error reporting with rate monitoring and aggregation.

    Production-ready error reporting with:
    - Automatic sensitive data redaction (passwords, tokens, API keys)
    - Correlation ID and causation ID tracking for distributed tracing
    - Time-based cleanup to prevent memory leaks
    - Alert deduplication to prevent notification spam
    - Rate monitoring with configurable thresholds

    This class is designed for AWS Lambda environments with long-running
    warm containers, preventing unbounded memory growth while maintaining
    recent error history for dashboards and alerting.

    Examples:
        Basic usage::

            reporter = EnhancedErrorReporter()
            reporter.report_error_with_context(
                ValueError("Invalid price"),
                context={
                    "correlation_id": "req-abc-123",
                    "causation_id": "evt-xyz-456",
                    "symbol": "AAPL",
                    "price": 150.50
                },
                operation="order_validation"
            )

        Critical error with sensitive data::

            reporter.report_error_with_context(
                SecurityError("Auth failed"),
                context={
                    "api_key": "secret-key-123",  # Will be redacted
                    "user_id": "user-789"
                },
                is_critical=True,
                operation="authentication"
            )

    Thread Safety:
        This class is NOT thread-safe. Use separate instances per thread
        or the global singleton with appropriate locking.

    """

    def __init__(self) -> None:
        """Initialize enhanced error reporter.

        Sets up tracking structures with time-based cleanup to prevent
        unbounded memory growth in long-running Lambda containers.
        """
        self.error_counts: dict[str, int] = defaultdict(int)
        self.error_counts_timestamps: dict[
            str, float
        ] = {}  # Track when each error type was last seen
        self.critical_errors: list[dict[str, Any]] = []
        self.error_rate_window = ERROR_RATE_WINDOW_SECONDS
        self.recent_errors: list[dict[str, Any]] = []
        self._alerted_errors: set[str] = set()  # Track which error rates we've alerted on
        self._alert_cooldown_until: dict[str, float] = {}  # Track cooldown periods

    def report_error_with_context(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        *,
        is_critical: bool = False,
        operation: str | None = None,
    ) -> None:
        """Report an error with enhanced context tracking.

        Automatically redacts sensitive data, extracts correlation IDs for
        distributed tracing, and maintains time-windowed error history.

        Args:
            error: The exception that occurred
            context: Additional context dict. Recommended fields:
                - correlation_id: Request/workflow correlation ID (for tracing)
                - causation_id: ID of the event that caused this error
                - module: Module where the error occurred
                - Additional domain-specific context
            is_critical: Whether to trigger immediate notification via error handler
            operation: Name of the operation that failed (e.g., "order_placement")

        Raises:
            ImportError: If error_handler module cannot be imported (critical errors only)

        Pre-conditions:
            - error must be an Exception instance

        Post-conditions:
            - Error tracked in recent_errors (time-windowed, 5 minutes)
            - Error counted in error_counts (time-windowed, 1 hour)
            - Sensitive data redacted from stored context
            - If critical, notification sent via error_handler
            - If rate exceeds threshold, warning logged (with cooldown)
            - correlation_id and causation_id extracted to top level if present

        Examples:
            Standard error reporting::

                reporter.report_error_with_context(
                    ValueError("Invalid quantity"),
                    context={
                        "correlation_id": "req-123",
                        "symbol": "AAPL",
                        "quantity": -5
                    },
                    operation="order_validation"
                )

            Critical error (triggers notification)::

                reporter.report_error_with_context(
                    SecurityError("Unauthorized access"),
                    context={"correlation_id": "req-456", "user_id": "user-789"},
                    is_critical=True,
                    operation="authentication"
                )

        Note:
            This method is NOT idempotent. The same error can be reported
            multiple times intentionally for rate monitoring. Deduplication
            should happen at the caller level if needed.

            Sensitive data in context is automatically redacted before storage
            and logging (password, token, api_key, secret, auth, credentials, account_id).

        """
        # Redact sensitive data first
        safe_context = self._redact_sensitive_data(context or {})

        # Extract correlation IDs for observability
        correlation_id = safe_context.get("correlation_id")
        causation_id = safe_context.get("causation_id")

        error_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
            "context": safe_context,
            "is_critical": is_critical,
            "operation": operation,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
        }

        # Use existing error handler for notifications
        if is_critical:
            # Import here to avoid circular imports
            from .error_handler import get_error_handler

            # Use the global error handler to process the error
            get_error_handler().handle_error(
                error=error,
                context=operation or "unknown",
                component="enhanced_reporter",
                additional_data=safe_context,
            )

            # Track critical errors
            self.critical_errors.append(error_data)

        # Track for rate monitoring
        error_key = f"{error.__class__.__name__}:{operation or 'unknown'}"
        self.error_counts[error_key] += 1
        self.error_counts_timestamps[error_key] = datetime.now(UTC).timestamp()

        # Add to recent errors
        self.recent_errors.append(error_data)
        self._cleanup_old_errors()
        self._cleanup_old_error_counts()

        # Check error rates
        self._check_error_rates()

    def _redact_sensitive_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from error context.

        Recursively redacts sensitive keys (password, token, api_key, etc.)
        from the context dictionary and any nested dictionaries.

        Args:
            context: The error context to redact

        Returns:
            New dictionary with sensitive keys replaced with "[REDACTED]"

        Examples:
            >>> reporter = EnhancedErrorReporter()
            >>> context = {"username": "john", "password": "secret123"}
            >>> safe = reporter._redact_sensitive_data(context)
            >>> safe
            {'username': 'john', 'password': '[REDACTED]'}

            Nested redaction::

                >>> context = {"request": {"headers": {"authorization": "Bearer token"}}}
                >>> safe = reporter._redact_sensitive_data(context)
                >>> safe['request']['headers']['authorization']
                '[REDACTED]'

        """
        redacted_context: dict[str, Any] = {}
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
        """Remove errors older than the monitoring window.

        Removes errors from recent_errors and critical_errors that are
        older than ERROR_RATE_WINDOW_SECONDS (5 minutes) to prevent
        unbounded memory growth.

        This method is called automatically after each error report.
        """
        current_time = datetime.now(UTC)
        cutoff_time = current_time.timestamp() - self.error_rate_window

        # Clean up recent errors
        self.recent_errors = [
            error
            for error in self.recent_errors
            if self._parse_timestamp(error.get("timestamp", "")).timestamp() > cutoff_time
        ]

        # Clean up critical errors (use longer window - 1 hour)
        critical_cutoff = current_time.timestamp() - ERROR_COUNTS_CLEANUP_WINDOW_SECONDS
        self.critical_errors = [
            error
            for error in self.critical_errors
            if self._parse_timestamp(error.get("timestamp", "")).timestamp() > critical_cutoff
        ]

    def _cleanup_old_error_counts(self) -> None:
        """Remove error counts older than the cleanup window.

        Prevents unbounded growth of error_counts dictionary by removing
        entries that haven't been updated in ERROR_COUNTS_CLEANUP_WINDOW_SECONDS
        (1 hour).

        This implements time-based decay for error statistics.
        """
        current_time = datetime.now(UTC).timestamp()
        cutoff_time = current_time - ERROR_COUNTS_CLEANUP_WINDOW_SECONDS

        # Find keys to remove
        keys_to_remove = [
            key
            for key, timestamp in self.error_counts_timestamps.items()
            if timestamp < cutoff_time
        ]

        # Remove old counts
        for key in keys_to_remove:
            del self.error_counts[key]
            del self.error_counts_timestamps[key]

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO format timestamp with error handling.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            Parsed datetime object, or current time if parsing fails

        """
        try:
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            # Return current time for malformed timestamps
            return datetime.now(UTC)

    def _check_error_rates(self) -> None:
        """Check for high error rates and alert with deduplication.

        Logs a warning if error rate exceeds ERROR_RATE_THRESHOLD_PER_MIN
        (10 errors/minute). Implements cooldown period to prevent alert spam.

        Alert deduplication:
            - Only alerts once per error rate level
            - Cooldown period of ALERT_COOLDOWN_SECONDS (5 minutes)
            - Includes correlation context in structured logging
        """
        error_rate = len(self.recent_errors) / (self.error_rate_window / 60)  # errors per minute

        if error_rate > ERROR_RATE_THRESHOLD_PER_MIN:
            alert_key = f"high_rate_{int(error_rate)}"
            current_time = datetime.now(UTC).timestamp()

            # Check if we've already alerted recently
            if (
                alert_key not in self._alerted_errors
                or current_time > self._alert_cooldown_until.get(alert_key, 0)
            ):
                # Extract correlation context from recent errors
                recent_correlation_ids = [
                    e.get("correlation_id")
                    for e in self.recent_errors[-5:]
                    if e.get("correlation_id")
                ]

                logger.warning(
                    "High error rate detected",
                    extra={
                        "error_rate_per_minute": error_rate,
                        "threshold": ERROR_RATE_THRESHOLD_PER_MIN,
                        "recent_errors_count": len(self.recent_errors),
                        "recent_correlation_ids": recent_correlation_ids[
                            :3
                        ],  # Sample of recent IDs
                    },
                )

                self._alerted_errors.add(alert_key)
                self._alert_cooldown_until[alert_key] = current_time + ALERT_COOLDOWN_SECONDS

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of recent errors for dashboard.

        Returns comprehensive error statistics including rate monitoring,
        most common errors, and critical error counts.

        Returns:
            Dictionary with error metrics:
                - total_error_types: Number of unique error types tracked
                - error_counts: Full mapping of error types to counts
                - recent_errors_count: Number of errors in recent window
                - error_rate_per_minute: Current error rate
                - most_common_errors: Top 5 most frequent error types
                - critical_errors_count: Number of critical errors tracked

        Examples:
            >>> reporter = EnhancedErrorReporter()
            >>> # ... report some errors ...
            >>> summary = reporter.get_error_summary()
            >>> print(f"Error rate: {summary['error_rate_per_minute']:.1f}/min")
            >>> print(f"Critical errors: {summary['critical_errors_count']}")

        """
        return {
            "total_error_types": len(self.error_counts),
            "error_counts": dict(self.error_counts),
            "recent_errors_count": len(self.recent_errors),
            "error_rate_per_minute": len(self.recent_errors) / (self.error_rate_window / 60),
            "most_common_errors": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "critical_errors_count": len(self.critical_errors),
        }


# Factory function for enhanced error reporter
def get_enhanced_error_reporter() -> EnhancedErrorReporter:
    """Create a new EnhancedErrorReporter instance.

    Returns:
        Fresh EnhancedErrorReporter instance with empty state

    Note:
        This creates a new instance each time. For shared state across
        multiple calls, use get_global_error_reporter() instead.

    Examples:
        Create independent reporter::

            reporter = get_enhanced_error_reporter()
            reporter.report_error_with_context(error, context, operation="test")

        Use in tests::

            def test_error_reporting():
                reporter = get_enhanced_error_reporter()
                reporter.report_error_with_context(ValueError("test"), operation="test")
                assert len(reporter.recent_errors) == 1

    """
    return EnhancedErrorReporter()


# Global enhanced error reporter instance (for backward compatibility)
# Consider using get_enhanced_error_reporter() in new code for better testability
_global_enhanced_error_reporter: EnhancedErrorReporter | None = None


def get_global_error_reporter() -> EnhancedErrorReporter:
    """Get the global error handler instance, creating it if needed.

    Implements singleton pattern for shared error tracking across
    the application lifecycle.

    Returns:
        Global EnhancedErrorReporter singleton instance

    Warning:
        The global instance persists state for the lifetime of the process
        (or Lambda container). In long-running containers, this accumulates
        error history. Time-based cleanup prevents unbounded growth, but
        be aware that statistics are cumulative.

        For isolated testing, use get_enhanced_error_reporter() instead.

    Examples:
        Use in production code::

            reporter = get_global_error_reporter()
            reporter.report_error_with_context(
                error,
                context={"correlation_id": "req-123"},
                operation="order_processing"
            )

        Access statistics::

            reporter = get_global_error_reporter()
            summary = reporter.get_error_summary()
            print(f"Total error types: {summary['total_error_types']}")

    Thread Safety:
        This function is NOT thread-safe. The singleton instance should only
        be accessed from a single thread, or external locking should be used.

    """
    global _global_enhanced_error_reporter
    if _global_enhanced_error_reporter is None:
        _global_enhanced_error_reporter = EnhancedErrorReporter()
    return _global_enhanced_error_reporter
