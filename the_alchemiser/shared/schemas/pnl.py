#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Schemas for P&L analysis.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyPnLEntry(BaseModel):
    """Daily P&L entry with equity and profit/loss metrics.

    Attributes:
        date: ISO format date string (YYYY-MM-DD)
        equity: Total portfolio equity value at end of day
        profit_loss: Daily profit or loss amount
        profit_loss_pct: Daily profit or loss percentage

    """

    model_config = ConfigDict(strict=True, frozen=True)

    date: str
    equity: Decimal
    profit_loss: Decimal
    profit_loss_pct: Decimal


class PnLData(BaseModel):
    """Immutable container for P&L analysis data.

    Attributes:
        period: Human-readable period description
        start_date: ISO format start date
        end_date: ISO format end date
        start_value: Portfolio value at start of period
        end_value: Portfolio value at end of period
        total_pnl: Total profit/loss for period
        total_pnl_pct: Total profit/loss percentage
        daily_data: List of daily P&L entries

    """

    model_config = ConfigDict(strict=True, frozen=True)

    period: str
    start_date: str
    end_date: str
    start_value: Decimal | None = None
    end_value: Decimal | None = None
    total_pnl: Decimal | None = None
    total_pnl_pct: Decimal | None = None
    daily_data: list[DailyPnLEntry] = Field(default_factory=list)
