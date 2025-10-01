#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Enhanced error reporting with rate monitoring and aggregation.

This module provides the EnhancedErrorReporter class for production-ready
error tracking, rate monitoring, and aggregation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.logging.logging_utils import get_logger

logger = get_logger(__name__)


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
            # Import here to avoid circular imports
            from .error_handler import get_error_handler

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
            logger.warning(f"High error rate detected: {error_rate:.1f} errors/minute")

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
