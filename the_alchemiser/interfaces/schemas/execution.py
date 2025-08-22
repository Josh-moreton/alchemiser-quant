#!/usr/bin/env python3
"""
Trading execution and result DTOs for The Alchemiser Trading System.

This module contains Pydantic v2 DTOs for trading execution results, order processing,
and system integration, replacing TypedDict definitions with strongly typed, validated
structures as part of the Pydantic migration.

Key Features:
- Strict Pydantic v2 BaseModel with comprehensive validation
- Decimal precision for financial values (no float equality)
- Symbol normalization and comprehensive field validation
- Immutable DTOs with frozen=True for data integrity
- Type safety for execution lifecycle management

Usage:
    from the_alchemiser.interfaces.schemas.execution import (
        ExecutionResultDTO,
        TradingPlanDTO,
        WebSocketResultDTO,
        QuoteDTO,
        TradingAction,
        WebSocketStatus
    )

    # Create trading plan
    plan = TradingPlanDTO(
        symbol="aapl",  # Will be normalized to "AAPL"
        action=TradingAction.BUY,
        quantity=Decimal("100"),
        estimated_price=Decimal("150.25"),
        reasoning="Strong momentum signal"
    )
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from the_alchemiser.domain.types import AccountInfo, OrderDetails


class TradingAction(str, Enum):
    """Trading action enumeration."""
    
    BUY = "BUY"
    SELL = "SELL"


class WebSocketStatus(str, Enum):
    """WebSocket operation status enumeration."""
    
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"


class ExecutionResultDTO(BaseModel):
    """
    DTO for trading execution results.
    
    Contains the complete outcome of a trading execution cycle including
    orders executed, account state before/after, and execution summary.
    Used for reporting execution status and portfolio state changes.
    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    
    orders_executed: list[OrderDetails] = Field(
        description="List of orders that were executed during this cycle"
    )
    account_info_before: AccountInfo = Field(
        description="Account state before execution"
    )
    account_info_after: AccountInfo = Field(
        description="Account state after execution"
    )
    execution_summary: dict[str, Any] = Field(
        description="Summary of execution results and metrics"
    )
    final_portfolio_state: dict[str, Any] | None = Field(
        default=None,
        description="Final portfolio state after execution"
    )


class TradingPlanDTO(BaseModel):
    """
    DTO for trading execution plans.
    
    Contains the planned trading action with financial values validated
    using Decimal precision. Symbol is automatically normalized to uppercase.
    All financial values must be positive.
    """
    
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
        """Validate and normalize symbol to uppercase."""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        symbol = v.strip().upper()
        if not symbol.isalnum():
            raise ValueError("Symbol must be alphanumeric")
        return symbol
    
    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v
    
    @field_validator("estimated_price")
    @classmethod
    def validate_estimated_price(cls, v: Decimal) -> Decimal:
        """Validate estimated price is positive."""
        if v <= 0:
            raise ValueError("Estimated price must be greater than 0")
        return v


class LimitOrderResultDTO(BaseModel):
    """
    DTO for limit order processing results.
    
    Contains the outcome of limit order processing including the original
    request and any error messages encountered during processing.
    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    
    order_request: Any | None = Field(
        default=None,
        description="Original limit order request (LimitOrderRequest)"
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if order processing failed"
    )


class WebSocketResultDTO(BaseModel):
    """
    DTO for WebSocket operation results.
    
    Contains the outcome of WebSocket operations including status,
    message, and list of completed orders.
    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    
    status: WebSocketStatus = Field(description="WebSocket operation status")
    message: str = Field(description="Status or error message")
    orders_completed: list[str] = Field(
        default_factory=list,
        description="List of order IDs that were completed"
    )


class QuoteDTO(BaseModel):
    """
    DTO for real-time quote data.
    
    Contains bid/ask prices and sizes with Decimal precision for financial
    accuracy. All price and size values must be positive.
    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    
    bid_price: Decimal = Field(description="Bid price (must be positive)")
    ask_price: Decimal = Field(description="Ask price (must be positive)")
    bid_size: Decimal = Field(description="Bid size (must be positive)")
    ask_size: Decimal = Field(description="Ask size (must be positive)")
    timestamp: str = Field(description="Quote timestamp in ISO format")
    
    @field_validator("bid_price", "ask_price")
    @classmethod
    def validate_prices(cls, v: Decimal) -> Decimal:
        """Validate prices are positive."""
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v
    
    @field_validator("bid_size", "ask_size")
    @classmethod
    def validate_sizes(cls, v: Decimal) -> Decimal:
        """Validate sizes are positive."""
        if v <= 0:
            raise ValueError("Size must be greater than 0")
        return v


class LambdaEventDTO(BaseModel):
    """
    DTO for AWS Lambda event data.
    
    Contains optional configuration parameters for Lambda function execution
    including trading mode, market hours settings, and arguments.
    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    
    mode: str | None = Field(default=None, description="Execution mode")
    trading_mode: str | None = Field(default=None, description="Trading mode (paper/live)")
    ignore_market_hours: bool | None = Field(
        default=None,
        description="Whether to ignore market hours"
    )
    arguments: list[str] | None = Field(
        default=None,
        description="Additional command line arguments"
    )


class OrderHistoryDTO(BaseModel):
    """
    DTO for order history data.
    
    Contains historical order data with associated metadata for
    analysis and reporting purposes.
    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    
    orders: list[OrderDetails] = Field(
        description="List of historical orders"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the order history"
    )
