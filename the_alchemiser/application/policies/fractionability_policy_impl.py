"""
Fractionability Policy Implementation

Concrete implementation of FractionabilityPolicy that handles asset fractionability
validation and quantity adjustments. Extracts logic from LimitOrderHandler.
"""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.domain.math.asset_info import fractionability_detector
from the_alchemiser.infrastructure.logging.logging_utils import log_with_context
from the_alchemiser.interfaces.schemas.orders import (
    AdjustedOrderRequestDTO,
    OrderRequestDTO,
    PolicyWarningDTO,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class FractionabilityPolicyImpl:
    """
    Concrete implementation of fractionability policy.

    Handles validation and adjustment of order quantities based on asset
    fractionability rules, with structured logging and warning generation.
    """

    def __init__(self) -> None:
        """Initialize the fractionability policy."""
        self.policy_name = "FractionabilityPolicy"

    def validate_and_adjust(
        self,
        order_request: OrderRequestDTO
    ) -> AdjustedOrderRequestDTO:
        """
        Validate and adjust order quantity based on fractionability rules.

        Args:
            order_request: The original order request to validate

        Returns:
            AdjustedOrderRequestDTO with fractionability adjustments applied
        """
        log_with_context(
            logger,
            logging.INFO,
            f"Validating fractionability for {order_request.symbol}",
            policy=self.policy_name,
            symbol=order_request.symbol,
            original_quantity=str(order_request.quantity),
        )

        original_quantity = order_request.quantity
        adjusted_quantity = original_quantity
        warnings: list[PolicyWarningDTO] = []
        adjustment_reason = None

        # Check if asset is fractionable
        is_fractionable = self.is_fractionable(order_request.symbol)

        if not is_fractionable:
            # Convert to whole shares for non-fractionable assets
            whole_quantity, was_adjusted = self.convert_to_whole_shares(
                order_request.symbol,
                float(original_quantity),
                float(order_request.limit_price) if order_request.limit_price else None
            )

            if was_adjusted:
                adjusted_quantity = Decimal(str(whole_quantity))

                if adjusted_quantity <= 0:
                    # Reject order if it rounds to zero
                    log_with_context(
                        logger,
                        logging.WARNING,
                        f"Order rejected: {order_request.symbol} quantity rounded to zero",
                        policy=self.policy_name,
                        action="reject",
                        symbol=order_request.symbol,
                        original_quantity=str(original_quantity),
                        adjusted_quantity="0",
                    )

                    return AdjustedOrderRequestDTO(
                        symbol=order_request.symbol,
                        side=order_request.side,
                        quantity=original_quantity,
                        order_type=order_request.order_type,
                        time_in_force=order_request.time_in_force,
                        limit_price=order_request.limit_price,
                        client_order_id=order_request.client_order_id,
                        is_approved=False,
                        original_quantity=original_quantity,
                        adjustment_reason="Non-fractionable asset quantity rounded to zero",
                        rejection_reason="Order quantity rounds to zero whole shares",
                        total_risk_score=Decimal("0"),
                    )

                # Add warning for adjustment
                warning = PolicyWarningDTO(
                    policy_name=self.policy_name,
                    action="adjust",
                    message=f"Rounded {order_request.symbol} to {adjusted_quantity} whole shares for non-fractionable asset",
                    original_value=str(original_quantity),
                    adjusted_value=str(adjusted_quantity),
                    risk_level="low",
                )
                warnings.append(warning)
                adjustment_reason = f"Rounded to {adjusted_quantity} whole shares for non-fractionable asset"

                log_with_context(
                    logger,
                    logging.INFO,
                    "Adjusted quantity for non-fractionable asset",
                    policy=self.policy_name,
                    action="adjust",
                    symbol=order_request.symbol,
                    original_quantity=str(original_quantity),
                    adjusted_quantity=str(adjusted_quantity),
                )
        else:
            # For fractionable assets, apply standard rounding
            rounded_quantity = float(
                Decimal(str(original_quantity)).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_DOWN
                )
            )

            if rounded_quantity != float(original_quantity):
                adjusted_quantity = Decimal(str(rounded_quantity))

                warning = PolicyWarningDTO(
                    policy_name=self.policy_name,
                    action="adjust",
                    message=f"Applied precision rounding to {order_request.symbol}",
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
                    symbol=order_request.symbol,
                    original_quantity=str(original_quantity),
                    adjusted_quantity=str(adjusted_quantity),
                )

        # Check final quantity is valid
        if adjusted_quantity <= 0:
            log_with_context(
                logger,
                logging.WARNING,
                "Order rejected: final quantity is zero or negative",
                policy=self.policy_name,
                action="reject",
                symbol=order_request.symbol,
                adjusted_quantity=str(adjusted_quantity),
            )

            return AdjustedOrderRequestDTO(
                symbol=order_request.symbol,
                side=order_request.side,
                quantity=original_quantity,
                order_type=order_request.order_type,
                time_in_force=order_request.time_in_force,
                limit_price=order_request.limit_price,
                client_order_id=order_request.client_order_id,
                is_approved=False,
                original_quantity=original_quantity,
                adjustment_reason=adjustment_reason,
                rejection_reason="Final quantity is zero or negative",
                warnings=warnings,
                total_risk_score=Decimal("0"),
            )

        # Approve the order
        log_with_context(
            logger,
            logging.INFO,
            "Fractionability validation passed",
            policy=self.policy_name,
            action="allow",
            symbol=order_request.symbol,
            final_quantity=str(adjusted_quantity),
            has_adjustments=str(adjusted_quantity != original_quantity),
        )

        return AdjustedOrderRequestDTO(
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=adjusted_quantity,
            order_type=order_request.order_type,
            time_in_force=order_request.time_in_force,
            limit_price=order_request.limit_price,
            client_order_id=order_request.client_order_id,
            is_approved=True,
            original_quantity=original_quantity if adjusted_quantity != original_quantity else None,
            adjustment_reason=adjustment_reason,
            warnings=warnings,
            policy_metadata={"is_fractionable": str(is_fractionable)},
            total_risk_score=Decimal("0"),
        )

    def is_fractionable(self, symbol: str) -> bool:
        """
        Check if a symbol supports fractional shares.

        Args:
            symbol: Stock symbol to check

        Returns:
            True if the symbol supports fractional shares
        """
        return fractionability_detector.is_fractionable(symbol)

    def convert_to_whole_shares(
        self,
        symbol: str,
        quantity: float,
        price: float | None = None
    ) -> tuple[float, bool]:
        """
        Convert fractional quantity to whole shares for non-fractionable assets.

        Args:
            symbol: Stock symbol
            quantity: Original quantity (may be fractional)
            price: Current price (for value-based adjustments)

        Returns:
            Tuple of (adjusted_quantity, was_adjusted)
        """
        return fractionability_detector.convert_to_whole_shares(symbol, quantity, price or 0.0)

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name

    @policy_name.setter
    def policy_name(self, value: str) -> None:
        """Set the policy name."""
        self._policy_name = value
