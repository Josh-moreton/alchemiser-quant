"""Business Unit: portfolio | Status: current..

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
