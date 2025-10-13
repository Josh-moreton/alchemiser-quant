"""Business Unit: shared | Status: current.

Unified error context data for event-driven error handling.

This module provides a consolidated ErrorContextData model that combines
best practices from all previous implementations with full support for
event tracing (correlation_id, causation_id) as required by the event-driven
architecture.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorContextData(BaseModel):
    """Unified error context for event-driven architecture.

    Consolidates three previous implementations into one canonical version
    with full support for event tracing and error tracking.

    Event Tracing (Required):
        - correlation_id: Traces request/workflow across services
        - causation_id: Links to triggering event in event chains

    Error Location:
        - operation: What operation was being performed
        - component: Which component/module encountered the error
        - function_name: Specific function that raised the error

    Request Context (Optional):
        - request_id: External request identifier
        - session_id: User session identifier

    Metadata:
        - additional_data: Flexible dict for extra context
        - timestamp: When the error occurred (ISO 8601)
        - schema_version: Schema version for compatibility tracking

    Note:
        The timestamp field is auto-generated using datetime.now(UTC). For
        deterministic testing, either provide an explicit timestamp or use
        freezegun to freeze time during tests.

    Examples:
        >>> context = ErrorContextData(
        ...     operation="execute_order",
        ...     component="execution_v2",
        ...     correlation_id="abc-123",
        ...     function_name="place_market_order"
        ... )
        >>> context.operation
        'execute_order'
        >>> context.timestamp  # Auto-generated
        '2025-10-07T12:34:56.789012+00:00'

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="forbid",
    )

    # Event tracing (REQUIRED for event-driven architecture)
    correlation_id: str | None = Field(
        default=None,
        description="Traces request/workflow across services and event handlers",
    )
    causation_id: str | None = Field(
        default=None, description="Links to the event that triggered this operation"
    )

    # Error location (optional for backward compatibility)
    operation: str | None = Field(
        default=None, description="Operation being performed when error occurred"
    )
    component: str | None = Field(
        default=None, description="Component/module where error originated"
    )
    function_name: str | None = Field(
        default=None, description="Specific function that raised the error"
    )

    # Legacy compatibility (from v2 implementation)
    module: str | None = Field(
        default=None, description="Module name (legacy, use component instead)"
    )
    function: str | None = Field(
        default=None, description="Function name (legacy, use function_name instead)"
    )

    # Request context (optional)
    request_id: str | None = Field(default=None, description="External request identifier")
    session_id: str | None = Field(default=None, description="User session identifier")

    # Flexible additional data
    additional_data: dict[str, Any] = Field(
        default_factory=dict, description="Additional context-specific data"
    )

    # Timestamp (auto-generated)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp when error context was created",
    )

    # Schema version for compatibility tracking
    schema_version: Literal["1.0"] = Field(
        default="1.0",
        description="Schema version for compatibility tracking",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary with all non-None fields

        """
        return self.model_dump(exclude_none=True, mode="python")
