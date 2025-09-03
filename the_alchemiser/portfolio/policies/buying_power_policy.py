"""Business Unit: portfolio | Status: current..

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
