#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Schemas for P&L analysis.

This module contains immutable DTOs for portfolio profit and loss data,
used for performance reporting and analysis.

Key Features:
- Decimal precision for all financial values
- Schema versioning for compatibility tracking
- Strict validation and frozen models
- ISO 8601 date format validation
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyPnLEntry(BaseModel):
    """Daily P&L entry with equity and profit/loss metrics.

    Immutable container for a single day's portfolio performance data.
    All financial values use Decimal for precision.

    Attributes:
        date: ISO 8601 date string (YYYY-MM-DD format)
        equity: Total portfolio equity value at end of day (must be non-negative)
        profit_loss: Daily profit or loss amount (can be negative)
        profit_loss_pct: Daily profit or loss percentage (can be negative)
        schema_version: Schema version for compatibility tracking

    Example:
        >>> entry = DailyPnLEntry(
        ...     date="2025-01-01",
        ...     equity=Decimal("10000.00"),
        ...     profit_loss=Decimal("500.00"),
        ...     profit_loss_pct=Decimal("5.00")
        ... )
        >>> entry.equity
        Decimal('10000.00')

    """

    model_config = ConfigDict(strict=True, frozen=True)

    date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO 8601 date (YYYY-MM-DD)",
    )
    equity: Decimal = Field(
        ge=0,
        description="Total portfolio equity at end of day",
    )
    profit_loss: Decimal = Field(
        description="Daily profit or loss amount",
    )
    profit_loss_pct: Decimal = Field(
        description="Daily profit or loss percentage",
    )
    schema_version: str = Field(
        default="1.0",
        description="Schema version for compatibility tracking",
    )


class PnLData(BaseModel):
    """Immutable container for P&L analysis data.

    Aggregated portfolio performance data for a specific time period.
    All financial values use Decimal for precision. Optional fields are
    None when no data is available for the period (e.g., no trading history).

    Attributes:
        period: Human-readable period description (e.g., "1W", "1M")
        start_date: ISO 8601 format start date (YYYY-MM-DD), None if no data
        end_date: ISO 8601 format end date (YYYY-MM-DD), None if no data
        start_value: Portfolio value at start of period (None if no data)
        end_value: Portfolio value at end of period (None if no data)
        total_pnl: Total profit/loss for period (None if no data)
        total_pnl_pct: Total profit/loss percentage (None if no data)
        daily_data: List of daily P&L entries (empty if no data)
        schema_version: Schema version for compatibility tracking

    Example:
        >>> pnl = PnLData(
        ...     period="1W",
        ...     start_date="2025-01-01",
        ...     end_date="2025-01-07",
        ...     start_value=Decimal("10000.00"),
        ...     end_value=Decimal("10500.00"),
        ...     total_pnl=Decimal("500.00"),
        ...     total_pnl_pct=Decimal("5.00")
        ... )
        >>> pnl.total_pnl
        Decimal('500.00')

    """

    model_config = ConfigDict(strict=True, frozen=True)

    period: str = Field(
        description="Human-readable period description",
    )
    start_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO 8601 start date (YYYY-MM-DD), None if no data available",
    )
    end_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO 8601 end date (YYYY-MM-DD), None if no data available",
    )
    start_value: Decimal | None = Field(
        default=None,
        ge=0,
        description="Portfolio value at period start (None if no data)",
    )
    end_value: Decimal | None = Field(
        default=None,
        ge=0,
        description="Portfolio value at period end (None if no data)",
    )
    total_pnl: Decimal | None = Field(
        default=None,
        description="Total profit/loss for period (None if no data)",
    )
    total_pnl_pct: Decimal | None = Field(
        default=None,
        description="Total profit/loss percentage (None if no data)",
    )
    daily_data: list[DailyPnLEntry] = Field(
        default_factory=list,
        description="Daily P&L breakdown (empty if no data)",
    )
    schema_version: str = Field(
        default="1.0",
        description="Schema version for compatibility tracking",
    )
