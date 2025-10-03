"""Business Unit: shared | Status: current.

Portfolio snapshot model for backtesting system.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PositionSnapshot(BaseModel):
    """Snapshot of a single position."""

    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str = Field(description="Trading symbol")
    quantity: Decimal = Field(description="Number of shares held")
    average_price: Decimal = Field(description="Average entry price")
    current_price: Decimal = Field(description="Current market price")
    market_value: Decimal = Field(description="Current market value")


class PortfolioSnapshot(BaseModel):
    """Complete portfolio state at a point in time."""

    model_config = ConfigDict(strict=True, frozen=True)

    date: datetime = Field(description="Snapshot date (UTC)")
    cash: Decimal = Field(description="Available cash")
    positions: dict[str, PositionSnapshot] = Field(
        default_factory=dict, description="Current positions by symbol"
    )
    total_value: Decimal = Field(description="Total portfolio value (cash + positions)")

    @classmethod
    def empty(cls, date: datetime, initial_cash: Decimal) -> PortfolioSnapshot:
        """Create an empty portfolio with only cash.
        
        Args:
            date: Portfolio date
            initial_cash: Starting cash amount
            
        Returns:
            Empty portfolio snapshot

        """
        return cls(date=date, cash=initial_cash, positions={}, total_value=initial_cash)
