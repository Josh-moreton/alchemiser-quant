"""Business Unit: shared | Status: current.

Trade ledger schemas for recording filled order information.

This module provides DTOs for tracking filled orders with strategy attribution,
market data at execution time, and comprehensive order details.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class TradeLedgerEntry(BaseModel):
    """DTO for individual trade ledger entry.

    Records a filled order with all available market data and strategy attribution.
    Designed to handle cases where data may be partially available without blocking
    the recording of core trade information.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core trade identification
    order_id: str = Field(..., min_length=1, description="Broker order ID")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for traceability")

    # Asset and direction
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    direction: Literal["BUY", "SELL"] = Field(..., description="Trade direction")

    # Quantity and pricing
    filled_qty: Decimal = Field(..., gt=0, description="Filled quantity")
    fill_price: Decimal = Field(..., gt=0, description="Average fill price")

    # Market data at time of fill (optional)
    bid_at_fill: Decimal | None = Field(default=None, gt=0, description="Bid price at fill time")
    ask_at_fill: Decimal | None = Field(default=None, gt=0, description="Ask price at fill time")

    # Timing
    fill_timestamp: datetime = Field(..., description="Time and date of fill")

    # Order characteristics
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] = Field(
        ..., description="Order type"
    )

    # Strategy attribution (supports multi-strategy aggregation)
    strategy_names: list[str] = Field(
        default_factory=list,
        description="List of strategies that contributed to this order",
    )
    strategy_weights: dict[str, Decimal] | None = Field(
        default=None,
        description="Optional strategy weight allocation (strategy_name -> weight 0-1)",
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("fill_timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure fill timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("fill_timestamp cannot be None")
        return result

    @field_validator("strategy_weights")
    @classmethod
    def validate_strategy_weights(cls, v: dict[str, Decimal] | None) -> dict[str, Decimal] | None:
        """Validate strategy weights sum to approximately 1.0."""
        if v is None:
            return None

        if not v:
            raise ValueError("strategy_weights cannot be empty if provided")

        total = sum(v.values())
        # Allow small tolerance for rounding
        if not (Decimal("0.99") <= total <= Decimal("1.01")):
            raise ValueError(f"Strategy weights must sum to ~1.0, got {total}")

        return v


class TradeLedger(BaseModel):
    """DTO for collection of trade ledger entries.

    Maintains a list of all recorded trades with metadata for tracking
    and analysis purposes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    entries: list[TradeLedgerEntry] = Field(
        default_factory=list, description="List of trade ledger entries"
    )
    ledger_id: str = Field(..., min_length=1, description="Unique ledger identifier")
    created_at: datetime = Field(..., description="Ledger creation timestamp")

    @field_validator("created_at")
    @classmethod
    def ensure_timezone_aware_created_at(cls, v: datetime) -> datetime:
        """Ensure created_at timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("created_at cannot be None")
        return result

    @property
    def total_entries(self) -> int:
        """Get total number of entries in ledger."""
        return len(self.entries)

    @property
    def total_buy_value(self) -> Decimal:
        """Calculate total value of BUY trades."""
        return sum(
            entry.filled_qty * entry.fill_price
            for entry in self.entries
            if entry.direction == "BUY"
        )

    @property
    def total_sell_value(self) -> Decimal:
        """Calculate total value of SELL trades."""
        return sum(
            entry.filled_qty * entry.fill_price
            for entry in self.entries
            if entry.direction == "SELL"
        )
