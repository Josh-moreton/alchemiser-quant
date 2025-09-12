"""Business Unit: portfolio | Status: current

Portfolio state management and rebalancing logic.

Sizing policy models for trade amount calculations and rounding rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class SizingMode(Enum):
    """Sizing modes for trade calculations."""

    DOLLAR_AMOUNT = "dollar"  # Trade by dollar amount (fractional shares allowed)
    WHOLE_SHARES = "shares"  # Trade by whole shares only
    LOT_SIZE = "lot"  # Trade by lot sizes (e.g., 100 share lots)


@dataclass(frozen=True)
class SizingPolicy:
    """Policy for sizing trades and applying thresholds.

    Defines how to round trade amounts and apply minimum thresholds
    to avoid micro-trades and transaction costs.
    """

    min_trade_amount: Decimal = Decimal("10.00")  # Minimum dollar amount to trade
    sizing_mode: SizingMode = SizingMode.DOLLAR_AMOUNT
    lot_size: int = 100  # Shares per lot (for LOT_SIZE mode)
    rounding_precision: int = 2  # Decimal places for dollar amounts

    def __post_init__(self) -> None:
        """Validate sizing policy parameters."""
        if self.min_trade_amount < 0:
            raise ValueError(f"min_trade_amount cannot be negative: {self.min_trade_amount}")

        if self.lot_size <= 0:
            raise ValueError(f"lot_size must be positive: {self.lot_size}")

        if self.rounding_precision < 0:
            raise ValueError(f"rounding_precision cannot be negative: {self.rounding_precision}")

    def should_trade(self, trade_amount: Decimal) -> bool:
        """Determine if trade amount meets minimum threshold.

        Args:
            trade_amount: Dollar amount to trade (absolute value)

        Returns:
            True if trade amount meets minimum threshold

        """
        return abs(trade_amount) >= self.min_trade_amount

    def round_trade_amount(self, trade_amount: Decimal) -> Decimal:
        """Round trade amount according to policy.

        Args:
            trade_amount: Raw trade amount in dollars

        Returns:
            Rounded trade amount

        """
        if self.sizing_mode == SizingMode.DOLLAR_AMOUNT:
            # Round to specified decimal places
            return trade_amount.quantize(Decimal("0.1") ** self.rounding_precision)

        if self.sizing_mode == SizingMode.WHOLE_SHARES:
            # This would require price information, so just round dollars for now
            # TODO: Implement proper share-based sizing in calculator
            return trade_amount.quantize(Decimal("0.1") ** self.rounding_precision)

        if self.sizing_mode == SizingMode.LOT_SIZE:
            # This would require price information, so just round dollars for now
            # TODO: Implement proper lot-based sizing in calculator
            return trade_amount.quantize(Decimal("0.1") ** self.rounding_precision)

        raise ValueError(f"Unknown sizing mode: {self.sizing_mode}")

    def apply_sizing_rules(self, trade_amount: Decimal) -> tuple[Decimal, str]:
        """Apply sizing rules and return final amount with action.

        Args:
            trade_amount: Raw trade amount (positive=buy, negative=sell)

        Returns:
            Tuple of (final_trade_amount, action)
            action is one of: "BUY", "SELL", "HOLD"

        """
        # Round the trade amount
        rounded_amount = self.round_trade_amount(trade_amount)

        # Check if it meets minimum threshold
        if not self.should_trade(rounded_amount):
            return Decimal("0"), "HOLD"

        # Determine action based on sign
        if rounded_amount > 0:
            return rounded_amount, "BUY"
        if rounded_amount < 0:
            return rounded_amount, "SELL"
        return Decimal("0"), "HOLD"


# Default policy instance
DEFAULT_SIZING_POLICY = SizingPolicy(
    min_trade_amount=Decimal("25.00"),  # $25 minimum to avoid excessive transaction costs
    sizing_mode=SizingMode.DOLLAR_AMOUNT,
    rounding_precision=2,  # Round to cents
)
