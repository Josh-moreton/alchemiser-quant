"""Business Unit: utilities; Status: current.

Policy Orchestrator

Central coordinator for all order validation policies. Runs policies in sequence
and aggregates their results into a final order decision. Now uses pure domain
objects internally and provides DTO mapping at boundaries.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from the_alchemiser.application.mapping.policy_mapping import (
    domain_result_to_dto,
    dto_to_domain_order_request,
)
from the_alchemiser.domain.policies.policy_result import PolicyResult, PolicyWarning
from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
from the_alchemiser.infrastructure.logging.logging_utils import log_with_context
from the_alchemiser.interfaces.schemas.orders import (
    AdjustedOrderRequestDTO,
    OrderRequestDTO,
)

if TYPE_CHECKING:
    from the_alchemiser.portfolio.application.buying_power_policy_impl import (
        BuyingPowerPolicyImpl,
    )
    from the_alchemiser.portfolio.application.fractionability_policy_impl import (
        FractionabilityPolicyImpl,
    )
    from the_alchemiser.portfolio.application.position_policy_impl import (
        PositionPolicyImpl,
    )
    from the_alchemiser.portfolio.application.risk_policy_impl import RiskPolicyImpl

logger = logging.getLogger(__name__)


class PolicyOrchestrator:
    """Central orchestrator for order validation policies.

    Coordinates all policy validations and aggregates results into a final
    order decision with comprehensive logging and structured warnings.
    Uses pure domain objects internally with DTO mapping at boundaries.
    """

    def __init__(
        self,
        fractionability_policy: FractionabilityPolicyImpl,
        position_policy: PositionPolicyImpl,
        buying_power_policy: BuyingPowerPolicyImpl,
        risk_policy: RiskPolicyImpl,
    ) -> None:
        """Initialize the policy orchestrator.

        Args:
            fractionability_policy: Policy for asset fractionability
            position_policy: Policy for position validation
            buying_power_policy: Policy for buying power validation
            risk_policy: Policy for risk assessment

        """
        self.fractionability_policy = fractionability_policy
        self.position_policy = position_policy
        self.buying_power_policy = buying_power_policy
        self.risk_policy = risk_policy
        self._orchestrator_name = "PolicyOrchestrator"

    def validate_and_adjust_order(self, order_request: OrderRequestDTO) -> AdjustedOrderRequestDTO:
        """Run all policies on an order request and return aggregated result.

        This method serves as the boundary between DTOs (interface layer) and
        domain objects. It converts DTOs to domain objects, runs domain validation,
        and converts back to DTOs for return.

        Policies are run in order:
        1. FractionabilityPolicy - adjusts quantities for asset types
        2. PositionPolicy - validates against current positions
        3. BuyingPowerPolicy - validates against available funds
        4. RiskPolicy - assesses overall risk

        Args:
            order_request: The original order request DTO to validate

        Returns:
            AdjustedOrderRequestDTO with final validation results

        """
        # Convert DTO to domain object
        domain_order_request = dto_to_domain_order_request(order_request)

        # Run domain validation
        domain_result = self._validate_and_adjust_domain(domain_order_request)

        # Convert back to DTO for boundary
        return domain_result_to_dto(domain_result)

    # New public domain-facing entrypoint to avoid unnecessary DTO round-trips
    def validate_and_adjust_domain(self, order_request: OrderRequest) -> PolicyResult:
        """Validate using pure domain objects (preferred internal pathway)."""
        return self._validate_and_adjust_domain(order_request)

    def _validate_and_adjust_domain(self, order_request: OrderRequest) -> PolicyResult:
        """Internal method that runs policy validation using pure domain objects.

        This method maintains immutability by creating new PolicyResult instances
        instead of mutating existing ones.

        Args:
            order_request: The domain order request to validate

        Returns:
            PolicyResult with final validation results

        """
        log_with_context(
            logger,
            logging.INFO,
            f"Starting policy validation for {order_request.symbol.value}",
            orchestrator=self._orchestrator_name,
            symbol=order_request.symbol.value,
            side=order_request.side.value,
            quantity=str(order_request.quantity.value),
            order_type=order_request.order_type.value,
        )

        # Track aggregated state immutably
        current_request = order_request
        all_warnings: list[PolicyWarning] = []
        all_metadata: dict[str, str] = {}

        # 1. Fractionability Policy
        try:
            fractionability_result = self.fractionability_policy.validate_and_adjust(
                current_request
            )

            if not fractionability_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Order rejected by fractionability policy",
                    orchestrator=self._orchestrator_name,
                    policy="FractionabilityPolicy",
                    symbol=order_request.symbol.value,
                    reason=fractionability_result.rejection_reason,
                )
                return fractionability_result

            # Update current request if adjustments were made
            current_request = fractionability_result.order_request

            # Collect warnings and metadata immutably
            all_warnings.extend(fractionability_result.warnings)
            if fractionability_result.policy_metadata:
                all_metadata.update(fractionability_result.policy_metadata)

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Fractionability policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="FractionabilityPolicy",
                symbol=order_request.symbol.value,
                error=str(e),
            )

            from the_alchemiser.domain.policies.policy_result import (
                create_rejected_result,
            )

            return create_rejected_result(
                order_request=order_request,
                rejection_reason=f"Fractionability policy error: {e}",
            )

        # 2. Position Policy
        try:
            position_result = self.position_policy.validate_and_adjust(current_request)

            if not position_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Order rejected by position policy",
                    orchestrator=self._orchestrator_name,
                    policy="PositionPolicy",
                    symbol=order_request.symbol.value,
                    reason=position_result.rejection_reason,
                )

                # Include previous warnings in the rejection (immutable)
                combined_warnings = tuple(all_warnings) + position_result.warnings
                return position_result.with_warnings(combined_warnings)

            # Update current request and collect state
            current_request = position_result.order_request
            all_warnings.extend(position_result.warnings)
            if position_result.policy_metadata:
                all_metadata.update(position_result.policy_metadata)

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Position policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="PositionPolicy",
                symbol=order_request.symbol.value,
                error=str(e),
            )

            from the_alchemiser.domain.policies.policy_result import (
                create_rejected_result,
            )

            result = create_rejected_result(
                order_request=current_request,
                rejection_reason=f"Position policy error: {e}",
            )
            return result.with_warnings(tuple(all_warnings))

        # 3. Buying Power Policy
        try:
            buying_power_result = self.buying_power_policy.validate_and_adjust(current_request)

            if not buying_power_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Order rejected by buying power policy",
                    orchestrator=self._orchestrator_name,
                    policy="BuyingPowerPolicy",
                    symbol=order_request.symbol.value,
                    reason=buying_power_result.rejection_reason,
                )

                # Include previous warnings (immutable)
                combined_warnings = tuple(all_warnings) + buying_power_result.warnings
                return buying_power_result.with_warnings(combined_warnings)

            # Collect state
            all_warnings.extend(buying_power_result.warnings)
            if buying_power_result.policy_metadata:
                all_metadata.update(buying_power_result.policy_metadata)

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Buying power policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="BuyingPowerPolicy",
                symbol=order_request.symbol.value,
                error=str(e),
            )

            from the_alchemiser.domain.policies.policy_result import (
                create_rejected_result,
            )

            result = create_rejected_result(
                order_request=current_request,
                rejection_reason=f"Buying power policy error: {e}",
            )
            return result.with_warnings(tuple(all_warnings))

        # 4. Risk Policy
        try:
            risk_result = self.risk_policy.validate_and_adjust(current_request)

            if not risk_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Order rejected by risk policy",
                    orchestrator=self._orchestrator_name,
                    policy="RiskPolicy",
                    symbol=order_request.symbol.value,
                    reason=risk_result.rejection_reason,
                )

                # Include previous warnings (immutable)
                combined_warnings = tuple(all_warnings) + risk_result.warnings
                return risk_result.with_warnings(combined_warnings)

            # Collect final state
            all_warnings.extend(risk_result.warnings)
            if risk_result.policy_metadata:
                all_metadata.update(risk_result.policy_metadata)

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Risk policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="RiskPolicy",
                symbol=order_request.symbol.value,
                error=str(e),
            )

            from the_alchemiser.domain.policies.policy_result import (
                create_rejected_result,
            )

            result = create_rejected_result(
                order_request=current_request,
                rejection_reason=f"Risk policy error: {e}",
            )
            return result.with_warnings(tuple(all_warnings))

        # All policies passed - create final approved result
        final_quantity = current_request.quantity.value
        has_adjustments = final_quantity != order_request.quantity.value

        log_with_context(
            logger,
            logging.INFO,
            "All policies approved order",
            orchestrator=self._orchestrator_name,
            symbol=order_request.symbol.value,
            final_quantity=str(final_quantity),
            original_quantity=str(order_request.quantity.value),
            has_adjustments=str(has_adjustments),
            total_warnings=str(len(all_warnings)),
        )

        from the_alchemiser.domain.policies.policy_result import create_approved_result

        result = create_approved_result(
            order_request=current_request,
            original_quantity=order_request.quantity.value if has_adjustments else None,
            adjustment_reason="Policy adjustments applied" if has_adjustments else None,
        )

        # Add accumulated warnings and metadata immutably
        if all_warnings:
            result = result.with_warnings(tuple(all_warnings))
        if all_metadata:
            result = result.with_metadata(all_metadata)

        return result

    @property
    def orchestrator_name(self) -> str:
        """Get the name of this orchestrator for logging."""
        return self._orchestrator_name
