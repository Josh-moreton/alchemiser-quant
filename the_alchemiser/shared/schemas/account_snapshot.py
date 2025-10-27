"""Business Unit: shared | Status: current.

Account snapshot schemas for deterministic reporting.

This module provides DTOs for capturing complete account state snapshots
that combine Alpaca API data with internal trade ledger data for reproducible
reporting and analysis.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class AlpacaAccountData(BaseModel):
    """DTO for Alpaca account information in snapshot.

    Captures account-level financial metrics and status at snapshot time.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    account_id: str = Field(..., min_length=1, description="Alpaca account ID")
    account_number: str | None = Field(default=None, description="Alpaca account number")
    status: str = Field(..., description="Account status (e.g., ACTIVE)")
    currency: str = Field(default="USD", description="Account currency")
    buying_power: Decimal = Field(..., ge=0, description="Available buying power")
    cash: Decimal = Field(..., ge=0, description="Cash balance")
    equity: Decimal = Field(..., ge=0, description="Total equity")
    portfolio_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    last_equity: Decimal | None = Field(default=None, ge=0, description="Previous day equity")
    long_market_value: Decimal | None = Field(
        default=None, ge=0, description="Long positions market value"
    )
    short_market_value: Decimal | None = Field(
        default=None, description="Short positions market value"
    )
    initial_margin: Decimal | None = Field(default=None, ge=0, description="Initial margin")
    maintenance_margin: Decimal | None = Field(default=None, ge=0, description="Maintenance margin")


class AlpacaPositionData(BaseModel):
    """DTO for individual position in snapshot."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(..., min_length=1, description="Trading symbol")
    qty: Decimal = Field(..., description="Quantity held")
    qty_available: Decimal | None = Field(
        default=None, description="Quantity available for trading"
    )
    avg_entry_price: Decimal = Field(..., gt=0, description="Average entry price")
    current_price: Decimal = Field(..., gt=0, description="Current market price")
    market_value: Decimal = Field(..., description="Current market value")
    cost_basis: Decimal = Field(..., description="Total cost basis")
    unrealized_pl: Decimal = Field(..., description="Unrealized profit/loss")
    unrealized_plpc: Decimal = Field(..., description="Unrealized P/L percentage")
    unrealized_intraday_pl: Decimal | None = Field(
        default=None, description="Unrealized intraday P/L"
    )
    unrealized_intraday_plpc: Decimal | None = Field(
        default=None, description="Unrealized intraday P/L percentage"
    )
    side: str = Field(..., description="Position side (long/short)")
    asset_class: str = Field(default="us_equity", description="Asset class")


class AlpacaOrderData(BaseModel):
    """DTO for order information in snapshot."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str = Field(..., min_length=1, description="Order ID")
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    side: str = Field(..., description="Order side (buy/sell)")
    order_type: str = Field(..., description="Order type (market/limit/etc)")
    qty: Decimal | None = Field(default=None, gt=0, description="Order quantity")
    notional: Decimal | None = Field(default=None, gt=0, description="Order notional value")
    filled_qty: Decimal = Field(default=Decimal("0"), ge=0, description="Filled quantity")
    filled_avg_price: Decimal | None = Field(default=None, gt=0, description="Average fill price")
    status: str = Field(..., description="Order status")
    time_in_force: str = Field(..., description="Time in force")
    limit_price: Decimal | None = Field(default=None, gt=0, description="Limit price if applicable")
    stop_price: Decimal | None = Field(default=None, gt=0, description="Stop price if applicable")
    submitted_at: datetime = Field(..., description="Order submission timestamp")
    filled_at: datetime | None = Field(default=None, description="Order fill timestamp")
    expired_at: datetime | None = Field(default=None, description="Order expiration timestamp")
    canceled_at: datetime | None = Field(default=None, description="Order cancellation timestamp")

    @field_validator("submitted_at", "filled_at", "expired_at", "canceled_at")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime | None) -> datetime | None:
        """Ensure all timestamps are timezone-aware."""
        if v is None:
            return None
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("Timestamp cannot be None after timezone conversion")
        return result


class AccountSnapshot(BaseModel):
    """Complete account snapshot for deterministic reporting.

    Consolidates Alpaca account data to provide a complete, reproducible view of account state.
    Trade ledger data can be queried separately using the correlation_id.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Snapshot metadata
    snapshot_id: str = Field(..., min_length=1, description="Unique snapshot identifier")
    snapshot_version: str = Field(default="1.0", description="Snapshot schema version")
    account_id: str = Field(..., min_length=1, description="Account identifier")
    period_start: datetime = Field(..., description="Period start timestamp")
    period_end: datetime = Field(..., description="Period end timestamp")
    correlation_id: str = Field(
        ..., min_length=1, description="Workflow correlation ID for querying trade ledger"
    )
    created_at: datetime = Field(..., description="Snapshot creation timestamp")

    # Alpaca data (external API data that changes over time)
    alpaca_account: AlpacaAccountData = Field(..., description="Alpaca account data")
    alpaca_positions: list[AlpacaPositionData] = Field(
        default_factory=list, description="Alpaca positions"
    )
    alpaca_orders: list[AlpacaOrderData] = Field(default_factory=list, description="Alpaca orders")

    # Integrity
    checksum: str = Field(..., min_length=1, description="SHA-256 checksum for integrity")

    @field_validator("period_start", "period_end", "created_at")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime) -> datetime:
        """Ensure all timestamps are timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("Timestamp cannot be None")
        return result

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ttl_timestamp(self) -> int:
        """Compute TTL timestamp for DynamoDB (90 days from creation).

        Returns:
            Unix timestamp for TTL (90 days from created_at)

        """
        from datetime import timedelta

        ttl_date = self.created_at + timedelta(days=90)
        return int(ttl_date.timestamp())

    @staticmethod
    def calculate_checksum(snapshot_data: dict[str, Any]) -> str:
        """Calculate SHA-256 checksum for snapshot data.

        Args:
            snapshot_data: Snapshot data dictionary (without checksum field)

        Returns:
            SHA-256 hex digest

        """
        from ..utils.serialization import to_serializable

        # Create a copy without checksum field
        data_for_hash = {k: v for k, v in snapshot_data.items() if k != "checksum"}

        # Convert Decimal and other non-JSON-serializable types to proper strings
        serialized_data = to_serializable(data_for_hash)

        # Sort keys for deterministic serialization
        json_str = json.dumps(serialized_data, sort_keys=True)

        # Calculate SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()

    def verify_checksum(self) -> bool:
        """Verify the snapshot checksum.

        Returns:
            True if checksum is valid, False otherwise

        """
        # Exclude computed fields from checksum calculation
        snapshot_dict = self.model_dump(exclude={"ttl_timestamp"})
        calculated = self.calculate_checksum(snapshot_dict)
        return calculated == self.checksum
