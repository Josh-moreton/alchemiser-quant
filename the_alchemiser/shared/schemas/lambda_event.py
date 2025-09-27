#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Lambda event data transfer objects for AWS Lambda event handling.

Provides typed DTOs for Lambda event parsing and cross-module coordination.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LambdaEvent(BaseModel):
    """DTO for AWS Lambda event data.

    Used for parsing Lambda events to determine trading mode and configuration.
    Supports both trading and signal-only modes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Trading invocation fields
    mode: str | None = Field(default=None, description="Execution mode")
    trading_mode: str | None = Field(default=None, description="Trading mode (paper/live)")
    arguments: list[str] | None = Field(
        default=None, description="Additional command line arguments"
    )

    # Monthly summary invocation fields (optional)
    action: str | None = Field(
        default=None, description="Action to perform (e.g., 'monthly_summary')"
    )
    month: str | None = Field(
        default=None, description="Target month in YYYY-MM format (defaults to previous month)"
    )
    account_id: str | None = Field(
        default=None, description="Explicit account ID override for summary"
    )
    to: str | None = Field(default=None, description="Override recipient email address for summary")
    subject: str | None = Field(default=None, description="Override email subject for summary")
    dry_run: bool | None = Field(
        default=None, description="When true, compute summary but do not send email"
    )


# Backward compatibility alias retained intentionally; remove in future major version when safe
LambdaEventDTO = LambdaEvent
