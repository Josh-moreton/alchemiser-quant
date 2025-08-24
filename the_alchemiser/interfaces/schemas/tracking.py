#!/usr/bin/env python3
"""
Strategy Tracking DTOs for The Alchemiser Trading System.

This module defines Pydantic v2 DTOs for strategy order tracking and execution
telemetry, consumed by application/tracking/strategy_order_tracker.py.

Key Features:
- Type-safe DTOs with comprehensive validation
- Strategy-aware order event tracking
- Execution summary aggregation with computed fields
- Strict mode validation with Decimal precision
- Symbol normalization and data integrity checks

Usage:
    from the_alchemiser.interfaces.schemas.tracking import (
        StrategyOrderEventDTO,
        StrategyExecutionSummaryDTO,
        OrderEventStatus,
        ExecutionStatus
    )

    # Create order event
    event = StrategyOrderEventDTO(
        event_id="evt_123",
        strategy="NUCLEAR",
        symbol="aapl",  # Will be normalized to "AAPL"
        side="buy",
        quantity=Decimal("100"),
        status="filled",
        price=Decimal("150.25"),
        ts=datetime.now(),
        error=None
    )

    # Create execution summary
    summary = StrategyExecutionSummaryDTO(
        strategy="NUCLEAR",
        symbol="AAPL",
        total_qty=Decimal("100"),
        avg_price=Decimal("150.25"),
        pnl=Decimal("250.50"),
        status="ok",
        details=[event]
    )
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Self, cast

from pydantic import BaseModel, Field, field_validator, model_validator

from the_alchemiser.domain.registry.strategy_registry import StrategyType


class OrderEventStatus(str, Enum):
    """Order event status enumeration."""

    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"
    CANCELED = "canceled"
    ERROR = "error"


class ExecutionStatus(str, Enum):
    """Execution summary status enumeration."""

    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


# Type alias for strategy validation using literal values from StrategyType
StrategyLiteral = Literal["NUCLEAR", "TECL", "KLM"]


class StrategyValidationMixin:
    """
    Mixin providing common validation methods for strategy tracking DTOs.

    Centralizes validation logic to eliminate code duplication while
    maintaining type safety and reusability across strategy DTO classes.
    """

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Validate strategy is a registered strategy type."""
        try:
            # Verify it's a valid strategy type
            StrategyType(v)
            return v
        except ValueError:
            valid_strategies = [s.value for s in StrategyType]
            raise ValueError(f"Strategy must be one of {valid_strategies}, got: {v}")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase and validate format."""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")

        symbol = v.strip().upper()

        # Basic symbol validation
        if not symbol.isalpha() or len(symbol) > 10:
            raise ValueError(f"Invalid symbol format: {symbol}")

        return symbol


class StrategyOrderEventDTO(BaseModel, StrategyValidationMixin):
    """
    Strategy order event DTO with comprehensive validation.

    Represents a single order event tagged with strategy information,
    providing immutable tracking of order lifecycle events.
    """

    # Event identification
    event_id: str = Field(..., min_length=1, description="Unique event identifier")

    # Strategy and symbol information
    strategy: StrategyLiteral = Field(..., description="Strategy name from registered strategies")
    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Stock symbol (normalized to uppercase)"
    )

    # Order details
    side: Literal["buy", "sell"] = Field(..., description="Order side")
    quantity: Decimal = Field(..., gt=0, description="Order quantity (positive decimal)")
    status: OrderEventStatus = Field(..., description="Order event status")

    # Pricing and timing
    price: Decimal | None = Field(
        None, ge=0, description="Order price (null for market orders initially)"
    )
    ts: datetime = Field(..., description="Event timestamp")

    # Error tracking
    error: str | None = Field(None, description="Error message if status indicates failure")

    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,  # Strip whitespace
        "validate_assignment": True,  # Validate on assignment
        "use_enum_values": True,  # Use enum values in serialization
    }

    @field_validator("quantity")
    @classmethod
    def validate_quantity_precision(cls, v: Decimal) -> Decimal:
        """Ensure quantity is a non-negative decimal with reasonable precision."""
        if v < 0:
            raise ValueError("Quantity must be non-negative")

        # Ensure reasonable precision (max 6 decimal places for fractional shares)
        # Only check for normal numbers (not infinity, NaN, etc.)
        if v.is_finite():
            exponent = v.as_tuple().exponent
            if isinstance(exponent, int) and exponent < -6:
                raise ValueError("Quantity precision too high (max 6 decimal places)")

        return v

    @model_validator(mode="after")
    def validate_error_status_consistency(self) -> Self:
        """Ensure error field is consistent with status."""
        if self.status in [OrderEventStatus.ERROR, OrderEventStatus.REJECTED]:
            if not self.error:
                raise ValueError(f"Error message required when status is {self.status}")
        elif self.error:
            # Allow error field for informational purposes even on success
            pass

        return self


class StrategyOrderDTO(BaseModel, StrategyValidationMixin):
    """
    Strategy order DTO representing a completed order with strategy information.

    This replaces the StrategyOrder dataclass with comprehensive validation,
    timestamp handling, and side normalization for consistent data representation.
    """

    order_id: str = Field(..., min_length=1, description="Unique order identifier")
    strategy: StrategyLiteral = Field(..., description="Strategy name from registered strategies")
    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Stock symbol (normalized to uppercase)"
    )
    side: Literal["buy", "sell"] = Field(..., description="Order side (normalized to lowercase)")
    quantity: Decimal = Field(..., gt=0, description="Order quantity (positive decimal)")
    price: Decimal = Field(..., ge=0, description="Order execution price")
    timestamp: datetime = Field(..., description="Order execution timestamp")

    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,  # Strip whitespace
        "validate_assignment": True,  # Validate on assignment
        "use_enum_values": True,  # Use enum values in serialization
    }

    @field_validator("side", mode="before")
    @classmethod
    def normalize_side(cls, v: str) -> str:
        """Normalize side to lowercase."""
        return v.lower().strip()

    @field_validator("quantity", "price")
    @classmethod
    def validate_financial_precision(cls, v: Decimal) -> Decimal:
        """Ensure financial values have reasonable precision."""
        if not v.is_finite():
            raise ValueError("Financial values must be finite")

        # Check precision for quantity (max 6 decimal places for fractional shares)
        exponent = v.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -6:
            raise ValueError("Precision too high (max 6 decimal places)")

        return v

    @classmethod
    def from_strategy_order_data(
        cls,
        order_id: str,
        strategy: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        timestamp: str | datetime | None = None,
    ) -> "StrategyOrderDTO":
        """Create DTO from raw order data (factory method for legacy compatibility)."""
        if timestamp is None:
            ts = datetime.now(UTC)
        elif isinstance(timestamp, str):
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            ts = timestamp

        return cls(
            order_id=order_id,
            strategy=cast(StrategyLiteral, strategy),
            symbol=symbol,
            side=cast(Literal["buy", "sell"], side),
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            timestamp=ts,
        )


class StrategyPositionDTO(BaseModel, StrategyValidationMixin):
    """
    Strategy position DTO with validation invariants and computed fields.

    Replaces StrategyPosition dataclass with strict validation for position
    invariants (e.g., non-negative quantities when position is closed).
    """

    strategy: StrategyLiteral = Field(..., description="Strategy name from registered strategies")
    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Stock symbol (normalized to uppercase)"
    )
    quantity: Decimal = Field(..., ge=0, description="Position quantity (non-negative)")
    average_cost: Decimal = Field(..., ge=0, description="Average cost per share")
    total_cost: Decimal = Field(..., ge=0, description="Total cost basis")
    last_updated: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,  # Strip whitespace
        "validate_assignment": True,  # Validate on assignment
        "use_enum_values": True,  # Use enum values in serialization
    }

    @model_validator(mode="after")
    def validate_position_invariants(self) -> Self:
        """Validate position invariants for data consistency."""
        # If position is closed (quantity = 0), cost fields should also be 0
        if self.quantity == 0:
            if self.total_cost != 0 or self.average_cost != 0:
                raise ValueError("Closed position (quantity=0) must have zero cost fields")

        # If position exists, average cost should be positive
        elif self.quantity > 0:
            if self.average_cost <= 0:
                raise ValueError("Open position must have positive average cost")

            # Validate total_cost consistency with quantity * average_cost
            expected_total = self.quantity * self.average_cost
            # Allow small floating point differences (within 0.01)
            if abs(self.total_cost - expected_total) > Decimal("0.01"):
                raise ValueError(
                    f"Total cost {self.total_cost} inconsistent with quantity * average_cost {expected_total}"
                )

        return self

    @classmethod
    def from_position_data(
        cls,
        strategy: str,
        symbol: str,
        quantity: float,
        average_cost: float,
        total_cost: float,
        last_updated: str | datetime | None = None,
    ) -> "StrategyPositionDTO":
        """Create DTO from raw position data (factory method for legacy compatibility)."""
        if last_updated is None:
            ts = datetime.now(UTC)
        elif isinstance(last_updated, str):
            ts = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        else:
            ts = last_updated

        return cls(
            strategy=cast(StrategyLiteral, strategy),
            symbol=symbol,
            quantity=Decimal(str(quantity)),
            average_cost=Decimal(str(average_cost)),
            total_cost=Decimal(str(total_cost)),
            last_updated=ts,
        )


class StrategyPnLDTO(BaseModel):
    """
    Strategy P&L DTO for serialization consistency and computed metrics.

    Replaces StrategyPnL dataclass with validation and computed fields
    for consistent P&L reporting across the system.
    """

    strategy: StrategyLiteral = Field(..., description="Strategy name from registered strategies")
    realized_pnl: Decimal = Field(..., description="Realized profit/loss")
    unrealized_pnl: Decimal = Field(..., description="Unrealized profit/loss")
    total_pnl: Decimal = Field(..., description="Total profit/loss")
    positions: dict[str, Decimal] = Field(
        default_factory=dict, description="Current positions by symbol (symbol -> quantity)"
    )
    allocation_value: Decimal = Field(..., ge=0, description="Total allocation value")

    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,  # Strip whitespace
        "validate_assignment": True,  # Validate on assignment
        "use_enum_values": True,  # Use enum values in serialization
    }

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Validate strategy is a registered strategy type."""
        try:
            # Verify it's a valid strategy type
            StrategyType(v)
            return v
        except ValueError:
            valid_strategies = [s.value for s in StrategyType]
            raise ValueError(f"Strategy must be one of {valid_strategies}, got: {v}")

    @field_validator("positions")
    @classmethod
    def validate_positions_format(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Validate position symbols and quantities."""
        validated_positions = {}
        for symbol, quantity in v.items():
            # Validate symbol format
            if not symbol or not symbol.strip() or not symbol.isalpha():
                raise ValueError(f"Invalid symbol format: {symbol}")

            # Normalize symbol to uppercase
            normalized_symbol = symbol.strip().upper()

            # Validate quantity is non-negative
            if quantity < 0:
                raise ValueError(
                    f"Position quantity must be non-negative, got {quantity} for {normalized_symbol}"
                )

            validated_positions[normalized_symbol] = quantity

        return validated_positions

    @model_validator(mode="after")
    def validate_pnl_consistency(self) -> Self:
        """Validate P&L calculation consistency."""
        # Total P&L should equal realized + unrealized
        expected_total = self.realized_pnl + self.unrealized_pnl
        if abs(self.total_pnl - expected_total) > Decimal(
            "0.01"
        ):  # Allow small rounding differences
            raise ValueError(
                f"Total P&L {self.total_pnl} inconsistent with realized {self.realized_pnl} + unrealized {self.unrealized_pnl}"
            )

        return self

    @property
    def total_return_pct(self) -> Decimal:
        """Calculate total return percentage."""
        if self.allocation_value <= 0:
            return Decimal("0.0")
        return (self.total_pnl / self.allocation_value) * Decimal("100")

    @property
    def position_count(self) -> int:
        """Count of non-zero positions."""
        return len([q for q in self.positions.values() if q > 0])

    @classmethod
    def from_pnl_data(
        cls,
        strategy: str,
        realized_pnl: float,
        unrealized_pnl: float,
        total_pnl: float,
        positions: dict[str, float],
        allocation_value: float,
    ) -> "StrategyPnLDTO":
        """Create DTO from raw P&L data (factory method for legacy compatibility)."""
        # Convert positions to Decimal
        decimal_positions = {symbol: Decimal(str(qty)) for symbol, qty in positions.items()}

        return cls(
            strategy=cast(StrategyLiteral, strategy),
            realized_pnl=Decimal(str(realized_pnl)),
            unrealized_pnl=Decimal(str(unrealized_pnl)),
            total_pnl=Decimal(str(total_pnl)),
            positions=decimal_positions,
            allocation_value=Decimal(str(allocation_value)),
        )


class StrategyExecutionSummaryDTO(BaseModel, StrategyValidationMixin):
    """
    Strategy execution summary DTO with aggregated metrics.

    Provides an immutable summary of strategy execution with computed
    fields and validation of aggregate data consistency.
    """

    # Strategy and symbol identification
    strategy: StrategyLiteral = Field(..., description="Strategy name from registered strategies")
    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Stock symbol (normalized to uppercase)"
    )

    # Aggregate metrics
    total_qty: Decimal = Field(
        ..., ge=0, description="Total quantity across all events (non-negative)"
    )
    avg_price: Decimal | None = Field(
        None, ge=0, description="Average execution price (null if no fills)"
    )
    pnl: Decimal | None = Field(None, description="Profit and loss (null if cannot be calculated)")

    # Status and details
    status: ExecutionStatus = Field(..., description="Overall execution status")
    details: list[StrategyOrderEventDTO] = Field(
        default_factory=list, description="List of order events (ordered by timestamp)"
    )

    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,  # Strip whitespace
        "validate_assignment": True,  # Validate on assignment
        "use_enum_values": True,  # Use enum values in serialization
    }

    @field_validator("total_qty")
    @classmethod
    def validate_total_qty_non_negative(cls, v: Decimal) -> Decimal:
        """Ensure total quantity is non-negative."""
        if v < 0:
            raise ValueError("Total quantity must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_event_ordering_and_consistency(self) -> Self:
        """Validate event ordering by timestamp and data consistency."""
        if not self.details:
            return self

        # Ensure events are ordered by timestamp
        sorted_events = sorted(self.details, key=lambda e: e.ts)
        if [e.ts for e in self.details] != [e.ts for e in sorted_events]:
            raise ValueError("Order events must be sorted by timestamp")

        # Validate all events belong to the same strategy and symbol
        for event in self.details:
            if event.strategy != self.strategy:
                raise ValueError(
                    f"Event strategy {event.strategy} doesn't match summary strategy {self.strategy}"
                )
            if event.symbol != self.symbol:
                raise ValueError(
                    f"Event symbol {event.symbol} doesn't match summary symbol {self.symbol}"
                )

        return self
