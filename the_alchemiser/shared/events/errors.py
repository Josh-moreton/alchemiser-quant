#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event-specific exceptions for event-driven architecture.

Provides custom exception classes for event publishing, handling,
and routing failures in the EventBridge-based architecture.
"""

from __future__ import annotations


class EventPublishError(Exception):
    """Raised when publishing an event to EventBridge fails.

    This exception is raised when:
    - EventBridge API returns a FailedEntryCount > 0
    - AWS ClientError occurs during publish
    - Unexpected errors occur during event serialization/transmission

    Attributes:
        message: Human-readable error description
        event_id: ID of the event that failed to publish (optional)
        correlation_id: Correlation ID for tracing (optional)
        error_code: AWS error code if available (optional)

    Examples:
        >>> raise EventPublishError(
        ...     "InternalException: EventBridge service unavailable",
        ...     event_id="evt-123",
        ...     correlation_id="corr-456"
        ... )

    """

    def __init__(
        self,
        message: str,
        *,
        event_id: str | None = None,
        correlation_id: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize EventPublishError.

        Args:
            message: Human-readable error description
            event_id: ID of the event that failed to publish
            correlation_id: Correlation ID for tracing
            error_code: AWS error code if available

        """
        super().__init__(message)
        self.event_id = event_id
        self.correlation_id = correlation_id
        self.error_code = error_code

    def __str__(self) -> str:
        """Format error message with context."""
        parts = [super().__str__()]
        if self.event_id:
            parts.append(f"event_id={self.event_id}")
        if self.correlation_id:
            parts.append(f"correlation_id={self.correlation_id}")
        if self.error_code:
            parts.append(f"error_code={self.error_code}")
        return " | ".join(parts)
