#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

General execution result DTOs for The Alchemiser Trading System.

This module contains DTOs for general operation results, including
success/error handling patterns used across the trading system.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Consistent success/error patterns
- Type safety for operation results
- Comprehensive field validation
"""

from __future__ import annotations

import warnings
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, field_validator

from the_alchemiser.shared.schemas.base import Result

if TYPE_CHECKING:
    from the_alchemiser.shared.value_objects.core_types import OrderStatusLiteral


class TerminalOrderError(str, Enum):
    """Error types indicating an order is already in a terminal state.

    These are not actual errors - they indicate the order has completed
    or been terminated and cannot be modified further.
    """

    ALREADY_FILLED = "already_filled"
    ALREADY_CANCELLED = "already_cancelled"
    ALREADY_REJECTED = "already_rejected"
    ALREADY_EXPIRED = "already_expired"


class OperationResult(Result):
    """Generic DTO for operation results with success/error handling.
    
    Examples:
        >>> result = OperationResult(success=True, error=None)
        >>> result = OperationResult(
        ...     success=False,
        ...     error="Operation failed",
        ...     details={"reason": "timeout", "code": "500"}
        ... )
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    details: dict[str, object] | None = None


class OrderCancellationResult(Result):
    """DTO for order cancellation results.
    
    Examples:
        >>> result = OrderCancellationResult(
        ...     success=True,
        ...     error=None,
        ...     order_id="order-123"
        ... )
        >>> result = OrderCancellationResult(
        ...     success=True,
        ...     error="already_filled",
        ...     order_id="order-456"
        ... )
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None

    @field_validator("order_id")
    @classmethod
    def validate_order_id_not_empty(cls, v: str | None) -> str | None:
        """Ensure order_id is not empty string if provided."""
        if v is not None and v.strip() == "":
            raise ValueError("order_id must not be empty string")
        return v


class OrderStatusResult(Result):
    """DTO for order status query results.
    
    Examples:
        >>> result = OrderStatusResult(
        ...     success=True,
        ...     error=None,
        ...     order_id="order-123",
        ...     status="filled"
        ... )
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None
    status: str | None = None  # Uses OrderStatusLiteral at runtime

    @field_validator("order_id")
    @classmethod
    def validate_order_id_not_empty(cls, v: str | None) -> str | None:
        """Ensure order_id is not empty string if provided."""
        if v is not None and v.strip() == "":
            raise ValueError("order_id must not be empty string")
        return v


# Backward compatibility aliases - will be removed in version 3.0.0
def __getattr__(name: str) -> type:
    """Provide deprecated aliases with warnings."""
    if name == "OperationResultDTO":
        warnings.warn(
            "OperationResultDTO is deprecated, use OperationResult instead. "
            "Will be removed in version 3.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        return OperationResult
    elif name == "OrderCancellationDTO":
        warnings.warn(
            "OrderCancellationDTO is deprecated, use OrderCancellationResult instead. "
            "Will be removed in version 3.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        return OrderCancellationResult
    elif name == "OrderStatusDTO":
        warnings.warn(
            "OrderStatusDTO is deprecated, use OrderStatusResult instead. "
            "Will be removed in version 3.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        return OrderStatusResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Keep direct aliases for type checkers and backwards compatibility
OperationResultDTO = OperationResult
OrderCancellationDTO = OrderCancellationResult
OrderStatusDTO = OrderStatusResult
