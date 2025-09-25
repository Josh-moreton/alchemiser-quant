#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

System configuration and error schemas.

Provides typed schemas for system configuration and error handling
across the application.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Configuration(BaseModel):
    """Schema for system configuration data.

    Provides a structured way to handle configuration data
    with proper validation and type safety.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    config_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration data with structured validation",
    )


class Error(BaseModel):
    """Schema for structured error information.

    Provides standardized error reporting with proper validation
    and type safety for error handling across modules.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    error_type: str = Field(description="Type of error")
    message: str = Field(description="Error message")
    context: dict[str, Any] = Field(default_factory=dict, description="Error context data")