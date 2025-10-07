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
    "OrderResultSummary",
    "ExecutionSummary",
    "TradeRunResult",
    "OrderAction",
    "ExecutionStatus",
    "TradingMode",
]


class OrderResultSummary(BaseModel):
    """Summary of a single order execution for CLI display."""

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
    order_id_redacted: str | None = Field(default=None, description="Last 6 chars of order ID")
    order_id_full: str | None = Field(default=None, description="Full order ID (for verbose)")
    success: bool = Field(..., description="Order success flag")
    error_message: str | None = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(..., description="Order execution timestamp")


class ExecutionSummary(BaseModel):
    """Summary of trading execution for CLI display."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    orders_total: int = Field(..., ge=0, description="Total number of orders")
    orders_succeeded: int = Field(..., ge=0, description="Number of successful orders")
    orders_failed: int = Field(..., ge=0, description="Number of failed orders")
    total_value: Decimal = Field(..., ge=0, description="Total dollar value traded")
    success_rate: float = Field(..., ge=0, le=1, description="Success rate (0-1)")
    execution_duration_seconds: float = Field(..., ge=0, description="Execution time in seconds")


class TradeRunResult(BaseModel):
    """Complete result of a trade execution run.

    This DTO replaces the boolean return from main.py and provides
    all information needed for CLI rendering and JSON output.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Core execution status
    status: str = Field(..., description="SUCCESS, FAILURE, or PARTIAL")
    success: bool = Field(..., description="Overall execution success flag")

    # Execution summary
    execution_summary: ExecutionSummary = Field(..., description="Execution metrics")

    # Order details (redacted by default)
    orders: list[OrderResultSummary] = Field(
        default_factory=list, description="Individual order results"
    )

    # Warnings and notifications
    warnings: list[str] = Field(
        default_factory=list, description="Non-critical warnings (e.g., email failures)"
    )

    # Execution metadata
    trading_mode: str = Field(..., description="PAPER or LIVE")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    correlation_id: str = Field(..., description="Correlation ID for traceability")

    # Additional context
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata"
    )

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
