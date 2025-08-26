"""Buying Power Policy Interface

Handles validation of order values against available buying power.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.interfaces.schemas.orders import AdjustedOrderRequestDTO, OrderRequestDTO


class BuyingPowerPolicy(Protocol):
    """Policy for validating orders against available buying power.

    This policy ensures buy orders don't exceed available buying power and
    raises BuyingPowerError for insufficient funds (no string parsing heuristics).
    """

    def validate_and_adjust(self, order_request: OrderRequestDTO) -> AdjustedOrderRequestDTO:
        """Validate order against available buying power.

        For buy orders, checks if order value is within buying power limits.
        Raises BuyingPowerError for insufficient funds.

        Args:
            order_request: The original order request to validate

        Returns:
            AdjustedOrderRequestDTO with buying power validation results

        Raises:
            BuyingPowerError: If insufficient buying power for the order

        """
        ...

    def get_available_buying_power(self) -> float:
        """Get current available buying power.

        Returns:
            Available buying power amount

        """
        ...

    def estimate_order_value(
        self, symbol: str, quantity: float, order_type: str = "market"
    ) -> float:
        """Estimate the total value of an order.

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            order_type: Type of order ("market" or "limit")

        Returns:
            Estimated order value in dollars

        """
        ...

    def validate_buying_power(
        self, symbol: str, quantity: float, estimated_price: float | None = None
    ) -> bool:
        """Validate if sufficient buying power exists for an order.

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            estimated_price: Price estimate (if None, fetches current price)

        Returns:
            True if sufficient buying power exists

        Raises:
            BuyingPowerError: If insufficient buying power

        """
        ...

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        ...
