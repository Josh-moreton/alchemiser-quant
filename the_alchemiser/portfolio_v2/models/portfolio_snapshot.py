"""Business Unit: portfolio | Status: current

Portfolio state management and rebalancing logic.

Portfolio snapshot models for immutable state representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Immutable snapshot of portfolio state.

    Contains current positions, prices, and cash for rebalancing calculations.
    All monetary values use Decimal for precision.
    """

    positions: dict[str, Decimal]  # symbol -> quantity (shares)
    prices: dict[str, Decimal]  # symbol -> current price per share
    cash: Decimal  # available cash balance
    total_value: Decimal  # total portfolio value (positions + cash)

    def __post_init__(self) -> None:
        """Validate snapshot consistency."""
        # Validate all positions have prices
        missing_prices = set(self.positions.keys()) - set(self.prices.keys())
        if missing_prices:
            raise ValueError(f"Missing prices for positions: {sorted(missing_prices)}")

        # Validate all values are non-negative
        if self.cash < 0:
            raise ValueError(f"Cash cannot be negative: {self.cash}")

        if self.total_value < 0:
            raise ValueError(f"Total value cannot be negative: {self.total_value}")

        for symbol, quantity in self.positions.items():
            if quantity < 0:
                raise ValueError(f"Position quantity cannot be negative for {symbol}: {quantity}")

        for symbol, price in self.prices.items():
            if price <= 0:
                raise ValueError(f"Price must be positive for {symbol}: {price}")

    def get_position_value(self, symbol: str) -> Decimal:
        """Get the market value of a position.

        Args:
            symbol: Trading symbol

        Returns:
            Market value (quantity * price)

        Raises:
            KeyError: If symbol not found in positions or prices

        """
        if symbol not in self.positions:
            raise KeyError(f"Symbol {symbol} not found in positions")
        if symbol not in self.prices:
            raise KeyError(f"Symbol {symbol} not found in prices")

        return self.positions[symbol] * self.prices[symbol]

    def get_all_position_values(self) -> dict[str, Decimal]:
        """Get market values for all positions.

        Returns:
            Dictionary mapping symbol to market value

        """
        return {symbol: self.get_position_value(symbol) for symbol in self.positions.keys()}

    def get_total_position_value(self) -> Decimal:
        """Get total market value of all positions.

        Returns:
            Sum of all position market values

        """
        values = list(self.get_all_position_values().values())
        if not values:
            return Decimal("0")
        total = Decimal("0")
        for value in values:
            total += value
        return total

    def validate_total_value(self, tolerance: Decimal = Decimal("0.01")) -> bool:
        """Validate that total_value equals positions + cash within tolerance.

        Args:
            tolerance: Maximum allowed difference

        Returns:
            True if values match within tolerance

        """
        calculated_total = self.get_total_position_value() + self.cash
        diff = abs(self.total_value - calculated_total)
        return diff <= tolerance
