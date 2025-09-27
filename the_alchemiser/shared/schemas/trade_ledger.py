#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade ledger data transfer objects for persistent trade tracking.

This module provides schemas for the trade ledger system that tracks all executions
per strategy for accurate performance attribution when multiple strategies
trade the same ticker.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class TradeSide(str, Enum):
    """Trade side enumeration."""

    BUY = "BUY"
    SELL = "SELL"


class AssetType(str, Enum):
    """Asset type enumeration."""

    STOCK = "STOCK"
    ETF = "ETF"
    CRYPTO = "CRYPTO"
    OPTION = "OPTION"
    FUTURE = "FUTURE"


class TradeLedgerEntry(BaseModel):
    """DTO for a single trade ledger entry representing one execution slice (fill).

    This is the atomic unit of trade recording, capturing each fill with complete
    traceability and idempotency support.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Unique identifiers for idempotency and traceability
    ledger_id: str = Field(..., min_length=1, description="Unique ledger entry identifier (UUID4)")
    event_id: str = Field(..., min_length=1, description="Event identifier from execution")
    correlation_id: str = Field(..., min_length=1, description="Workflow correlation identifier")
    causation_id: str = Field(..., min_length=1, description="Causation identifier for chaining")

    # Strategy attribution
    strategy_name: str = Field(..., min_length=1, description="Strategy that generated this trade")

    # Instrument identification
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    asset_type: AssetType | None = Field(default=None, description="Asset type classification")

    # Execution details
    side: TradeSide = Field(..., description="Trade side (BUY/SELL)")
    quantity: Decimal = Field(..., gt=0, description="Executed quantity")
    price: Decimal = Field(..., gt=0, description="Execution price per share")
    fees: Decimal = Field(default=Decimal("0"), ge=0, description="Total fees for this fill")
    timestamp: datetime = Field(..., description="Execution timestamp (UTC)")

    # Broker references for reconciliation
    order_id: str = Field(..., min_length=1, description="Broker order identifier")
    client_order_id: str | None = Field(default=None, description="Client-side order identifier")
    fill_id: str | None = Field(default=None, description="Broker fill/execution identifier")

    # Account and venue context
    account_id: str | None = Field(default=None, description="Trading account identifier")
    venue: str | None = Field(default=None, description="Execution venue (e.g., 'ALPACA')")

    # Metadata and versioning
    schema_version: int = Field(default=1, ge=1, description="Schema version for migrations")
    source: str = Field(..., min_length=1, description="Source module (e.g., 'execution_v2.core')")
    notes: str | None = Field(default=None, description="Optional execution notes")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("strategy_name", "source")
    @classmethod
    def normalize_strings(cls, v: str) -> str:
        """Normalize string fields."""
        return v.strip()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("timestamp cannot be None")
        return result

    @property
    def total_value(self) -> Decimal:
        """Calculate total trade value including fees."""
        base_value = self.quantity * self.price
        return base_value + self.fees

    @property
    def net_value(self) -> Decimal:
        """Calculate net trade value (negative for purchases, positive for sales)."""
        base_value = self.quantity * self.price
        if self.side == TradeSide.BUY:
            return -(base_value + self.fees)
        return base_value - self.fees

    def get_unique_key(self) -> tuple[str, str]:
        """Get unique key for idempotency checks.

        Returns:
            Tuple of (order_id, fill_id) for deduplication

        """
        return (self.order_id, self.fill_id or self.ledger_id)


class TradeLedgerQuery(BaseModel):
    """DTO for trade ledger query filters."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Filter criteria
    strategy_name: str | None = Field(default=None, description="Filter by strategy name")
    symbol: str | None = Field(default=None, description="Filter by symbol")
    asset_type: AssetType | None = Field(default=None, description="Filter by asset type")
    side: TradeSide | None = Field(default=None, description="Filter by trade side")
    account_id: str | None = Field(default=None, description="Filter by account ID")

    # Date range filtering
    start_date: datetime | None = Field(default=None, description="Start of date range (inclusive)")
    end_date: datetime | None = Field(default=None, description="End of date range (inclusive)")

    # Pagination
    limit: int | None = Field(default=None, ge=1, le=10000, description="Maximum results to return")
    offset: int | None = Field(default=None, ge=0, description="Number of results to skip")

    # Ordering
    order_by: Literal["timestamp", "symbol", "strategy_name"] = Field(
        default="timestamp", description="Field to order results by"
    )
    ascending: bool = Field(default=True, description="Sort order (True for ascending)")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str | None) -> str | None:
        """Normalize symbol to uppercase."""
        return v.strip().upper() if v else None

    @field_validator("strategy_name")
    @classmethod
    def normalize_strategy_name(cls, v: str | None) -> str | None:
        """Normalize strategy name."""
        return v.strip() if v else None

    @field_validator("start_date", "end_date")
    @classmethod
    def ensure_timezone_aware_dates(cls, v: datetime | None) -> datetime | None:
        """Ensure date filters are timezone-aware."""
        if v is None:
            return None
        return ensure_timezone_aware(v)


class AccountValueQuery(BaseModel):
    """DTO for account value query filters."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Filter criteria
    account_id: str | None = Field(default=None, description="Filter by account ID")

    # Date range filtering
    start_date: datetime | None = Field(default=None, description="Start of date range (inclusive)")
    end_date: datetime | None = Field(default=None, description="End of date range (inclusive)")

    # Pagination
    limit: int | None = Field(default=None, ge=1, le=10000, description="Maximum results to return")
    offset: int | None = Field(default=None, ge=0, description="Number of results to skip")

    # Ordering
    ascending: bool = Field(default=True, description="Sort order (True for ascending)")

    @field_validator("start_date", "end_date")
    @classmethod
    def ensure_timezone_aware_dates(cls, v: datetime | None) -> datetime | None:
        """Ensure date filters are timezone-aware."""
        if v is None:
            return None
        return ensure_timezone_aware(v)


class Lot(BaseModel):
    """DTO representing a lot (position slice) for attribution tracking."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Lot identification
    lot_id: str = Field(..., min_length=1, description="Unique lot identifier")
    strategy_name: str = Field(..., min_length=1, description="Strategy that owns this lot")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")

    # Position details
    quantity: Decimal = Field(..., gt=0, description="Lot quantity (always positive)")
    cost_basis: Decimal = Field(..., gt=0, description="Average cost per share for this lot")
    opened_timestamp: datetime = Field(..., description="When this lot was opened")

    # Attribution details
    opening_ledger_ids: list[str] = Field(
        description="Ledger entry IDs that created this lot", min_length=1
    )
    remaining_quantity: Decimal = Field(..., ge=0, description="Remaining unmatched quantity")

    # Optional metadata
    notes: str | None = Field(default=None, description="Optional lot notes")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("strategy_name")
    @classmethod
    def normalize_strategy_name(cls, v: str) -> str:
        """Normalize strategy name."""
        return v.strip()

    @field_validator("opened_timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("opened_timestamp cannot be None")
        return result

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost of remaining quantity."""
        return self.remaining_quantity * self.cost_basis

    @property
    def is_closed(self) -> bool:
        """Check if lot is fully closed."""
        return self.remaining_quantity == 0


class PerformanceSummary(BaseModel):
    """DTO for strategy performance summary."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Summary identification
    strategy_name: str = Field(..., min_length=1, description="Strategy name")
    symbol: str | None = Field(default=None, description="Symbol (None for all symbols)")
    calculation_timestamp: datetime = Field(..., description="When summary was calculated")

    # Realized P&L
    realized_pnl: Decimal = Field(default=Decimal("0"), description="Realized profit/loss")
    realized_trades: int = Field(default=0, ge=0, description="Number of completed round trips")

    # Open position summary
    open_quantity: Decimal = Field(default=Decimal("0"), ge=0, description="Total open quantity")
    open_lots_count: int = Field(default=0, ge=0, description="Number of open lots")
    average_cost_basis: Decimal | None = Field(
        default=None, ge=0, description="Weighted average cost basis of open position"
    )

    # Unrealized P&L (requires current price)
    current_price: Decimal | None = Field(default=None, gt=0, description="Current market price")
    unrealized_pnl: Decimal | None = Field(default=None, description="Unrealized profit/loss")

    # Trading activity summary
    total_buy_quantity: Decimal = Field(default=Decimal("0"), ge=0, description="Total bought")
    total_sell_quantity: Decimal = Field(default=Decimal("0"), ge=0, description="Total sold")
    total_fees: Decimal = Field(default=Decimal("0"), ge=0, description="Total fees paid")

    @field_validator("strategy_name")
    @classmethod
    def normalize_strategy_name(cls, v: str) -> str:
        """Normalize strategy name."""
        return v.strip()

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str | None) -> str | None:
        """Normalize symbol to uppercase."""
        return v.strip().upper() if v else None

    @field_validator("calculation_timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("calculation_timestamp cannot be None")
        return result

    @property
    def total_pnl(self) -> Decimal | None:
        """Calculate total P&L (realized + unrealized)."""
        if self.unrealized_pnl is None:
            return None
        return self.realized_pnl + self.unrealized_pnl

    @property
    def net_quantity(self) -> Decimal:
        """Calculate net quantity (buys - sells)."""
        return self.total_buy_quantity - self.total_sell_quantity


class AccountValueEntry(BaseModel):
    """DTO for account value snapshots in trade ledger for simplified tracking.

    This allows the trade ledger to support account value tracking with optional
    full trade logging disabled, providing a lightweight alternative for
    portfolio performance visualization.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Identification
    entry_id: str = Field(..., min_length=1, description="Unique identifier for this entry")
    account_id: str = Field(..., min_length=1, description="Account identifier")

    # Value information
    portfolio_value: Decimal = Field(..., description="Total portfolio value")
    cash: Decimal = Field(..., description="Cash balance")
    equity: Decimal = Field(..., description="Equity (positions + cash)")

    # Metadata
    timestamp: datetime = Field(..., description="Entry timestamp (timezone-aware)")
    source: str = Field(default="trade_ledger", description="Source system")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    def get_date_key(self) -> str:
        """Get date key for daily grouping (YYYY-MM-DD format)."""
        return self.timestamp.strftime("%Y-%m-%d")
