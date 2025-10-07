#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trace data transfer objects for DSL engine execution tracking.

Provides typed DTOs for tracking strategy evaluation traces with structured
logging and observability support.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class TraceEntry(BaseModel):
    """Single trace entry in strategy evaluation."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    step_id: str = Field(..., min_length=1, description="Unique step identifier")
    step_type: str = Field(..., min_length=1, description="Type of evaluation step")
    timestamp: datetime = Field(..., description="When this step occurred")
    description: str = Field(..., min_length=1, description="Human-readable step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Step inputs")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Step outputs")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional step metadata")

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)


class Trace(BaseModel):
    """DTO for complete strategy evaluation trace.

    Contains structured trace log for audit and observability purposes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Trace identification
    trace_id: str = Field(..., min_length=1, description="Unique trace identifier")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracking")
    strategy_id: str = Field(..., min_length=1, description="Strategy that was evaluated")

    # Timing
    started_at: datetime = Field(..., description="When evaluation started")
    completed_at: datetime | None = Field(default=None, description="When evaluation completed")

    # Trace entries
    entries: list[TraceEntry] = Field(default_factory=list, description="Ordered trace entries")

    # Results
    final_allocation: dict[str, Decimal] = Field(
        default_factory=dict, description="Final portfolio allocation"
    )
    success: bool = Field(default=True, description="Whether evaluation succeeded")
    error_message: str | None = Field(default=None, description="Error message if failed")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional trace metadata")

    @field_validator("started_at")
    @classmethod
    def ensure_timezone_aware_started_at(cls, v: datetime) -> datetime:
        """Ensure started_at is timezone-aware."""
        return ensure_timezone_aware(v)

    @field_validator("completed_at")
    @classmethod
    def ensure_timezone_aware_completed_at(cls, v: datetime | None) -> datetime | None:
        """Ensure completed_at is timezone-aware."""
        if v is None:
            return None
        return ensure_timezone_aware(v)

    def add_entry(
        self,
        step_id: str,
        step_type: str,
        description: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Trace:
        """Add a trace entry and return new immutable trace.

        Args:
            step_id: Unique step identifier
            step_type: Type of evaluation step
            description: Human-readable description
            inputs: Step inputs
            outputs: Step outputs
            metadata: Additional metadata

        Returns:
            New Trace with added entry

        """
        entry = TraceEntry(
            step_id=step_id,
            step_type=step_type,
            timestamp=datetime.now(UTC),
            description=description,
            inputs=inputs or {},
            outputs=outputs or {},
            metadata=metadata or {},
        )

        new_entries = [*self.entries, entry]
        return self.model_copy(update={"entries": new_entries})

    def mark_completed(self, *, success: bool = True, error_message: str | None = None) -> Trace:
        """Mark trace as completed and return new immutable trace.

        Args:
            success: Whether evaluation succeeded
            error_message: Error message if failed

        Returns:
            New Trace marked as completed

        """
        return self.model_copy(
            update={
                "completed_at": datetime.now(UTC),
                "success": success,
                "error_message": error_message,
            }
        )

    def get_duration_seconds(self) -> float | None:
        """Get evaluation duration in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()
