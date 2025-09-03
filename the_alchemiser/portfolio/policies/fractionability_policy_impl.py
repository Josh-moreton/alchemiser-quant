"""Business Unit: portfolio | Status: current..

        Args:
            symbol: Asset symbol
            quantity: Requested quantity (float for detector compatibility)
            price: Optional price context

        Returns:
            Tuple (whole_share_qty, was_adjusted)

        """
        return fractionability_detector.convert_to_whole_shares(symbol, quantity, price or 0.0)

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name
