#!/usr/bin/env python3
"""
Alpaca Infrastructure DTOs for The Alchemiser Trading System.

This module provides Pydantic v2 DTOs for Alpaca API responses, ensuring
typed boundaries at the infrastructure layer. These DTOs map directly
to Alpaca API response structures and are used for validation and type safety.

Key Features:
- Direct mapping to Alpaca API response structures
- Decimal precision for financial values
- Comprehensive field validation
- Error response handling
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AlpacaOrderDTO(BaseModel):
    """
    DTO for Alpaca order responses.

    Maps directly to Alpaca order API response structure with proper
    validation and type conversion for financial values.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core order identification
    id: str = Field(description="Alpaca order ID")
    symbol: str = Field(description="Trading symbol")
    asset_class: str = Field(description="Asset class (equity, etc.)")

    # Order amounts and quantities
    notional: Decimal | None = Field(default=None, description="Notional dollar amount")
    qty: Decimal | None = Field(default=None, description="Quantity of shares")
    filled_qty: Decimal | None = Field(default=None, description="Filled quantity")
    filled_avg_price: Decimal | None = Field(default=None, description="Average fill price")

    # Order classification
    order_class: str = Field(description="Order class (simple, bracket, etc.)")
    order_type: str = Field(description="Order type (market, limit, etc.)")
    type: str = Field(description="Alias for order_type")
    side: Literal["buy", "sell"] = Field(description="Order side")
    time_in_force: str = Field(description="Time in force (day, gtc, etc.)")

    # Order status and timing
    status: str = Field(description="Order status")
    created_at: datetime = Field(description="Order creation timestamp")
    updated_at: datetime = Field(description="Order last update timestamp")
    submitted_at: datetime | None = Field(default=None, description="Order submission timestamp")
    filled_at: datetime | None = Field(default=None, description="Order fill timestamp")
    expired_at: datetime | None = Field(default=None, description="Order expiration timestamp")
    canceled_at: datetime | None = Field(default=None, description="Order cancellation timestamp")

    @field_validator("qty", "filled_qty", "notional", "filled_avg_price")
    @classmethod
    def validate_financial_values(cls, v: Decimal | None) -> Decimal | None:
        """Validate financial values are non-negative when provided."""
        if v is not None and v < 0:
            raise ValueError("Financial values cannot be negative")
        return v

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize symbol."""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        return v.strip().upper()


class AlpacaErrorDTO(BaseModel):
    """
    DTO for Alpaca API error responses.

    Provides structured error information with consistent format
    for error handling and debugging.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    code: int = Field(description="HTTP error code")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    request_id: str | None = Field(default=None, description="Request ID for tracking")

    @field_validator("code")
    @classmethod
    def validate_error_code(cls, v: int) -> int:
        """Validate error code is a valid HTTP status code."""
        if not (100 <= v <= 599):
            raise ValueError("Error code must be a valid HTTP status code")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate error message is not empty."""
        if not v or not v.strip():
            raise ValueError("Error message cannot be empty")
        return v.strip()
