#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Schemas for daily PnL tracking in DynamoDB.

This module defines the canonical daily PnL data structure for persistent storage
and retrieval. Daily PnL entries track equity, profit/loss (adjusted for deposits
and withdrawals), and provide the single source of truth for historical performance.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ISO 8601 date pattern (YYYY-MM-DD format)
_ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
_ISO_TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"


class DailyPnLRecord(BaseModel):
    """Immutable daily PnL record for DynamoDB persistence.

    This is the canonical representation of daily portfolio performance,
    adjusted for deposits and withdrawals to reflect true trading P&L.

    Settlement Logic (T+1):
    - Deposits settle on the next trading day after they're made
    - `deposits_settled` tracks deposits that settled TODAY (made on prev trading day or weekend)
    - `pnl_amount` = equity_change - deposits_settled (true trading P&L)
    - `raw_pnl` = Alpaca's reported P&L (for reference/debugging)

    Attributes:
        date: ISO 8601 date (YYYY-MM-DD) - partition key
        equity: Total account equity at end of day (USD)
        pnl_amount: Daily profit/loss in dollars, adjusted for deposits/withdrawals (T+1 settlement)
        pnl_percent: Daily profit/loss as percentage
        raw_pnl: Alpaca's reported P&L before deposit adjustment (for transparency)
        deposits_settled: Deposits that settled on this day (from prev trading day or weekends)
        deposits: Total deposits made on this calendar day (CSD activities)
        withdrawals: Total withdrawals on this day (CSW activities)
        timestamp: ISO 8601 timestamp when record was captured
        environment: Environment (dev/staging/prod)
        schema_version: Schema version for compatibility tracking

    Example:
        >>> record = DailyPnLRecord(
        ...     date="2025-01-15",
        ...     equity=Decimal("10500.00"),
        ...     pnl_amount=Decimal("250.00"),
        ...     pnl_percent=Decimal("2.44"),
        ...     raw_pnl=Decimal("250.00"),
        ...     deposits_settled=Decimal("0"),
        ...     deposits=Decimal("0"),
        ...     withdrawals=Decimal("0"),
        ...     timestamp="2025-01-15T21:00:00Z",
        ...     environment="prod"
        ... )
        >>> record.equity
        Decimal('10500.00')

    """

    model_config = ConfigDict(strict=True, frozen=True)

    date: str = Field(
        pattern=_ISO_DATE_PATTERN,
        description="ISO 8601 date (YYYY-MM-DD) - DynamoDB partition key",
    )
    equity: Decimal = Field(
        ge=0,
        description="Total account equity at end of day (USD)",
    )
    pnl_amount: Decimal = Field(
        description="Daily P&L in dollars, adjusted for deposits/withdrawals (T+1 settlement)",
    )
    pnl_percent: Decimal = Field(
        description="Daily P&L as percentage",
    )
    raw_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Alpaca's reported P&L before deposit adjustment (for transparency)",
    )
    deposits_settled: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Deposits that settled on this day (from prev trading day or weekends)",
    )
    deposits: Decimal = Field(
        ge=0,
        description="Total deposits made on this calendar day (CSD activities)",
    )
    withdrawals: Decimal = Field(
        ge=0,
        description="Total withdrawals on this day (CSW activities)",
    )
    timestamp: str = Field(
        pattern=_ISO_TIMESTAMP_PATTERN,
        description="ISO 8601 timestamp when record was captured",
    )
    environment: str = Field(
        description="Environment (dev/staging/prod)",
    )
    schema_version: str = Field(
        default="1.1",
        description="Schema version for compatibility tracking (1.1 adds raw_pnl, deposits_settled)",
    )
