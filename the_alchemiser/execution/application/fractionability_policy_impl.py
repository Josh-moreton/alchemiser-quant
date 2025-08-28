"""Business Unit: utilities; Status: current.

Fractionability policy implementation.

Concrete implementation handling asset fractionability validation and quantity
adjustments (extracted from legacy handlers) using pure domain objects.
"""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared_kernel.domain.asset_info import fractionability_detector
from the_alchemiser.execution.domain.policy_result import (
    PolicyResult,
    PolicyWarning,
    create_approved_result,
    create_rejected_result,
)
from the_alchemiser.execution.domain.value_objects.order_request import OrderRequest
from the_alchemiser.execution.domain.value_objects.quantity import Quantity
from the_alchemiser.shared_kernel.infrastructure.logging_utils import log_with_context

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class FractionabilityPolicyImpl:
    """Concrete implementation of fractionability policy.

    Handles validation and adjustment of order quantities based on asset
    fractionability rules, with structured logging and warning generation.
    Uses pure domain objects to maintain separation of concerns.
    """

    def __init__(self) -> None:
        """Initialize the fractionability policy."""
        self._policy_name = "FractionabilityPolicy"

    def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
        """Validate and adjust order quantity based on fractionability rules.

        Args:
            order_request: The domain order request to validate

        Returns:
            PolicyResult with fractionability adjustments applied

        """
        log_with_context(
            logger,
            logging.INFO,
            f"Validating fractionability for {order_request.symbol.value}",
            policy=self.policy_name,
            symbol=order_request.symbol.value,
            original_quantity=str(order_request.quantity.value),
        )

        original_quantity = order_request.quantity.value
        adjusted_quantity = original_quantity
        warnings: list[PolicyWarning] = []
        adjustment_reason = None

        # Determine if asset supports fractional shares
        is_fractionable = self.is_fractionable(order_request.symbol.value)
        if not is_fractionable:
            limit_price = (
                float(order_request.limit_price.amount)
                if order_request.limit_price is not None
                else None
            )
            whole_quantity, was_adjusted = self.convert_to_whole_shares(
                order_request.symbol.value, float(original_quantity), limit_price
            )
            if was_adjusted:
                adjusted_quantity = Decimal(str(whole_quantity))
                if adjusted_quantity <= 0:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        f"Order rejected: {order_request.symbol.value} quantity rounded to zero",
                        policy=self.policy_name,
                        action="reject",
                        symbol=order_request.symbol.value,
                        original_quantity=str(original_quantity),
                        adjusted_quantity="0",
                    )
                    return create_rejected_result(
                        order_request=order_request,
                        rejection_reason="Order quantity rounds to zero whole shares",
                    )
                warning = PolicyWarning(
                    policy_name=self.policy_name,
                    action="adjust",
                    message=(
                        f"Rounded {order_request.symbol.value} to {adjusted_quantity} whole shares "
                        "for non-fractionable asset"
                    ),
                    original_value=str(original_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="low",
                )
                warnings.append(warning)
                adjustment_reason = (
                    f"Rounded to {adjusted_quantity} whole shares for non-fractionable asset"
                )
                log_with_context(
                    logger,
                    logging.INFO,
                    "Adjusted quantity for non-fractionable asset",
                    policy=self.policy_name,
                    action="adjust",
                    symbol=order_request.symbol.value,
                    original_quantity=str(original_quantity),
                    adjusted_quantity=str(adjusted_quantity),
                )
        else:
            rounded_quantity = Decimal(str(original_quantity)).quantize(
                Decimal("0.000001"), rounding=ROUND_DOWN
            )
            if rounded_quantity != original_quantity:
                adjusted_quantity = rounded_quantity
                warning = PolicyWarning(
                    policy_name=self.policy_name,
                    action="adjust",
                    message=f"Applied precision rounding to {order_request.symbol.value}",
                    original_value=str(original_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="low",
                )
                warnings.append(warning)
                adjustment_reason = "Applied precision rounding"
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Applied precision rounding",
                    policy=self.policy_name,
                    action="adjust",
                    symbol=order_request.symbol.value,
                    original_quantity=str(original_quantity),
                    adjusted_quantity=str(adjusted_quantity),
                )

        if adjusted_quantity <= 0:
            log_with_context(
                logger,
                logging.WARNING,
                "Order rejected: final quantity is zero or negative",
                policy=self.policy_name,
                action="reject",
                symbol=order_request.symbol.value,
                adjusted_quantity=str(adjusted_quantity),
            )
            return create_rejected_result(
                order_request=order_request,
                rejection_reason="Final quantity is zero or negative",
            )

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

        log_with_context(
            logger,
            logging.INFO,
            "Fractionability validation passed",
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
        if warnings:
            result = result.with_warnings(tuple(warnings))
        metadata = {"fractionability.is_fractionable": str(is_fractionable)}
        return result.with_metadata(metadata)

    def is_fractionable(self, symbol: str) -> bool:
        """Return True if the symbol supports fractional shares."""
        return fractionability_detector.is_fractionable(symbol)

    def convert_to_whole_shares(
        self, symbol: str, quantity: float, price: float | None = None
    ) -> tuple[float, bool]:
        """Convert fractional quantity to whole shares for non-fractionable assets.

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
