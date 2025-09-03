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
        try:
            buying_power = self.get_available_buying_power()

            # Get price for order value calculation
            if estimated_price is None:
                current_price = self.data_provider.get_current_price(symbol)
                if current_price is None or current_price <= 0:
                    raise DataProviderError(f"Invalid current price for {symbol}: {current_price}")
                price_value = float(current_price)
            else:
                price_value = estimated_price

            order_value = quantity * price_value

            if order_value > buying_power:
                shortfall = order_value - buying_power
                raise BuyingPowerError(
                    f"Order value ${order_value:.2f} exceeds buying power ${buying_power:.2f} for {symbol}",
                    symbol=symbol,
                    required_amount=order_value,
                    available_amount=buying_power,
                    shortfall=shortfall,
                )

            return True

        except BuyingPowerError:
            # Re-raise BuyingPowerError as-is
            raise
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Error validating buying power for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                quantity=str(quantity),
                error=str(e),
                error_type=type(e).__name__,
            )
            # Convert any other errors to BuyingPowerError for consistency
            raise BuyingPowerError(
                f"Unable to validate buying power for {symbol}: {e}",
                symbol=symbol,
            ) from e

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name
