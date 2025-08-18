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

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Self

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
