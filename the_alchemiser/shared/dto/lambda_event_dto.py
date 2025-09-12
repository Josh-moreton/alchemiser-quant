#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Lambda event data transfer objects for AWS Lambda event handling.

Provides typed DTOs for Lambda event parsing and cross-module coordination.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LambdaEventDTO(BaseModel):
    """DTO for AWS Lambda event data.

    Used for parsing Lambda events to determine trading mode and configuration.
    Supports both trading and signal-only modes with market hours override.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    mode: str | None = Field(default=None, description="Execution mode")
    trading_mode: str | None = Field(default=None, description="Trading mode (paper/live)")
    ignore_market_hours: bool | None = Field(
        default=None, description="Whether to ignore market hours"
    )
    arguments: list[str] | None = Field(
        default=None, description="Additional command line arguments"
    )
