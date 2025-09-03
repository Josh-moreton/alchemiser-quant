#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Trading execution and result DTOs for The Alchemiser Trading System.

Pydantic v2 DTOs supporting trading execution lifecycle, order processing,
websocket events, quotes, lambda events, and order history. Replaces legacy
TypedDict structures with immutable, validated models.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from the_alchemiser.shared.dto.execution_report_dto import ExecutionReportDTO
from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioStateDTO
from the_alchemiser.shared.value_objects.core_types import AccountInfo, OrderDetails


class TradingAction(str, Enum):
    """Trading action enumeration."""

    BUY = "BUY"
    SELL = "SELL"


class WebSocketStatus(str, Enum):
    """WebSocket operation status enumeration."""

    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"


class ExecutionResult(BaseModel):
    """Complete outcome of a trading execution cycle."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    orders_executed: list[OrderDetails] = Field(
        description="List of orders executed during this cycle"
    )
    account_info_before: AccountInfo = Field(description="Account state before execution")
    account_info_after: AccountInfo = Field(description="Account state after execution")
    execution_summary: ExecutionReportDTO = Field(
        description="Structured summary of execution results and metrics"
    )
    final_portfolio_state: PortfolioStateDTO | None = Field(
        default=None, description="Final portfolio state after execution"
    )


class TradingPlan(BaseModel):
    """Validated trading plan with normalized symbol and positive financial values."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(description="Trading symbol (normalized to uppercase)")
    action: TradingAction = Field(description="Trading action (BUY or SELL)")
    quantity: Decimal = Field(description="Quantity to trade (must be positive)")
    estimated_price: Decimal = Field(description="Estimated execution price (must be positive)")
    reasoning: str = Field(description="Reasoning behind the trading decision")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v or not v.strip():  # pragma: no cover - defensive
            raise ValueError("Symbol cannot be empty")
        symbol = v.strip().upper()
        if not symbol.isalnum():
            raise ValueError("Symbol must be alphanumeric")
        return symbol

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("estimated_price")
    @classmethod
    def validate_estimated_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Estimated price must be greater than 0")
        return v

    # NOTE: LimitOrderResultDTO moved to interfaces/schemas/orders.py to avoid duplicate
    # definitions and provide richer success/failure semantics. This placeholder comment
    # preserves historical context for the refactor.


class WebSocketResult(BaseModel):
    """Outcome of WebSocket operations (status, message, completed orders)."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    status: WebSocketStatus = Field(description="WebSocket operation status")
    message: str = Field(description="Status or error message")
    orders_completed: list[str] = Field(
        default_factory=list, description="List of completed order IDs"
    )


class Quote(BaseModel):
    """Real-time quote data with positive bid/ask prices and sizes."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    bid_price: Decimal = Field(description="Bid price (must be > 0)")
    ask_price: Decimal = Field(description="Ask price (must be > 0)")
    bid_size: Decimal = Field(description="Bid size (must be > 0)")
    ask_size: Decimal = Field(description="Ask size (must be > 0)")
    timestamp: str = Field(description="Quote timestamp in ISO format")

    @field_validator("bid_price", "ask_price")
    @classmethod
    def validate_prices(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("bid_size", "ask_size")
    @classmethod
    def validate_sizes(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Size must be greater than 0")
        return v


class LambdaEvent(BaseModel):
    """AWS Lambda event configuration parameters."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    mode: str | None = Field(default=None, description="Execution mode")
    trading_mode: str | None = Field(default=None, description="Trading mode (paper/live)")
    ignore_market_hours: bool | None = Field(
        default=None, description="Whether to ignore market hours"
    )
    arguments: list[str] | None = Field(
        default=None, description="Additional command line arguments"
    )


class OrderHistory(BaseModel):
    """Historical order data with metadata for analysis/reporting."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    orders: list[OrderDetails] = Field(description="List of historical orders")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the order history"
    )


__all__ = [
    # Primary DTO exports (new naming policy)
    "ExecutionResult",
    "LambdaEvent",
    "OrderHistory",
    "Quote",
    "TradingPlan",
    "WebSocketResult",
    # Backward compatibility aliases
    "ExecutionResultDTO",
    "LambdaEventDTO",
    "OrderHistoryDTO",
    "QuoteDTO",
    "TradingPlanDTO",
    "WebSocketResultDTO",
]


# Backward compatibility aliases - will be removed in future version
ExecutionResultDTO = ExecutionResult
LambdaEventDTO = LambdaEvent
OrderHistoryDTO = OrderHistory
QuoteDTO = Quote
TradingPlanDTO = TradingPlan
WebSocketResultDTO = WebSocketResult
