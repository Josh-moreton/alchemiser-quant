"""Business Unit: shared | Status: current.

Schemas for account snapshot data stored in DynamoDB.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountSnapshot(BaseModel):
    """Account snapshot captured from Alpaca API.
    
    Stores complete account information at a point in time for historical tracking
    and dashboard display without requiring live API calls.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    # Identifiers
    snapshot_id: str = Field(description="Unique snapshot ID (e.g., 'ACCOUNT')")
    timestamp: str = Field(description="ISO 8601 timestamp when snapshot was taken")
    account_number: str = Field(description="Alpaca account number")
    
    # Account status
    status: str = Field(description="Account status (ACTIVE, ACCOUNT_CLOSED, etc.)")
    
    # Capital and equity
    cash: Decimal = Field(description="Cash balance (settled funds)")
    equity: Decimal = Field(description="Total account equity (cash + positions)")
    portfolio_value: Decimal = Field(description="Total portfolio value")
    
    # Buying power
    buying_power: Decimal = Field(description="Available buying power")
    regt_buying_power: Decimal = Field(description="Reg T buying power")
    daytrading_buying_power: Decimal = Field(description="Pattern day trader 4x buying power")
    
    # Margin information
    initial_margin: Decimal = Field(description="Initial margin requirement")
    maintenance_margin: Decimal = Field(description="Maintenance margin requirement")
    multiplier: str = Field(description="Account multiplier (1=cash, 2=margin, 4=PDT)")
    
    # P&L tracking
    last_equity: Decimal = Field(description="Previous day's ending equity")
    
    # Position summary
    long_market_value: Decimal = Field(default=Decimal("0"), description="Total long positions market value")
    short_market_value: Decimal = Field(default=Decimal("0"), description="Total short positions market value")
    
    # Account features
    pattern_day_trader: bool = Field(description="Whether account is marked as PDT")
    trading_blocked: bool = Field(description="Whether trading is blocked")
    transfers_blocked: bool = Field(description="Whether transfers are blocked")
    account_blocked: bool = Field(description="Whether account is blocked")
    
    # Metadata
    currency: str = Field(default="USD", description="Account currency")
    created_at: str | None = Field(default=None, description="Account creation timestamp")
    
    # TTL for DynamoDB (optional, set to 1 year from snapshot)
    ttl: int | None = Field(default=None, description="Unix timestamp for DynamoDB TTL")


class PositionSnapshot(BaseModel):
    """Individual position snapshot.
    
    Captures a single position at a point in time.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str = Field(description="Trading symbol")
    qty: Decimal = Field(description="Quantity held (positive for long, negative for short)")
    avg_entry_price: Decimal = Field(description="Average entry price")
    current_price: Decimal = Field(description="Current market price")
    market_value: Decimal = Field(description="Current market value")
    cost_basis: Decimal = Field(description="Total cost basis")
    unrealized_pl: Decimal = Field(description="Unrealized profit/loss in dollars")
    unrealized_plpc: Decimal = Field(description="Unrealized profit/loss in percent (0.0-1.0)")
    side: str = Field(description="Position side: 'long' or 'short'")
    
    # Optional fields
    change_today: Decimal | None = Field(default=None, description="Today's change in dollars")


class AccountSnapshotWithPositions(BaseModel):
    """Complete account snapshot including positions.
    
    Used for enriched dashboard display.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    account: AccountSnapshot = Field(description="Account-level snapshot")
    positions: list[PositionSnapshot] = Field(default_factory=list, description="Current positions")
    snapshot_timestamp: datetime = Field(description="When this snapshot was taken")
