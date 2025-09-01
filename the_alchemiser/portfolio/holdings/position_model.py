"""Business Unit: utilities; Status: current.

Position domain models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from the_alchemiser.domain.types import PositionInfo
from the_alchemiser.utils.num import floats_equal


@dataclass(frozen=True)
class PositionModel:
    """Immutable position model."""

    symbol: str
    qty: float
    side: Literal["long", "short"]
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float

    @classmethod
    def from_dict(cls, data: PositionInfo) -> PositionModel:
        """Create from PositionInfo TypedDict."""
        return cls(
            symbol=data["symbol"],
            qty=float(data["qty"]),
            side=data["side"],
            market_value=float(data["market_value"]),
            cost_basis=float(data["cost_basis"]),
            unrealized_pl=float(data["unrealized_pl"]),
            unrealized_plpc=float(data["unrealized_plpc"]),
            current_price=float(data["current_price"]),
        )

    def to_dict(self) -> PositionInfo:
        """Convert to PositionInfo TypedDict."""
        return {
            "symbol": self.symbol,
            "qty": self.qty,
            "side": self.side,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pl": self.unrealized_pl,
            "unrealized_plpc": self.unrealized_plpc,
            "current_price": self.current_price,
        }

    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.unrealized_pl > 0

    @property
    def percentage_return(self) -> float:
        """Get percentage return of the position."""
        return self.unrealized_plpc * 100

    @property
    def shares_count(self) -> int:
        """Get number of shares (rounded to int)."""
        return int(abs(self.qty))

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.side == "long"

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.side == "short"

    @property
    def average_cost(self) -> float:
        """Calculate average cost per share."""
        if floats_equal(self.qty, 0.0):
            return 0.0
        return abs(self.cost_basis / self.qty)
