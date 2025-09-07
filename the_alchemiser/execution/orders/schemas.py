"""Business Unit: execution | Status: current.

Consolidated order schemas and DTOs for application layer boundaries.

This module consolidates order request domain objects and Pydantic DTOs:
- OrderRequest (domain value object)
- Order DTOs (Pydantic models for API boundaries)
- Validation mixins and result types
- Policy and execution result DTOs
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from the_alchemiser.execution.orders.order_types import OrderType, Side

# Import consolidated DTOs from shared to avoid duplication
from the_alchemiser.shared.dto.broker_dto import OrderExecutionResult as OrderExecutionResultDTO
from the_alchemiser.shared.types.money import Money
from the_alchemiser.shared.types.quantity import Quantity
from the_alchemiser.shared.types.time_in_force import TimeInForce
from the_alchemiser.shared.value_objects.symbol import Symbol

# Domain Value Objects


@dataclass(frozen=True)
class OrderRequest:
    """Domain value object for order requests.

    Immutable value object representing an order request with all required
    fields for trading. Uses strongly-typed domain value objects for
    validation and type safety.
    """

    symbol: Symbol
    side: Side
    quantity: Quantity
    order_type: OrderType
    time_in_force: TimeInForce
    limit_price: Money | None = None
    client_order_id: str | None = None

    def __post_init__(self) -> None:  # pragma: no cover - validation logic
        from the_alchemiser.shared.utils.validation_utils import validate_order_limit_price

        validate_order_limit_price(self.order_type.value, self.limit_price)

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side.value == "buy"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side.value == "sell"

    @property
    def is_market_order(self) -> bool:
        """Check if this is a market order."""
        return self.order_type.value == "market"

    @property
    def is_limit_order(self) -> bool:
        """Check if this is a limit order."""
        return self.order_type.value == "limit"


# Pydantic DTOs


class OrderValidationMixin:
    """Mixin providing common validation methods for order DTOs.

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
    """DTO for incoming order requests.

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
    """DTO for validated orders with derived and normalized fields.

    Contains all OrderRequest fields plus additional metadata
    from validation and normalization processes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core order fields (mirrored from OrderRequest)
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


class LimitOrderResultDTO(BaseModel):
    """DTO for limit order preparation results.

    Contains the result of limit order preparation including the order request data,
    conversion information, and success/failure status.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    success: bool
    order_request: Any | None = None  # Prepared broker order request
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


class PolicyWarningDTO(BaseModel):
    """DTO for policy warnings during order validation."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    message: str
    policy_name: str
    severity: Literal["low", "medium", "high"] = "medium"
    action: str | None = None
    original_value: Any | None = None
    adjusted_value: Any | None = None
    risk_level: str | None = None


class AdjustedOrderRequestDTO(OrderRequestDTO):
    """DTO for order requests that have been adjusted by policies."""

    adjustment_reason: str | None = None
    original_quantity: Decimal | None = None
    warnings: list[PolicyWarningDTO] = Field(default_factory=list)
    is_approved: bool = True
    rejection_reason: str | None = None
    policy_metadata: dict[str, Any] | None = None
    total_risk_score: Decimal | None = None


class RawOrderEnvelope(BaseModel):
    """Raw order envelope containing both the original order and execution result."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw_order: Any | None = None
    original_request: Any | None = None
    request_timestamp: datetime
    response_timestamp: datetime
    success: bool
    error_message: str | None = None


# Backward compatibility aliases
OrderRequest = OrderRequestDTO  # Pydantic version for API boundaries
ValidatedOrder = ValidatedOrderDTO
OrderExecutionResult = OrderExecutionResultDTO
LimitOrderResult = LimitOrderResultDTO
AdjustedOrderRequest = AdjustedOrderRequestDTO
PolicyWarning = PolicyWarningDTO


__all__ = [
    # Domain objects
    "OrderRequest",
    # DTOs
    "OrderRequestDTO",
    "ValidatedOrderDTO",
    "OrderExecutionResultDTO",
    "LimitOrderResultDTO",
    "PolicyWarningDTO",
    "AdjustedOrderRequestDTO",
    "RawOrderEnvelope",
    # Mixins
    "OrderValidationMixin",
    # Aliases for compatibility
    "ValidatedOrder",
    "OrderExecutionResult",
    "LimitOrderResult",
    "AdjustedOrderRequest",
    "PolicyWarning",
]
