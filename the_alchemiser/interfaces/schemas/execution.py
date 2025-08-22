#!/usr/bin/env python3
"""
Trading execution and result DTOs for The Alchemiser Trading System.

This module contains DTOs for trading execution results, order processing,
and system integration, moved from domain/types.py as part of the Pydantic migration.
"""

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict

from the_alchemiser.domain.types import AccountInfo, OrderDetails


# Trading Execution Types
class ExecutionResult(TypedDict):
    """Result of trading execution."""

    orders_executed: list[OrderDetails]
    account_info_before: AccountInfo
    account_info_after: AccountInfo
    execution_summary: dict[str, Any]
    final_portfolio_state: dict[str, Any] | None


class ExecutionResultDTO(BaseModel):
    """
    DTO for trading execution results.

    Provides an immutable, validated container for trading execution
    outcomes, replacing dict usage with enhanced type safety
    and validation capabilities.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    orders_executed: list[OrderDetails]
    account_info_before: AccountInfo
    account_info_after: AccountInfo
    execution_summary: dict[str, Any]
    final_portfolio_state: dict[str, Any] | None = None


class TradingPlan(TypedDict):
    """Trading execution plan."""

    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: float
    estimated_price: float
    reasoning: str


# Order Processing Types
class LimitOrderResult(TypedDict):
    """Result of limit order processing."""

    order_request: Any | None  # LimitOrderRequest - using Any to avoid import
    error_message: str | None


class WebSocketResult(TypedDict):
    """WebSocket operation result."""

    status: Literal["completed", "timeout", "error"]
    message: str
    orders_completed: list[str]


# Quote and Market Data Types
class QuoteData(TypedDict):
    """Real-time quote data."""

    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: str


# Integration Types
class LambdaEvent(TypedDict, total=False):
    """AWS Lambda event data."""

    mode: str | None
    trading_mode: str | None
    ignore_market_hours: bool | None
    arguments: list[str] | None


class OrderHistoryData(TypedDict):
    """Order history data structure."""

    orders: list[OrderDetails]
    metadata: dict[str, Any]
