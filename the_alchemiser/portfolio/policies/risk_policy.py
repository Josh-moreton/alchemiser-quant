"""Business Unit: portfolio | Status: current..

        Args:
            symbol: Stock symbol
            additional_quantity: Additional quantity being added

        Returns:
            Tuple of (is_acceptable, warning_message)

        """
        ...

    def validate_order_size(
        self, symbol: str, quantity: float, portfolio_value: float
    ) -> tuple[bool, str | None]:
        """Validate order size against portfolio limits.

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            portfolio_value: Current portfolio value

        Returns:
            Tuple of (is_acceptable, warning_message)

        """
        ...

    @property
    def max_risk_score(self) -> Decimal:
        """Get the maximum acceptable risk score."""
        ...

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        ...
