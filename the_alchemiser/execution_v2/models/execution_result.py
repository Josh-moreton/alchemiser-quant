"""Business Unit: execution | Status: current.

Execution result schemas for execution_v2 module.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Execution status classification."""

    SUCCESS = "success"  # All non-skipped orders succeeded
    PARTIAL_SUCCESS = "partial_success"  # Some orders succeeded, some failed (excludes skipped)
    FAILURE = "failure"  # All orders failed or no orders placed
    SUCCESS_WITH_SKIPS = "success_with_skips"  # All attempted orders succeeded, but some were skipped


class OrderResult(BaseModel):
    """Result of a single order execution."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="Schema version")
    symbol: str = Field(..., max_length=10, description="Trading symbol")
    action: Literal["BUY", "SELL"] = Field(..., description="BUY or SELL action")
    trade_amount: Decimal = Field(..., ge=Decimal("0"), description="Dollar amount traded")
    shares: Decimal = Field(..., ge=Decimal("0"), description="Number of shares ordered")
    price: Decimal | None = Field(default=None, gt=Decimal("0"), description="Execution price")
    order_id: str | None = Field(default=None, max_length=100, description="Broker order ID")
    success: bool = Field(..., description="Order success flag")
    skipped: bool = Field(default=False, description="Whether order was intentionally skipped")
    skip_reason: str | None = Field(
        default=None, max_length=500, description="Reason for skipping (if skipped=True)"
    )
    error_message: str | None = Field(
        default=None, max_length=1000, description="Error message if failed"
    )
    timestamp: datetime = Field(..., description="Order execution timestamp")
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] = Field(
        default="MARKET", description="Order type"
    )
    filled_at: datetime | None = Field(default=None, description="Fill timestamp")


class ExecutionResult(BaseModel):
    """Complete execution result for a rebalance plan."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="Schema version")
    success: bool = Field(..., description="Overall execution success")
    status: ExecutionStatus = Field(..., description="Detailed execution status classification")
    plan_id: str = Field(..., max_length=100, description="Rebalance plan ID")
    correlation_id: str = Field(..., max_length=100, description="Correlation ID for traceability")
    causation_id: str | None = Field(
        default=None, max_length=100, description="Causation ID for event sourcing"
    )
    orders: list[OrderResult] = Field(default_factory=list, description="Individual order results")
    orders_placed: int = Field(..., ge=0, description="Number of orders placed")
    orders_succeeded: int = Field(..., ge=0, description="Number of successful orders")
    orders_skipped: int = Field(default=0, ge=0, description="Number of orders skipped")
    total_trade_value: Decimal = Field(
        ..., ge=Decimal("0"), description="Total dollar value traded"
    )
    execution_timestamp: datetime = Field(..., description="Execution completion timestamp")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata only"
    )  # Arbitrary JSON-serializable metadata for serialization only; type safety is not required, so Any is justified.

    @classmethod
    def classify_execution_status(
        cls, orders_placed: int, orders_succeeded: int, orders_skipped: int = 0
    ) -> tuple[bool, ExecutionStatus]:
        """Classify execution status based on order results.

        The new classification logic treats skipped orders (due to bad market data or constraints)
        differently from failed orders (broker rejections). A run where all attempted orders
        succeed but some are skipped is considered successful.

        Args:
            orders_placed: Total number of orders placed (excludes skipped)
            orders_succeeded: Number of orders that succeeded
            orders_skipped: Number of orders intentionally skipped

        Returns:
            Tuple of (success_flag, status_classification)

        Classification Rules:
            - No orders placed and no skips: FAILURE
            - No orders placed but some skipped: SUCCESS_WITH_SKIPS (we chose not to trade)
            - All placed orders succeeded, no skips: SUCCESS
            - All placed orders succeeded, some skipped: SUCCESS_WITH_SKIPS
            - Some placed orders failed: PARTIAL_SUCCESS
            - All placed orders failed: FAILURE

        """
        # No activity at all
        if orders_placed == 0 and orders_skipped == 0:
            return False, ExecutionStatus.FAILURE

        # Only skips, no orders placed (chose not to trade due to bad data)
        if orders_placed == 0 and orders_skipped > 0:
            return True, ExecutionStatus.SUCCESS_WITH_SKIPS

        # All placed orders succeeded
        if orders_succeeded == orders_placed:
            if orders_skipped > 0:
                return True, ExecutionStatus.SUCCESS_WITH_SKIPS
            return True, ExecutionStatus.SUCCESS

        # Some placed orders succeeded, some failed
        if orders_succeeded > 0:
            return False, ExecutionStatus.PARTIAL_SUCCESS

        # All placed orders failed
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

    @staticmethod
    def create_skipped_order(
        symbol: str,
        action: str,
        shares: Decimal,
        skip_reason: str,
        timestamp: datetime | None = None,
    ) -> OrderResult:
        """Create an OrderResult for a skipped trade.

        Helper method to create consistent OrderResult objects when trades are
        intentionally skipped due to bad market data or other constraints.

        Args:
            symbol: Trading symbol
            action: "BUY" or "SELL"
            shares: Number of shares that would have been traded
            skip_reason: Reason for skipping the trade
            timestamp: Optional timestamp (defaults to now)

        Returns:
            OrderResult with skipped=True and success=False

        """
        return OrderResult(
            symbol=symbol,
            action=action.upper(),  # type: ignore[arg-type]
            trade_amount=Decimal("0"),  # No trade occurred
            shares=shares,
            price=None,  # No price since no order was placed
            order_id=None,  # No order placed
            success=False,  # Trade did not execute
            skipped=True,  # Explicitly skipped
            skip_reason=skip_reason,
            error_message=f"Trade skipped: {skip_reason}",
            timestamp=timestamp or datetime.now(UTC),
            order_type="MARKET",  # Default, not relevant for skipped orders
            filled_at=None,
        )
