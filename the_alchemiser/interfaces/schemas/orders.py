"""
Order DTOs for application layer and interface boundaries.

This module provides Pydantic v2 DTOs for order handling, replacing loose dicts
and Any usages with strongly typed, validated structures. These DTOs are used
at system boundaries for serialization, validation, and type safety.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Decimal precision for financial values
- Comprehensive field validation and normalization
- Type safety for order lifecycle management
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from alpaca.trading.requests import LimitOrderRequest
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class OrderValidationMixin:
    """
    Mixin providing common validation methods for order DTOs.

    Centralizes validation logic to eliminate code duplication while
    maintaining type safety and reusability across order DTO classes.
    """

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

    @field_validator("limit_price")
    @classmethod
    def validate_limit_price_positive(cls, v: Decimal | None) -> Decimal | None:
        """Validate limit_price is positive when provided."""
        if v is not None and v <= 0:
            raise ValueError("Limit price must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_limit_price_required(self) -> OrderValidationMixin:
        """Validate limit_price is required for limit orders."""
        if hasattr(self, "order_type") and hasattr(self, "limit_price"):
            if self.order_type == "limit" and self.limit_price is None:
                raise ValueError("Limit price required for limit orders")
        return self


class OrderRequestDTO(BaseModel, OrderValidationMixin):
    """
    DTO for incoming order requests.

    Used when creating new orders from user input or API requests.
    Provides validation and normalization of order parameters.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    symbol: str
    side: Literal["buy", "sell"]
    quantity: Decimal
    order_type: Literal["market", "limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"] = "day"
    limit_price: Decimal | None = None
    client_order_id: str | None = None


class ValidatedOrderDTO(BaseModel, OrderValidationMixin):
    """
    DTO for validated orders with derived and normalized fields.

    Contains all OrderRequest fields plus additional metadata
    from validation and normalization processes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core order fields (mirrored from OrderRequestDTO)
    symbol: str
    side: Literal["buy", "sell"]
    quantity: Decimal
    order_type: Literal["market", "limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    limit_price: Decimal | None = None
    client_order_id: str | None = None

    # Derived/normalized fields from validation
    estimated_value: Decimal | None = None
    is_fractional: bool = False
    normalized_quantity: Decimal | None = None
    risk_score: Decimal | None = None
    validation_timestamp: datetime


class OrderExecutionResultDTO(BaseModel):
    """
    DTO for order execution results.

    Contains the outcome of order submission and execution tracking.
    Used for reporting execution status and filled quantities.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str
    status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]
    filled_qty: Decimal
    avg_fill_price: Decimal | None = None
    submitted_at: datetime
    completed_at: datetime | None = None

    @field_validator("filled_qty")
    @classmethod
    def validate_filled_qty(cls, v: Decimal) -> Decimal:
        """Validate filled quantity is non-negative."""
        if v < 0:
            raise ValueError("Filled quantity cannot be negative")
        return v

    @field_validator("avg_fill_price")
    @classmethod
    def validate_avg_fill_price(cls, v: Decimal | None) -> Decimal | None:
        """Validate average fill price is positive when provided."""
        if v is not None and v <= 0:
            raise ValueError("Average fill price must be greater than 0")
        return v


class LimitOrderResultDTO(BaseModel):
    """
    DTO for limit order preparation results.

    Contains the result of limit order preparation including the order request data,
    conversion information, and success/failure status. Used to replace tuple returns
    with strongly typed results.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    success: bool
    order_request: LimitOrderRequest | None = None  # Prepared LimitOrderRequest
    conversion_info: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def validate_result_consistency(self) -> LimitOrderResultDTO:
        """Validate consistency between success flag and other fields."""
        if self.success:
            if self.order_request is None:
                raise ValueError("order_request is required when success=True")
            if self.error_message is not None:
                raise ValueError("error_message must be None when success=True")
        else:
            if self.order_request is not None:
                raise ValueError("order_request must be None when success=False")
            if not self.error_message:
                raise ValueError("error_message is required when success=False")
        return self

    @property
    def is_success(self) -> bool:
        """Alias for success to align with other result DTO naming patterns."""
        return self.success
