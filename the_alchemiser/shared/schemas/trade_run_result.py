"""Business Unit: shared | Status: current.

Trade run result DTOs for the trading system.

This module provides structured DTOs for trade execution results, replacing
boolean returns from main.py with comprehensive, typed results that support
both CLI rendering and JSON serialization.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Type aliases for string enums
OrderAction = Literal["BUY", "SELL"]
ExecutionStatus = Literal["SUCCESS", "FAILURE", "PARTIAL"]
TradingMode = Literal["PAPER", "LIVE"]

__all__ = [
    "ExecutionStatus",
    "ExecutionSummary",
    "OrderAction",
    "OrderResultSummary",
    "TradeRunResult",
    "TradingMode",
]


class OrderResultSummary(BaseModel):
    """Summary of a single order execution for CLI display.

    Example:
        >>> from datetime import UTC, datetime
        >>> from decimal import Decimal
        >>> order = OrderResultSummary(
        ...     symbol="AAPL",
        ...     action="BUY",
        ...     trade_amount=Decimal("1000.00"),
        ...     shares=Decimal("10.5"),
        ...     price=Decimal("95.24"),
        ...     success=True,
        ...     timestamp=datetime.now(UTC),
        ...     schema_version="1.0"
        ... )

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")
    symbol: str = Field(..., max_length=20, description="Trading symbol")
    action: OrderAction = Field(..., description="BUY or SELL action")
    trade_amount: Decimal = Field(..., ge=0, description="Dollar amount traded")
    shares: Decimal = Field(..., ge=0, description="Number of shares ordered")
    price: Decimal | None = Field(default=None, gt=0, description="Execution price")
    order_id_redacted: str | None = Field(
        default=None, min_length=6, max_length=6, description="Last 6 chars of order ID"
    )
    order_id_full: str | None = Field(default=None, description="Full order ID (for verbose)")
    success: bool = Field(..., description="Order success flag")
    error_message: str | None = Field(
        default=None, max_length=1000, description="Error message if failed"
    )
    timestamp: datetime = Field(..., description="Order execution timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        if v.tzinfo is None:
            msg = "timestamp must be timezone-aware"
            raise ValueError(msg)
        return v


class ExecutionSummary(BaseModel):
    """Summary of trading execution for CLI display.

    Example:
        >>> from decimal import Decimal
        >>> summary = ExecutionSummary(
        ...     orders_total=10,
        ...     orders_succeeded=8,
        ...     orders_failed=2,
        ...     total_value=Decimal("50000.00"),
        ...     success_rate=0.8,
        ...     execution_duration_seconds=12.5,
        ...     schema_version="1.0"
        ... )

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")
    orders_total: int = Field(..., ge=0, description="Total number of orders")
    orders_succeeded: int = Field(..., ge=0, description="Number of successful orders")
    orders_failed: int = Field(..., ge=0, description="Number of failed orders")
    total_value: Decimal = Field(..., ge=0, description="Total dollar value traded")
    success_rate: float = Field(..., ge=0, le=1, description="Success rate (0-1)")
    execution_duration_seconds: float = Field(..., ge=0, description="Execution time in seconds")

    @model_validator(mode="after")
    def validate_order_counts(self) -> ExecutionSummary:
        """Validate that order counts are consistent."""
        total = self.orders_succeeded + self.orders_failed
        if total != self.orders_total:
            msg = (
                f"orders_succeeded ({self.orders_succeeded}) + "
                f"orders_failed ({self.orders_failed}) must equal "
                f"orders_total ({self.orders_total})"
            )
            raise ValueError(msg)
        return self


class TradeRunResult(BaseModel):
    """Complete result of a trade execution run.

    This DTO replaces the boolean return from main.py and provides
    all information needed for CLI rendering and JSON output.

    Example:
        >>> from datetime import UTC, datetime
        >>> from decimal import Decimal
        >>> result = TradeRunResult(
        ...     status="SUCCESS",
        ...     success=True,
        ...     execution_summary=ExecutionSummary(
        ...         orders_total=1,
        ...         orders_succeeded=1,
        ...         orders_failed=0,
        ...         total_value=Decimal("1000.00"),
        ...         success_rate=1.0,
        ...         execution_duration_seconds=5.0
        ...     ),
        ...     trading_mode="PAPER",
        ...     started_at=datetime.now(UTC),
        ...     completed_at=datetime.now(UTC),
        ...     correlation_id="550e8400-e29b-41d4-a716-446655440000",
        ...     schema_version="1.0"
        ... )

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    schema_version: str = Field(default="1.0", description="DTO schema version")

    # Core execution status
    status: ExecutionStatus = Field(..., description="SUCCESS, FAILURE, or PARTIAL")
    success: bool = Field(..., description="Overall execution success flag")

    # Execution summary
    execution_summary: ExecutionSummary = Field(..., description="Execution metrics")

    # Order details (redacted by default)
    orders: list[OrderResultSummary] = Field(
        default_factory=list, description="Individual order results"
    )

    # Warnings and notifications
    warnings: list[str] = Field(
        default_factory=list,
        max_length=100,
        description="Non-critical warnings (e.g., email failures)",
    )

    # Execution metadata
    trading_mode: TradingMode = Field(..., description="PAPER or LIVE")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    correlation_id: str = Field(
        ..., min_length=1, max_length=100, description="Correlation ID for traceability"
    )
    causation_id: str | None = Field(
        default=None, min_length=1, max_length=100, description="Causation ID for event chaining"
    )

    # Additional context
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata"
    )

    @field_validator("started_at", "completed_at")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime fields are timezone-aware."""
        if v.tzinfo is None:
            msg = "datetime fields must be timezone-aware"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_temporal_ordering(self) -> TradeRunResult:
        """Validate that completed_at is not before started_at."""
        if self.completed_at < self.started_at:
            msg = f"completed_at ({self.completed_at}) must be >= started_at ({self.started_at})"
            raise ValueError(msg)
        return self

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        return (self.completed_at - self.started_at).total_seconds()

    def to_json_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict for --json output."""
        return {
            "status": self.status,
            "success": self.success,
            "trading_mode": self.trading_mode,
            "orders_total": self.execution_summary.orders_total,
            "orders_succeeded": self.execution_summary.orders_succeeded,
            "orders_failed": self.execution_summary.orders_failed,
            "total_value": str(self.execution_summary.total_value),
            "success_rate": self.execution_summary.success_rate,
            "duration_seconds": self.duration_seconds,
            "warnings": self.warnings,
            "orders": [
                {
                    "symbol": order.symbol,
                    "action": order.action,
                    "trade_amount": str(order.trade_amount),
                    "shares": str(order.shares),
                    "price": str(order.price) if order.price else None,
                    "success": order.success,
                    "error_message": order.error_message,
                    "timestamp": order.timestamp.isoformat(),
                }
                for order in self.orders
            ],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "correlation_id": self.correlation_id,
        }
