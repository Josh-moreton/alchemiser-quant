"""Business Unit: shared | Status: current.

Trade ledger schemas for recording filled order information.

This module provides DTOs for tracking filled orders with strategy attribution,
market data at execution time, and comprehensive order details. Also includes
signal persistence schemas for recording strategy signals to DynamoDB.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

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
            (
                entry.filled_qty * entry.fill_price
                for entry in self.entries
                if entry.direction == "BUY"
            ),
            Decimal("0"),
        )

    @property
    def total_sell_value(self) -> Decimal:
        """Calculate total value of SELL trades."""
        return sum(
            (
                entry.filled_qty * entry.fill_price
                for entry in self.entries
                if entry.direction == "SELL"
            ),
            Decimal("0"),
        )


class SignalLedgerEntry(BaseModel):
    """DTO for signal ledger entry.

    Records a strategy signal with full context for persistence to DynamoDB.
    Enables complete audit trail from signal generation through trade execution.

    Attributes:
        signal_id: Unique signal identifier
        correlation_id: Workflow correlation ID for traceability
        causation_id: Event causation ID for event chain tracking
        timestamp: Signal generation timestamp (timezone-aware UTC)
        strategy_name: Name of strategy that generated the signal
        data_source: Data source identifier (e.g., "dsl_engine:1-KMLM.clj")
        symbol: Trading symbol
        action: Trading action (BUY, SELL, HOLD)
        target_allocation: Target portfolio allocation (0.0-1.0)
        signal_strength: Raw signal strength value (optional)
        reasoning: Human-readable signal reasoning
        lifecycle_state: Current lifecycle state of signal
        executed_trade_ids: List of trade IDs that executed based on this signal
        technical_indicators: Market context indicators at signal generation time
        signal_dto: Full StrategySignal DTO serialization for replay capability
        created_at: Record creation timestamp

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core signal identification
    signal_id: str = Field(..., min_length=1, description="Unique signal identifier")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for traceability")
    causation_id: str = Field(..., min_length=1, description="Causation ID for event tracing")
    timestamp: datetime = Field(..., description="Signal generation timestamp")

    # Strategy context
    strategy_name: str = Field(..., min_length=1, description="Strategy that generated signal")
    data_source: str = Field(
        ..., min_length=1, description="Data source (e.g., 'dsl_engine:1-KMLM.clj')"
    )

    # Signal details
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    action: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Trading action")
    target_allocation: Decimal = Field(..., ge=0, le=1, description="Target allocation (0-1)")
    signal_strength: Decimal | None = Field(
        default=None, ge=0, description="Raw signal strength value"
    )
    reasoning: str = Field(..., min_length=1, max_length=1000, description="Signal reasoning")

    # Lifecycle management
    lifecycle_state: Literal["GENERATED", "EXECUTED", "IGNORED", "SUPERSEDED"] = Field(
        default="GENERATED", description="Signal lifecycle state"
    )
    executed_trade_ids: list[str] = Field(
        default_factory=list, description="Trade IDs that executed based on this signal"
    )

    # Market context
    technical_indicators: dict[str, Any] | None = Field(
        default=None, description="Technical indicators at signal generation time"
    )

    # Full signal serialization for replay
    signal_dto: dict[str, Any] = Field(..., description="Full StrategySignal DTO serialization")

    # Metadata
    created_at: datetime = Field(..., description="Record creation timestamp")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp", "created_at")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime) -> datetime:
        """Ensure timestamps are timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("Timestamp cannot be None")
        return result
