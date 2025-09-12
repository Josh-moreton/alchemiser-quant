#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Execution data transfer objects for AWS Lambda event handling.

Provides typed DTOs for Lambda event parsing and execution coordination.
"""

from __future__ import annotations

from typing import Literal

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

    mode: Literal["trade", "bot"] | None = Field(
        default=None,
        description="Operation mode: 'trade' for trading, 'bot' for signals only"
    )
    ignore_market_hours: bool = Field(
        default=False,
        description="Whether to ignore market hours constraints"
    )