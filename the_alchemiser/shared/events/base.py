#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Base event class for event-driven architecture.

Provides the foundation event class that all system events inherit from,
with correlation tracking and serialization support.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..constants import EVENT_TYPE_DESCRIPTION, UTC_TIMEZONE_SUFFIX
from ..utils.timezone_utils import ensure_timezone_aware
from ..schemas.types import UtcDatetime


class BaseEvent(BaseModel):
    """Base class for all events in the system.

    Provides common fields for correlation tracking, timing, and metadata.
    All specific events should inherit from this class.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Required correlation fields for traceability
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )

    # Event identification and timing
    event_id: str = Field(..., min_length=1, description="Unique event identifier")
    event_type: str = Field(..., min_length=1, description=EVENT_TYPE_DESCRIPTION)
    timestamp: UtcDatetime = Field(..., description="Event timestamp")

    # Event source and context
    source_module: str = Field(..., min_length=1, description="Module that emitted the event")
    source_component: str | None = Field(
        default=None, description="Specific component that emitted the event"
    )

    # Optional metadata for extensibility
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional event-specific metadata"
    )

    def __init__(self, **data: str | datetime | dict[str, Any] | None) -> None:
        """Initialize event with timezone-aware timestamp."""
        if "timestamp" in data and isinstance(data["timestamp"], datetime | type(None)):
            data["timestamp"] = ensure_timezone_aware(data["timestamp"])
        super().__init__(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization.

        Returns:
            Dictionary representation of the event with properly serialized values.

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseEvent:
        """Create event from dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            BaseEvent instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Convert string timestamp back to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                timestamp_str = data["timestamp"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + UTC_TIMEZONE_SUFFIX
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e

        return cls(**data)
