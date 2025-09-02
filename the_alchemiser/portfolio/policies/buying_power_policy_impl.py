"""Business Unit: utilities; Status: current.

Buying Power Policy Implementation

Concrete implementation of BuyingPowerPolicy that handles buying power validation.
Extracts logic from PositionManager and ensures BuyingPowerError is raised properly.
Now uses pure domain objects and typed protocols.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from the_alchemiser.shared.types.policy_result import (
    PolicyResult,
    PolicyWarning,
    create_approved_result,
    create_rejected_result,
)
from the_alchemiser.portfolio.policies.protocols import DataProviderProtocol, TradingClientProtocol
from the_alchemiser.execution.orders.order_request import OrderRequest
from the_alchemiser.shared.utils.logging_utils import log_with_context
from the_alchemiser.shared.utils.exceptions import BuyingPowerError, DataProviderError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BuyingPowerPolicyImpl:
    """Concrete implementation of buying power policy.

    Handles validation of orders against available buying power and raises
    BuyingPowerError for insufficient funds (no string parsing heuristics).
    Uses typed protocols for external dependencies.
    """

    def __init__(
        self, trading_client: TradingClientProtocol, data_provider: DataProviderProtocol
    ) -> None:
        """Initialize the buying power policy.

        Args:
            trading_client: Trading client for account data
            data_provider: Data provider for price information

        """
        self.trading_client = trading_client
        self.data_provider = data_provider
        self._policy_name = "BuyingPowerPolicy"

    def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
        """Validate order against available buying power.

        For buy orders, checks if order value is within buying power limits.
        Raises BuyingPowerError for insufficient funds.

        Args:
            order_request: The domain order request to validate

        Returns:
            PolicyResult with buying power validation results

        Raises:
            BuyingPowerError: If insufficient buying power for the order

        """
        log_with_context(
            logger,
            logging.INFO,
            f"Validating buying power for {order_request.symbol.value}",
            policy=self.policy_name,
            symbol=order_request.symbol.value,
            side=order_request.side.value,
            quantity=str(order_request.quantity.value),
        )

        warnings: list[PolicyWarning] = []

        # Only validate buying power for buy orders
        if order_request.side.value.lower() == "buy":
            try:
                # Get limit price if available
                limit_price = None
                if order_request.limit_price:
                    limit_price = float(order_request.limit_price.amount)

                # Validate buying power - this will raise BuyingPowerError if insufficient
                self.validate_buying_power(
                    order_request.symbol.value, float(order_request.quantity.value), limit_price
                )

                log_with_context(
                    logger,
                    logging.INFO,
                    "Buying power validation passed",
                    policy=self.policy_name,
                    action="allow",
                    symbol=order_request.symbol.value,
                    quantity=str(order_request.quantity.value),
                )

            except BuyingPowerError as e:
                # Log the buying power rejection with structured data
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Buy order rejected due to insufficient buying power",
                    policy=self.policy_name,
                    action="reject",
                    symbol=order_request.symbol.value,
                    quantity=str(order_request.quantity.value),
                    required_amount=str(e.required_amount) if e.required_amount else "unknown",
                    available_amount=str(e.available_amount) if e.available_amount else "unknown",
                    shortfall=str(e.shortfall) if e.shortfall else "unknown",
                )

                return create_rejected_result(
                    order_request=order_request,
                    rejection_reason=str(e),
                )

            except Exception as e:
                # For unexpected errors during buying power validation, log and continue
                # This matches the original behavior of returning warnings instead of failing
                warning_msg = (
                    f"Unable to validate buying power for {order_request.symbol.value}: {e}"
                )

                warning = PolicyWarning(
                    policy_name=self.policy_name,
                    action="allow",
                    message=warning_msg,
                    original_value=str(order_request.quantity.value),
                    adjusted_value=str(order_request.quantity.value),
                    risk_level="medium",
                )
                warnings.append(warning)

                log_with_context(
                    logger,
                    logging.WARNING,
                    "Buying power validation failed but allowing order to proceed",
                    policy=self.policy_name,
                    action="allow",
                    symbol=order_request.symbol.value,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        # Approve the order (sell orders or buy orders that passed validation)
        log_with_context(
            logger,
            logging.INFO,
            "Buying power policy approved order",
            policy=self.policy_name,
            action="allow",
            symbol=order_request.symbol.value,
            side=order_request.side.value,
        )

        result = create_approved_result(order_request=order_request)

        # Add warnings if any
        if warnings:
            result = result.with_warnings(tuple(warnings))

        return result

    def get_available_buying_power(self) -> float:
        """Get current available buying power.

        Returns:
            Available buying power amount

        """
        try:
            account = self.trading_client.get_account()
            return float(getattr(account, "buying_power", 0) or 0)
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to get buying power: {e}",
                policy=self.policy_name,
                error=str(e),
            )
            raise BuyingPowerError(
                f"Unable to retrieve buying power: {e}",
                required_amount=None,
                available_amount=None,
            ) from e

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
        try:
            current_price = self.data_provider.get_current_price(symbol)
            if current_price is None or current_price <= 0:
                raise DataProviderError(f"Invalid current price for {symbol}: {current_price}")

            return float(current_price) * quantity

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to estimate order value for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                quantity=str(quantity),
                error=str(e),
            )
            raise DataProviderError(f"Unable to estimate order value for {symbol}: {e}") from e

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
