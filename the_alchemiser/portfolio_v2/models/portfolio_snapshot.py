"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio snapshot models for immutable state representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.utils.data_conversion import (
    convert_decimal_dict_to_strings,
    convert_string_dict_to_decimals,
)
from the_alchemiser.shared.utils.validation_utils import (
    validate_non_negative_decimal,
    validate_positions_have_prices,
    validate_price_positive,
    validate_quantity_non_negative,
)


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Represent an immutable snapshot of portfolio state.

    Contains current positions, prices, and cash for rebalancing calculations.
    All monetary values use Decimal for precision.
    """

    positions: dict[str, Decimal]  # symbol -> quantity (shares)
    prices: dict[str, Decimal]  # symbol -> current price per share
    cash: Decimal  # available cash balance
    total_value: Decimal  # total portfolio value (positions + cash)

    def __post_init__(self) -> None:
        """Validate snapshot consistency using extracted validation utilities."""
        # Validate all positions have prices
        validate_positions_have_prices(self.positions, self.prices)

        # Validate all monetary values are non-negative
        validate_non_negative_decimal(self.cash, "Cash")
        validate_non_negative_decimal(self.total_value, "Total value")

        # Validate all position quantities are non-negative
        for symbol, quantity in self.positions.items():
            validate_quantity_non_negative(quantity, symbol)

        # Validate all prices are positive
        for symbol, price in self.prices.items():
            validate_price_positive(price, f"Price for {symbol}")

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
        return {symbol: self.get_position_value(symbol) for symbol in self.positions}

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

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary for serialization.

        Returns:
            Dictionary representation with string-serialized Decimals

        """
        return {
            "positions": convert_decimal_dict_to_strings(self.positions),
            "prices": convert_decimal_dict_to_strings(self.prices),
            "cash": str(self.cash),
            "total_value": str(self.total_value),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PortfolioSnapshot:
        """Create snapshot from dictionary.

        Args:
            data: Dictionary containing snapshot data

        Returns:
            PortfolioSnapshot instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Create a copy to avoid modifying the original
        data = data.copy()

        # Convert string dictionaries to Decimal dictionaries
        if "positions" in data and isinstance(data["positions"], dict):
            data["positions"] = convert_string_dict_to_decimals(data["positions"])

        if "prices" in data and isinstance(data["prices"], dict):
            data["prices"] = convert_string_dict_to_decimals(data["prices"])

        # Convert cash and total_value from strings to Decimals
        if "cash" in data and isinstance(data["cash"], str):
            try:
                data["cash"] = Decimal(data["cash"])
            except Exception as e:
                raise ValueError(f"Invalid cash value: {data['cash']}") from e

        if "total_value" in data and isinstance(data["total_value"], str):
            try:
                data["total_value"] = Decimal(data["total_value"])
            except Exception as e:
                raise ValueError(f"Invalid total_value: {data['total_value']}") from e

        return cls(**data)
