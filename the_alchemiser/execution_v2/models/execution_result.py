"""Business Unit: execution | Status: current.

Execution result schemas for execution_v2 module.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Execution status classification."""

    SUCCESS = "success"  # All orders succeeded
    PARTIAL_SUCCESS = "partial_success"  # Some orders succeeded, some failed
    FAILURE = "failure"  # All orders failed or no orders placed


class OrderResult(BaseModel):
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
    error_message: str | None = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(..., description="Order execution timestamp")


class ExecutionResult(BaseModel):
    """Complete execution result for a rebalance plan."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    success: bool = Field(..., description="Overall execution success")
    status: ExecutionStatus = Field(..., description="Detailed execution status classification")
    plan_id: str = Field(..., description="Rebalance plan ID")
    correlation_id: str = Field(..., description="Correlation ID for traceability")
    orders: list[OrderResult] = Field(default_factory=list, description="Individual order results")
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of successful orders")
    total_trade_value: Decimal = Field(..., description="Total dollar value traded")
    execution_timestamp: datetime = Field(..., description="Execution completion timestamp")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata only"
    )  # Arbitrary JSON-serializable metadata for serialization only; type safety is not required, so Any is justified.

    @classmethod
    def classify_execution_status(
        cls, orders_placed: int, orders_succeeded: int
    ) -> tuple[bool, ExecutionStatus]:
        """Classify execution status based on order results.

        Args:
            orders_placed: Total number of orders placed
            orders_succeeded: Number of orders that succeeded

        Returns:
            Tuple of (success_flag, status_classification)

        """
        if orders_placed == 0:
            return False, ExecutionStatus.FAILURE
        if orders_succeeded == orders_placed:
            return True, ExecutionStatus.SUCCESS
        if orders_succeeded > 0:
            return False, ExecutionStatus.PARTIAL_SUCCESS  # Some succeeded, some failed
        return False, ExecutionStatus.FAILURE

    @property
    def is_partial_success(self) -> bool:
        """Check if execution was a partial success."""
        return self.status == ExecutionStatus.PARTIAL_SUCCESS

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


# TODO: Remove in Phase 3 - Temporary backward compatibility aliases
OrderResultDTO = OrderResult
ExecutionResultDTO = ExecutionResult
