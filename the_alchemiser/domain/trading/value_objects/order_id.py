"""Business Unit: order execution/placement; Status: current."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from the_alchemiser.domain.shared_kernel.value_objects.identifier import Identifier

if TYPE_CHECKING:  # Only for static typing; avoids runtime circular import
    # Import the Order entity for precise typing during type checking only
    from the_alchemiser.domain.trading.entities.order import Order

    OrderIdBase = Identifier[Order]
else:
    # At runtime, fall back to Any to prevent import cycles
    OrderIdBase = Identifier[Any]


class OrderId(OrderIdBase):
    """Typed identifier for orders."""
