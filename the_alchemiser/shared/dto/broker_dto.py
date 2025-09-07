"""Business Unit: shared | Status: current.

Broker-specific DTOs for shared use.

This module provides DTOs that can be used by shared components like AlpacaManager
without creating circular dependencies with execution module.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

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
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Core execution data
    order_id: str
    status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]
    filled_qty: Decimal
    avg_fill_price: Decimal | None = None
    submitted_at: datetime
    completed_at: datetime | None = None

    @field_validator("filled_qty")
    @classmethod
    def validate_filled_qty(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Filled quantity cannot be negative")
        return v

    @field_validator("avg_fill_price")
    @classmethod
    def validate_avg_fill_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Average fill price must be greater than 0")
        return v


# Backward compatibility aliases
WebSocketResultDTO = WebSocketResult
OrderExecutionResultDTO = OrderExecutionResult
