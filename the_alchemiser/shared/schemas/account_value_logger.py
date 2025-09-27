#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Account Value Logger schema for daily account value tracking.

This module provides a simplified data transfer object for recording daily
account values, enabling portfolio performance visualization over time.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class AccountValueEntry(BaseModel):
    """DTO for a single account value entry representing daily portfolio value.
    
    This is a simplified version of trade ledger that just tracks account value
    over time for plotting and performance analysis.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Identification
    entry_id: str = Field(..., description="Unique identifier for this entry")
    account_id: str = Field(..., description="Account identifier")
    
    # Value information
    portfolio_value: Decimal = Field(..., description="Total portfolio value")
    cash: Decimal = Field(..., description="Cash balance")
    equity: Decimal = Field(..., description="Equity (positions + cash)")
    
    # Metadata
    timestamp: datetime = Field(..., description="Entry timestamp (timezone-aware)")
    source: str = Field(default="account_value_logger", description="Source system")
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    def get_date_key(self) -> str:
        """Get date key for daily grouping (YYYY-MM-DD format)."""
        return self.timestamp.strftime("%Y-%m-%d")


class AccountValueQuery(BaseModel):
    """Query filters for account value entries."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    account_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates(cls, v: datetime | None) -> datetime | None:
        """Ensure dates are timezone-aware if provided."""
        return ensure_timezone_aware(v) if v else None