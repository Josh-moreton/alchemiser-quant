"""Business Unit: shared | Status: current.

Account snapshot schemas for deterministic reporting.

This module provides DTOs for capturing a complete account state snapshot
at the end of each trading cycle. Snapshots consolidate data from both Alpaca API
and internal ledger for reproducible reporting without live API calls.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware

__all__ = [
    "AccountSnapshot",
    "AlpacaAccountData",
    "AlpacaOrderData",
    "AlpacaPositionData",
    "InternalLedgerData",
    "StrategyPerformance",
]


class AlpacaAccountData(BaseModel):
    """DTO for Alpaca account information in snapshot.

    Captures key account metrics from Alpaca API at snapshot time.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    account_id: str = Field(..., min_length=1, description="Alpaca account ID")
    account_number: str = Field(..., min_length=1, description="Alpaca account number")
    status: str = Field(..., description="Account status (ACTIVE, etc.)")
    currency: str = Field(default="USD", description="Account currency")

    # Financial metrics - all Decimal for precision
    buying_power: Decimal = Field(..., ge=0, description="Available buying power")
    cash: Decimal = Field(..., description="Cash balance (can be negative)")
    equity: Decimal = Field(..., ge=0, description="Total equity")
    portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value")

    # P&L metrics
    unrealized_pl: Decimal | None = Field(default=None, description="Unrealized P&L")
    realized_pl: Decimal | None = Field(default=None, description="Realized P&L (if available)")

    # Additional metrics
    initial_margin: Decimal | None = Field(
        default=None, ge=0, description="Initial margin requirement"
    )
    maintenance_margin: Decimal | None = Field(
        default=None, ge=0, description="Maintenance margin requirement"
    )
    last_equity: Decimal | None = Field(default=None, ge=0, description="Previous day equity")

    # Metadata
    captured_at: datetime = Field(..., description="When this data was captured from Alpaca")

    @field_validator("captured_at")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure captured_at is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("captured_at cannot be None")
        return result


class AlpacaPositionData(BaseModel):
    """DTO for Alpaca position information in snapshot.

    Captures individual position state from Alpaca API.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    qty: Decimal = Field(..., description="Position quantity (can be negative for shorts)")
    market_value: Decimal = Field(..., description="Current market value")
    avg_entry_price: Decimal = Field(..., gt=0, description="Average entry price")
    current_price: Decimal = Field(..., gt=0, description="Current market price")

    # P&L
    unrealized_pl: Decimal = Field(..., description="Unrealized P&L")
    unrealized_plpc: Decimal = Field(..., description="Unrealized P&L percentage")

    # Additional position details
    cost_basis: Decimal = Field(..., description="Total cost basis")
    asset_id: str | None = Field(default=None, description="Alpaca asset ID")
    exchange: str | None = Field(default=None, description="Exchange")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()


class AlpacaOrderData(BaseModel):
    """DTO for Alpaca order information in snapshot.

    Captures recent order history from Alpaca API.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str = Field(..., min_length=1, description="Alpaca order ID")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    side: Literal["buy", "sell"] = Field(..., description="Order side")
    order_type: str = Field(..., description="Order type (market, limit, etc.)")
    status: str = Field(..., description="Order status")

    qty: Decimal = Field(..., gt=0, description="Order quantity")
    filled_qty: Decimal = Field(..., ge=0, description="Filled quantity")

    # Pricing
    limit_price: Decimal | None = Field(default=None, gt=0, description="Limit price if applicable")
    filled_avg_price: Decimal | None = Field(default=None, gt=0, description="Average fill price")

    # Timing
    submitted_at: datetime = Field(..., description="Order submission time")
    filled_at: datetime | None = Field(default=None, description="Order fill time")

    # Fee (if available from Alpaca - not always provided)
    commission: Decimal | None = Field(default=None, ge=0, description="Commission fee")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("submitted_at", "filled_at")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamps are timezone-aware."""
        if v is None:
            return None
        return ensure_timezone_aware(v)


class StrategyPerformance(BaseModel):
    """DTO for per-strategy performance metrics.

    Captures performance data for a single strategy based on trade ledger analysis.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    strategy_name: str = Field(..., min_length=1, description="Strategy name")

    # Trade counts
    total_trades: int = Field(..., ge=0, description="Total number of trades for this strategy")
    buy_trades: int = Field(..., ge=0, description="Number of buy trades")
    sell_trades: int = Field(..., ge=0, description="Number of sell trades")

    # Trade volumes
    total_buy_value: Decimal = Field(..., ge=0, description="Total value of buy trades")
    total_sell_value: Decimal = Field(..., ge=0, description="Total value of sell trades")

    # P&L metrics (computed from matched buy/sell pairs)
    realized_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Realized P&L from completed buy/sell pairs",
    )
    gross_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Gross P&L (sell value - buy value)",
    )

    # Additional metrics
    symbols_traded: list[str] = Field(
        default_factory=list,
        description="List of symbols traded by this strategy",
    )
    allocation_weight: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Current allocation weight for this strategy (0-1)",
    )

    # Time range for these metrics
    first_trade_at: datetime | None = Field(
        default=None,
        description="Timestamp of first trade for this strategy",
    )
    last_trade_at: datetime | None = Field(
        default=None,
        description="Timestamp of last trade for this strategy",
    )


class InternalLedgerData(BaseModel):
    """DTO for internal ledger information in snapshot.

    Captures our internal transaction tracking and strategy attribution.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    ledger_id: str = Field(..., min_length=1, description="Ledger identifier")

    # Transaction history
    total_trades: int = Field(..., ge=0, description="Total number of trades recorded")
    total_buy_value: Decimal = Field(..., ge=0, description="Total value of buy trades")
    total_sell_value: Decimal = Field(..., ge=0, description="Total value of sell trades")

    # Strategy attribution
    strategies_active: list[str] = Field(
        default_factory=list,
        description="List of active strategy names",
    )
    strategy_allocations: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Strategy allocation weights",
    )

    # Per-strategy performance metrics
    strategy_performance: dict[str, StrategyPerformance] = Field(
        default_factory=dict,
        description="Performance metrics for each strategy (strategy_name -> metrics)",
    )

    # Most recent trades (limited sample for audit)
    recent_trades: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recent trade entries (serialized as dicts)",
    )


class AccountSnapshot(BaseModel):
    """Complete account snapshot for deterministic reporting.

    Aggregates data from Alpaca API and internal ledger into a single,
    versioned, immutable snapshot with integrity verification.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Metadata
    snapshot_version: str = Field(
        default="1.0",
        description="Schema version for backward compatibility",
    )
    snapshot_id: str = Field(..., min_length=1, description="Unique snapshot identifier")
    account_id: str = Field(..., min_length=1, description="Account identifier")

    # Timing
    period_start: datetime = Field(..., description="Start of the trading period")
    period_end: datetime = Field(..., description="End of the trading period")
    created_at: datetime = Field(..., description="When this snapshot was created")

    # Correlation tracking
    correlation_id: str = Field(
        ...,
        min_length=1,
        description="Workflow correlation ID that triggered this snapshot",
    )

    # Aggregated data
    alpaca_account: AlpacaAccountData = Field(
        ...,
        description="Alpaca account data at snapshot time",
    )
    alpaca_positions: list[AlpacaPositionData] = Field(
        default_factory=list,
        description="All positions from Alpaca",
    )
    alpaca_orders: list[AlpacaOrderData] = Field(
        default_factory=list,
        description="Recent orders from Alpaca",
    )
    internal_ledger: InternalLedgerData = Field(
        ...,
        description="Internal ledger transaction data",
    )

    # Integrity
    checksum: str | None = Field(
        default=None,
        description="SHA256 checksum of snapshot data for integrity verification",
    )

    # Additional context
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional snapshot metadata (market status, warnings, etc.)",
    )

    @field_validator("period_start", "period_end", "created_at")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamps are timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("Timestamp cannot be None")
        return result

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum of snapshot data for integrity verification.

        Returns:
            Hex string of SHA256 checksum

        """
        # Create a deterministic representation excluding the checksum field itself
        data = self.model_dump(exclude={"checksum"}, mode="json")

        # Sort keys for deterministic serialization
        json_str = json.dumps(data, sort_keys=True, default=str)

        # Compute SHA256
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def verify_checksum(self) -> bool:
        """Verify snapshot integrity using checksum.

        Returns:
            True if checksum matches, False otherwise

        """
        if self.checksum is None:
            return False

        computed = self.compute_checksum()
        return computed == self.checksum

    @property
    def s3_key(self) -> str:
        """Generate deterministic S3 key for this snapshot.

        Returns:
            S3 key path in format: snapshots/{account_id}/{YYYY}/{MM}/{DD}/{HHmm}_snapshot.json

        """
        # Use period_end for path generation (when the trading cycle completed)
        ts = self.period_end

        # Format: snapshots/{account_id}/{YYYY}/{MM}/{DD}/{HHmm}_snapshot.json
        return (
            f"snapshots/{self.account_id}/"
            f"{ts.year:04d}/{ts.month:02d}/{ts.day:02d}/"
            f"{ts.hour:02d}{ts.minute:02d}_snapshot.json"
        )
