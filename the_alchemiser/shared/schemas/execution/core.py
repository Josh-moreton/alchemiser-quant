"""Business Unit: shared | Status: current.

Execution-related schemas for order placement and tracking.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionResult(BaseModel):
    """Result of an order execution attempt.

    Contains all information about the order placement,
    whether successful or failed.

    Migrated from dataclass to Pydantic v2 for architecture compliance.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(description="Trading symbol")
    side: str = Field(description="Order side (buy/sell)")
    quantity: Decimal = Field(description="Order quantity")
    status: str = Field(description="Execution status")
    success: bool = Field(description="Whether execution was successful")
    execution_strategy: str = Field(description="Execution strategy used")
    order_id: str | None = Field(default=None, description="Order ID if available")
    price: Decimal | None = Field(default=None, description="Execution price")
    error: str | None = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Execution timestamp"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata"
    )
