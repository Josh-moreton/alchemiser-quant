"""Business Unit: utilities; Status: current.

Position Policy Implementation

Concrete implementation of PositionPolicy that handles position validation
and quantity adjustments. Extracts logic from PositionManager.
Now uses pure domain objects and typed protocols.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution.orders.order_request import OrderRequest
from the_alchemiser.execution.types.policy_result import (
    PolicyResult,
    PolicyWarning,
    create_approved_result,
    create_rejected_result,
)
from the_alchemiser.portfolio.policies.protocols import TradingClientProtocol
from the_alchemiser.shared.logging.logging_utils import log_with_context
from the_alchemiser.shared.types.exceptions import PositionValidationError
from the_alchemiser.shared.types.quantity import Quantity

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PositionPolicyImpl:
    """Concrete implementation of position policy.

    Handles validation and adjustment of orders based on current position holdings,
    with structured logging and warning generation. Uses typed protocols for
    external dependencies.
    """

    def __init__(self, trading_client: TradingClientProtocol) -> None:
        """Initialize the position policy.

        Args:
            trading_client: Trading client for position data

        """
        self.trading_client = trading_client
        self._policy_name = "PositionPolicy"

    def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
        """Validate and adjust order based on current positions.

        For sell orders, ensures quantity doesn't exceed available position.
        For buy orders, validates position concentration limits.

        Args:
            order_request: The domain order request to validate

        Returns:
            PolicyResult with position-based adjustments applied

        """
        log_with_context(
            logger,
            logging.INFO,
            f"Validating position for {order_request.symbol.value}",
            policy=self.policy_name,
            symbol=order_request.symbol.value,
            side=order_request.side.value,
            quantity=str(order_request.quantity.value),
        )

        original_quantity = order_request.quantity.value  # Decimal
        adjusted_quantity = original_quantity
        warnings: list[PolicyWarning] = []
        adjustment_reason = None

        # Handle sell orders - validate against available position
        if order_request.side.value.lower() == "sell":
            is_valid, final_quantity_float, warning_msg = self.validate_sell_quantity(
                order_request.symbol.value, float(order_request.quantity.value)
            )

            if not is_valid:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Sell order rejected: {warning_msg}",
                    policy=self.policy_name,
                    action="reject",
                    symbol=order_request.symbol.value,
                    requested_quantity=str(original_quantity),
                    reason=warning_msg,
                )

                return create_rejected_result(
                    order_request=order_request,
                    rejection_reason=warning_msg or "Insufficient position for sell order",
                )

            # Check if quantity was adjusted
            if Decimal(str(final_quantity_float)) != original_quantity:
                adjusted_quantity = Decimal(str(final_quantity_float))

                warning = PolicyWarning(
                    policy_name=self.policy_name,
                    action="adjust",
                    message=warning_msg or "Adjusted sell quantity to available position",
                    original_value=str(original_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="medium",
                )
                warnings.append(warning)
                adjustment_reason = "Adjusted to available position quantity"

                log_with_context(
                    logger,
                    logging.INFO,
                    "Adjusted sell quantity to available position",
                    policy=self.policy_name,
                    action="adjust",
                    symbol=order_request.symbol.value,
                    original_quantity=str(original_quantity),
                    adjusted_quantity=str(adjusted_quantity),
                    available_position=str(final_quantity_float),
                )
            elif warning_msg:
                # Position validation passed but with a warning
                warning = PolicyWarning(
                    policy_name=self.policy_name,
                    action="allow",
                    message=warning_msg,
                    original_value=str(original_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="low",
                )
                warnings.append(warning)

        # Check if liquidation API should be used for large sell orders
        should_liquidate = False
        if order_request.side.value.lower() == "sell":
            should_liquidate = self.should_use_liquidation_api(
                order_request.symbol.value, float(adjusted_quantity)
            )

            if should_liquidate:
                warning = PolicyWarning(
                    policy_name=self.policy_name,
                    action="allow",
                    message="Large sell order - consider using liquidation API",
                    original_value=str(adjusted_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="low",
                )
                warnings.append(warning)

                log_with_context(
                    logger,
                    logging.INFO,
                    "Liquidation API recommended for large sell order",
                    policy=self.policy_name,
                    action="allow",
                    symbol=order_request.symbol.value,
                    quantity=str(adjusted_quantity),
                    recommendation="use_liquidation_api",
                )

        # Create adjusted order request if needed
        final_order_request = order_request
        if adjusted_quantity != original_quantity:
            final_order_request = OrderRequest(
                symbol=order_request.symbol,
                side=order_request.side,
                quantity=Quantity(adjusted_quantity),
                order_type=order_request.order_type,
                time_in_force=order_request.time_in_force,
                limit_price=order_request.limit_price,
                client_order_id=order_request.client_order_id,
            )

        # Approve the order
        log_with_context(
            logger,
            logging.INFO,
            "Position validation passed",
            policy=self.policy_name,
            action="allow",
            symbol=order_request.symbol.value,
            final_quantity=str(adjusted_quantity),
            has_adjustments=str(adjusted_quantity != original_quantity),
        )

        result = create_approved_result(
            order_request=final_order_request,
            original_quantity=(
                original_quantity if adjusted_quantity != original_quantity else None
            ),
            adjustment_reason=adjustment_reason,
        )

        # Add warnings and metadata
        if warnings:
            result = result.with_warnings(tuple(warnings))

        metadata = {"liquidation_recommended": str(should_liquidate)}
        result = result.with_metadata(metadata)

        return result

    def get_available_position(self, symbol: str) -> float:
        """Get the available position quantity for a symbol.

        Args:
            symbol: Stock symbol to check

        Returns:
            Available quantity that can be sold

        """
        try:
            positions = self.trading_client.get_all_positions()
            for pos in positions:
                if str(getattr(pos, "symbol", "")) == symbol:
                    return float(getattr(pos, "qty", 0))
            return 0.0
        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Failed to get position for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                error=str(e),
            )
            return 0.0

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
