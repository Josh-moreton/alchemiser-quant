"""Business Unit: scripts | Status: current.

Portfolio snapshot models for backtesting.

Tracks portfolio state evolution across backtesting iterations.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PositionSnapshot(BaseModel):
    """Snapshot of a single position at a point in time."""

    model_config = ConfigDict(frozen=True, strict=True)

    symbol: str = Field(description="Stock symbol")
    quantity: Decimal = Field(description="Number of shares held")
    avg_entry_price: Decimal = Field(description="Average entry price", gt=0)
    current_price: Decimal = Field(description="Current market price", gt=0)
    market_value: Decimal = Field(description="Current market value", ge=0)
    unrealized_pnl: Decimal = Field(description="Unrealized profit/loss")


class PortfolioSnapshot(BaseModel):
    """Complete portfolio state at a point in time.

    Used to track portfolio evolution during backtesting.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(description="Snapshot timestamp (UTC)")
    cash: Decimal = Field(description="Available cash", ge=0)
    positions: dict[str, PositionSnapshot] = Field(
        description="Positions by symbol", default_factory=dict
    )
    total_value: Decimal = Field(description="Total portfolio value (cash + positions)", ge=0)
    day_pnl: Decimal = Field(description="P&L for the day", default=Decimal("0"))
    total_pnl: Decimal = Field(description="Total P&L since start", default=Decimal("0"))


class TradeRecord(BaseModel):
    """Record of a single trade execution in backtest."""

    model_config = ConfigDict(frozen=True, strict=True)

    timestamp: datetime = Field(description="Trade execution time")
    symbol: str = Field(description="Stock symbol")
    side: str = Field(description="BUY or SELL")
    quantity: Decimal = Field(description="Number of shares", gt=0)
    price: Decimal = Field(description="Execution price", gt=0)
    commission: Decimal = Field(description="Commission paid", ge=0)
    total_cost: Decimal = Field(description="Total cost including commission")
