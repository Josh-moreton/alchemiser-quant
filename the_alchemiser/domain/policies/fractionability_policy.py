"""Fractionability Policy Interface

Handles validation and adjustment of order quantities based on asset fractionability rules.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.interfaces.schemas.orders import AdjustedOrderRequestDTO, OrderRequestDTO


class FractionabilityPolicy(Protocol):
    """Policy for handling asset fractionability validation and quantity adjustments.

    This policy determines if an asset supports fractional shares and adjusts
    order quantities accordingly (e.g., rounding to whole shares for non-fractionable assets).
    """

    def validate_and_adjust(self, order_request: OrderRequestDTO) -> AdjustedOrderRequestDTO:
        """Validate and adjust order quantity based on fractionability rules.

        Args:
            order_request: The original order request to validate

        Returns:
            AdjustedOrderRequestDTO with fractionability adjustments applied

        """
        ...

    def is_fractionable(self, symbol: str) -> bool:
        """Check if a symbol supports fractional shares.

        Args:
            symbol: Stock symbol to check

        Returns:
            True if the symbol supports fractional shares

        """
        ...

    def convert_to_whole_shares(
        self, symbol: str, quantity: float, price: float | None = None
    ) -> tuple[float, bool]:
        """Convert fractional quantity to whole shares for non-fractionable assets.

        Args:
            symbol: Stock symbol
            quantity: Original quantity (may be fractional)
            price: Current price (for value-based adjustments)

        Returns:
            Tuple of (adjusted_quantity, was_adjusted)

        """
        ...

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        ...
