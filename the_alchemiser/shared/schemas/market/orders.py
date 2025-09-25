#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Order request schemas for inter-module communication.

Provides typed schemas for order requests with correlation tracking and
serialization helpers for communication between portfolio and execution modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...utils.timezone_utils import ensure_timezone_aware


class OrderRequest(BaseModel):
    """Schema for order request data transfer.

    Used for communication from portfolio module to execution module.
    Includes correlation tracking and serialization helpers.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: datetime = Field(..., description="Order request timestamp")

    # Order identification
    request_id: str = Field(..., min_length=1, description="Unique request identifier")

    # Order parameters
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    side: Literal["BUY", "SELL"] = Field(..., description="Order side")
    quantity: Decimal | None = Field(default=None, gt=0, description="Quantity (shares)")
    notional: Decimal | None = Field(default=None, gt=0, description="Dollar amount")
    order_type: str = Field(default="market", description="Order type (market, limit, etc.)")
    time_in_force: str = Field(default="day", description="Time in force")

    # Optional limit price for limit orders
    limit_price: Decimal | None = Field(default=None, gt=0, description="Limit price")

    # Order execution metadata
    priority: int = Field(default=3, ge=1, le=5, description="Execution priority (1=highest)")
    execution_mode: str = Field(default="paper", description="Execution mode (paper/live)")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)


class MarketData(BaseModel):
    """Schema for market data used in order processing.

    Contains current market information needed for order validation
    and intelligent execution.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    timestamp: datetime = Field(..., description="Market data timestamp")
    
    # Price information
    last_price: Decimal | None = Field(default=None, gt=0, description="Last trade price")
    bid_price: Decimal | None = Field(default=None, gt=0, description="Current bid price")
    ask_price: Decimal | None = Field(default=None, gt=0, description="Current ask price")
    
    # Volume information
    volume: int | None = Field(default=None, ge=0, description="Current session volume")
    
    # Market status
    market_open: bool = Field(default=True, description="Whether market is open")
    
    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)