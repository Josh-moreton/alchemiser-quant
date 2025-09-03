"""Business Unit: portfolio | Status: current..

        Args:
            symbol: Stock symbol to sell
            requested_quantity: Requested sell quantity

        Returns:
            Tuple of (is_valid, adjusted_quantity, warning_message)

        """
        try:
            available = self.get_available_position(symbol)

            if available <= 0:
                return False, 0.0, f"No position to sell for {symbol}"

            # Smart quantity adjustment - sell only what's actually available
            if requested_quantity > available:
                warning_msg = (
                    f"Adjusting sell quantity for {symbol}: {requested_quantity} -> {available}"
                )
                return True, available, warning_msg

            return True, requested_quantity, None

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Error validating sell quantity for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                requested_quantity=str(requested_quantity),
                error=str(e),
            )
            raise PositionValidationError(
                f"Failed to validate sell quantity for {symbol}: {e}",
                symbol=symbol,
                requested_qty=requested_quantity,
            ) from e

    def should_use_liquidation_api(self, symbol: str, requested_quantity: float) -> bool:
        """Determine if liquidation API should be used instead of regular sell.

        Args:
            symbol: Stock symbol
            requested_quantity: Requested sell quantity

        Returns:
            True if liquidation API should be used

        """
        try:
            available = self.get_available_position(symbol)

            if available <= 0:
                return False

            # Use liquidation API for selling 99%+ of position
            return requested_quantity >= available * 0.99

        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Error checking liquidation API requirement for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                error=str(e),
            )
            return False

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name
