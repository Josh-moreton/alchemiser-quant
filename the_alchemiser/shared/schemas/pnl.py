#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Schemas for P&L analysis.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PnLData(BaseModel):
    """Immutable container for P&L analysis data."""

    model_config = ConfigDict(strict=True, frozen=True)

    period: str
    start_date: str
    end_date: str
    start_value: Decimal | None = None
    end_value: Decimal | None = None
    total_pnl: Decimal | None = None
    total_pnl_pct: Decimal | None = None
    daily_data: list[dict[str, Any]] = Field(default_factory=list)
