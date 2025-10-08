"""Business Unit: shared | Status: current.

Broker-specific DTOs for shared use.

This module provides DTOs that can be used by shared components like AlpacaManager
without creating circular dependencies with execution module.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from the_alchemiser.shared.schemas.base import Result


class WebSocketStatus(str, Enum):
    """WebSocket operation status enumeration."""

    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"


class WebSocketResult(BaseModel):
    """Outcome of WebSocket operations (status, message, completed orders).

    Consolidated DTO used by both execution and shared modules to avoid duplication.
    Replaces duplicate definitions in execution.core.execution_schemas.

    Example:
        >>> result = WebSocketResult(
        ...     status=WebSocketStatus.COMPLETED,
        ...     message="Successfully monitored order completion",
        ...     completed_order_ids=["order123", "order456"],
        ...     metadata={"duration_ms": 1500}
        ... )
        >>> result.status
        <WebSocketStatus.COMPLETED: 'completed'>

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")
    status: WebSocketStatus = Field(description="WebSocket operation status")
    message: str = Field(description="Status message")
    completed_order_ids: list[str] = Field(
        default_factory=list, description="Order IDs that completed during operation"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OrderExecutionResult(Result):
    """DTO for order execution results.

    Consolidated DTO used by both execution and shared modules to avoid duplication.
    Adds uniform success/error fields to align with prior facade contract
    (which exposed a 'success' flag) while preserving structured status.

    Example:
        >>> from datetime import UTC, datetime
        >>> from decimal import Decimal
        >>> result = OrderExecutionResult(
        ...     success=True,
        ...     order_id="abc123",
        ...     status="filled",
        ...     filled_qty=Decimal("10.5"),
        ...     avg_fill_price=Decimal("150.25"),
        ...     submitted_at=datetime.now(UTC),
        ...     completed_at=datetime.now(UTC),
        ...     schema_version="1.0"
        ... )
        >>> result.filled_qty
        Decimal('10.5')

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Schema versioning
    schema_version: str = Field(default="1.0", description="DTO schema version")

    # Core execution data
    order_id: str = Field(description="Unique order identifier")
    status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = Field(
        description="Current order status"
    )
    filled_qty: Decimal = Field(description="Quantity filled (non-negative)")
    avg_fill_price: Decimal | None = Field(
        default=None, description="Average fill price (positive if filled)"
    )
    submitted_at: datetime = Field(description="Order submission timestamp (UTC)")
    completed_at: datetime | None = Field(
        default=None, description="Order completion timestamp (UTC, if completed)"
    )

    @field_validator("filled_qty")
    @classmethod
    def validate_filled_qty(cls, v: Decimal) -> Decimal:
        """Validate that filled quantity is non-negative.

        Args:
            v: Filled quantity value to validate

        Returns:
            Validated filled quantity

        Raises:
            ValueError: If quantity is negative

        """
        if v < 0:
            raise ValueError("Filled quantity cannot be negative")
        return v

    @field_validator("avg_fill_price")
    @classmethod
    def validate_avg_fill_price(cls, v: Decimal | None) -> Decimal | None:
        """Validate that average fill price is positive when present.

        Args:
            v: Average fill price to validate (or None)

        Returns:
            Validated price or None

        Raises:
            ValueError: If price is zero or negative

        """
        if v is not None and v <= 0:
            raise ValueError("Average fill price must be greater than 0")
        return v

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_at(cls, v: datetime) -> datetime:
        """Validate that submitted_at is timezone-aware (UTC).

        Args:
            v: Submission timestamp to validate

        Returns:
            Validated timezone-aware timestamp

        Raises:
            ValueError: If timestamp is not timezone-aware

        """
        if v.tzinfo is None:
            raise ValueError("submitted_at must be timezone-aware (UTC)")
        return v

    @field_validator("completed_at")
    @classmethod
    def validate_completed_at(cls, v: datetime | None) -> datetime | None:
        """Validate that completed_at is timezone-aware (UTC) when present.

        Args:
            v: Completion timestamp to validate (or None)

        Returns:
            Validated timezone-aware timestamp or None

        Raises:
            ValueError: If timestamp is present but not timezone-aware

        """
        if v is not None and v.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware (UTC)")
        return v

    @model_validator(mode="after")
    def validate_status_quantity_consistency(self) -> Self:
        """Validate consistency between order status and filled quantity.

        Ensures that:
        - Status 'filled' requires filled_qty > 0
        - Status 'accepted' should have filled_qty == 0
        - Status 'filled' requires avg_fill_price to be set

        Returns:
            Validated model instance

        Raises:
            ValueError: If status and quantity are inconsistent

        """
        if self.status == "filled":
            if self.filled_qty <= 0:
                raise ValueError("Status 'filled' requires filled_qty > 0")
            if self.avg_fill_price is None:
                raise ValueError("Status 'filled' requires avg_fill_price to be set")
        
        if self.status == "accepted" and self.filled_qty != 0:
            raise ValueError("Status 'accepted' should have filled_qty = 0")
        
        return self
