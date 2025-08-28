"""Business Unit: utilities; Status: current.

Position Policy Interface

Handles validation and adjustment of order quantities based on current positions.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.interfaces.schemas.orders import AdjustedOrderRequestDTO, OrderRequestDTO


class PositionPolicy(Protocol):
    """Policy for validating and adjusting orders based on current position holdings.

    This policy ensures sell orders don't exceed available positions and can
    adjust quantities to match actual holdings.
    """

    def validate_and_adjust(self, order_request: OrderRequestDTO) -> AdjustedOrderRequestDTO:
        """Validate and adjust order based on current positions.

        For sell orders, ensures quantity doesn't exceed available position.
        For buy orders, may apply position concentration limits.

        Args:
            order_request: The original order request to validate

        Returns:
            AdjustedOrderRequestDTO with position-based adjustments applied

        """
        ...

    def get_available_position(self, symbol: str) -> float:
        """Get the available position quantity for a symbol.

        Args:
            symbol: Stock symbol to check

        Returns:
            Available quantity that can be sold

        """
        ...

    def validate_sell_quantity(
        self, symbol: str, requested_quantity: float
    ) -> tuple[bool, float, str | None]:
        """Validate and adjust sell quantity based on available position.

        Args:
            symbol: Stock symbol to sell
            requested_quantity: Requested sell quantity

        Returns:
            Tuple of (is_valid, adjusted_quantity, warning_message)

        """
        ...

    def should_use_liquidation_api(self, symbol: str, requested_quantity: float) -> bool:
        """Determine if liquidation API should be used instead of regular sell.

        Args:
            symbol: Stock symbol
            requested_quantity: Requested sell quantity

        Returns:
            True if liquidation API should be used

        """
        ...

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        ...
