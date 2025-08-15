from __future__ import annotations

from typing import TYPE_CHECKING

from the_alchemiser.domain.shared_kernel.value_objects.identifier import Identifier

if TYPE_CHECKING:  # Only for type checking to avoid runtime circular imports
    from the_alchemiser.domain.trading.entities.order import Order


class OrderId(Identifier[Order]):
    """Typed identifier for orders."""

    pass
