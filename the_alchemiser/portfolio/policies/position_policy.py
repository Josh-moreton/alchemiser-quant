"""Business Unit: portfolio | Status: current..

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
