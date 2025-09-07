"""Business Unit: execution | Status: current.

Consolidated order type definitions and enumerations.

This module consolidates all order-related type definitions including:
- OrderId (typed identifier)
- OrderStatus (enum)
- OrderStatusLiteral (from shared types)
- OrderType (market/limit specification)
- Side (buy/sell specification)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from the_alchemiser.shared.value_objects.identifier import Identifier
from the_alchemiser.shared.value_objects.core_types import OrderStatusLiteral

if TYPE_CHECKING:  # Only for static typing; avoids runtime circular import
    # Import the Order entity for precise typing during type checking only
    from the_alchemiser.execution.orders.order import Order

    OrderIdBase = Identifier[Order]
else:
    # At runtime, fall back to Any to prevent import cycles
    OrderIdBase = Identifier[Any]


class OrderId(OrderIdBase):
    """Typed identifier for orders."""


class OrderStatus(str, Enum):
    """Order status enumeration."""

    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"



@dataclass(frozen=True)
class OrderType:
    """Order type specification with validation."""

    value: Literal["market", "limit"]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        from the_alchemiser.shared.utils.validation_utils import (
            ORDER_TYPES,
            validate_enum_value,
        )

        validate_enum_value(self.value, ORDER_TYPES, "OrderType")


@dataclass(frozen=True)
class Side:
    """Order side (buy/sell) specification with validation."""

    value: Literal["buy", "sell"]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        from the_alchemiser.shared.utils.validation_utils import (
            ORDER_SIDES,
            validate_enum_value,
        )

        validate_enum_value(self.value, ORDER_SIDES, "Side")


__all__ = [
    "OrderId",
    "OrderStatus",
    "OrderStatusLiteral",
    "OrderType",
    "Side",
]
