"""Business Unit: portfolio assessment & management; Status: current.

PositionDelta value object for position change calculations.
"""
from __future__ import annotations


from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class PositionDelta:
    """Immutable value object representing the change needed for a position.

    This pure domain object contains all the information needed to understand
    how to adjust a position from its current quantity to its target quantity,
    including the specific action required and the exact quantity to trade.
    """

    symbol: str
    current_qty: Decimal
    target_qty: Decimal
    delta: Decimal
    action: Literal["no_change", "sell_excess", "buy_more"]
    quantity: Decimal
    message: str

    @property
    def needs_action(self) -> bool:
        """Whether this position delta requires any trading action."""
        return self.action != "no_change"

    @property
    def is_buy(self) -> bool:
        """Whether this delta represents a buy action."""
        return self.action == "buy_more"

    @property
    def is_sell(self) -> bool:
        """Whether this delta represents a sell action."""
        return self.action == "sell_excess"

    @property
    def quantity_abs(self) -> Decimal:
        """Get the absolute quantity to trade."""
        return abs(self.quantity)

    def __str__(self) -> str:
        """Human-readable representation of the position delta."""
        return self.message
