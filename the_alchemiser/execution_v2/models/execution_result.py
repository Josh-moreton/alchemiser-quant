"""Business Unit: execution | Status: current.

Execution result DTOs for execution_v2 module.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.dto import ErrorDTO


class OrderResultDTO(BaseModel):
    """Result of a single order execution."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="BUY or SELL action")
    trade_amount: Decimal = Field(..., description="Dollar amount traded")
    shares: Decimal = Field(..., description="Number of shares ordered")
    price: Decimal | None = Field(default=None, description="Execution price")
    order_id: str | None = Field(default=None, description="Broker order ID")
    success: bool = Field(..., description="Order success flag")
    error: ErrorDTO | None = Field(default=None, description="Error details if failed")
    timestamp: datetime = Field(..., description="Order execution timestamp")


class ExecutionResultDTO(BaseModel):
    """Complete execution result for a rebalance plan."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    success: bool = Field(..., description="Overall execution success")
    plan_id: str = Field(..., description="Rebalance plan ID")
    correlation_id: str = Field(..., description="Correlation ID for traceability")
    orders: list[OrderResultDTO] = Field(
        default_factory=list, description="Individual order results"
    )
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of successful orders")
    total_trade_value: Decimal = Field(..., description="Total dollar value traded")
    execution_timestamp: datetime = Field(..., description="Execution completion timestamp")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata only"
    )  # Arbitrary JSON-serializable metadata for serialization only; type safety is not required, so Any is justified.

    @property
    def success_rate(self) -> float:
        """Calculate order success rate."""
        if self.orders_placed == 0:
            return 1.0
        return self.orders_succeeded / self.orders_placed

    @property
    def failure_count(self) -> int:
        """Count of failed orders."""
        return self.orders_placed - self.orders_succeeded
