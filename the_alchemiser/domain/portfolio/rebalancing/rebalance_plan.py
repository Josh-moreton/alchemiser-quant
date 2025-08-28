"""Business Unit: portfolio assessment & management; Status: current.

RebalancePlan value object for portfolio rebalancing calculations.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class RebalancePlan:
    """Immutable value object representing a portfolio rebalancing plan for a single symbol.

    This pure domain object contains all the information needed to execute
    a rebalancing trade for a specific symbol, including current state,
    target state, and calculated trade requirements.
    """

    symbol: str
    current_weight: Decimal
    target_weight: Decimal
    weight_diff: Decimal
    target_value: Decimal
    current_value: Decimal
    trade_amount: Decimal
    needs_rebalance: bool

    @property
    def trade_direction(self) -> Literal["BUY", "SELL", "HOLD"]:
        """Determine the trade direction based on the rebalancing requirements."""
        if not self.needs_rebalance:
            return "HOLD"
        return "BUY" if self.trade_amount > 0 else "SELL"

    @property
    def trade_amount_abs(self) -> Decimal:
        """Get the absolute value of the trade amount."""
        return abs(self.trade_amount)

    @property
    def weight_change_bps(self) -> int:
        """Get the weight change in basis points (1/100th of a percent)."""
        return int(self.weight_diff * Decimal("10000"))

    def __str__(self) -> str:
        """Human-readable representation of the rebalance plan."""
        direction = self.trade_direction
        if direction == "HOLD":
            return f"{self.symbol}: HOLD (within threshold)"

        return (
            f"{self.symbol}: {direction} ${self.trade_amount_abs:.2f} "
            f"({self.current_weight:.1%} → {self.target_weight:.1%})"
        )
