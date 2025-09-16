#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Error context DTO for consistent error reporting across modules.

Provides typed DTO for error context information, ensuring type safety
in error handling and reporting workflows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..utils.timezone_utils import ensure_timezone_aware


class ErrorContextDTO(BaseModel):
    """Standardized error context DTO with Pydantic v2 configuration.
    
    Provides immutable error context information for consistent error
    reporting and tracking across all modules.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    operation: str = Field(..., min_length=1, description="Operation being performed")
    component: str = Field(..., min_length=1, description="Component/module name")
    function_name: str | None = Field(default=None, description="Function name if available")
    request_id: str | None = Field(default=None, description="Request correlation ID")
    user_id: str | None = Field(default=None, description="User identifier if available")
    session_id: str | None = Field(default=None, description="Session identifier if available")
    additional_data: dict[str, str | int | float | bool] | None = Field(
        default=None, description="Additional context data"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Error occurrence timestamp"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for legacy compatibility."""
        return self.model_dump(mode="json")

    @classmethod
    def create(
        cls,
        operation: str,
        component: str,
        function_name: str | None = None,
        **additional_data: str | int | float | bool,
    ) -> ErrorContextDTO:
        """Create error context with additional data."""
        return cls(
            operation=operation,
            component=component,
            function_name=function_name,
            additional_data=additional_data if additional_data else None,
        )