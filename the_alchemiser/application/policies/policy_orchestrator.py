"""
Policy Orchestrator

Central coordinator for all order validation policies. Runs policies in sequence
and aggregates their results into a final order decision.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.interfaces.schemas.orders import (
    AdjustedOrderRequestDTO,
    OrderRequestDTO,
    PolicyWarningDTO,
)
from the_alchemiser.infrastructure.logging.logging_utils import log_with_context

if TYPE_CHECKING:
    from the_alchemiser.application.policies.buying_power_policy_impl import BuyingPowerPolicyImpl
    from the_alchemiser.application.policies.fractionability_policy_impl import FractionabilityPolicyImpl
    from the_alchemiser.application.policies.position_policy_impl import PositionPolicyImpl
    from the_alchemiser.application.policies.risk_policy_impl import RiskPolicyImpl

logger = logging.getLogger(__name__)


class PolicyOrchestrator:
    """
    Central orchestrator for order validation policies.
    
    Coordinates all policy validations and aggregates results into a final
    order decision with comprehensive logging and structured warnings.
    """
    
    def __init__(
        self,
        fractionability_policy: FractionabilityPolicyImpl,
        position_policy: PositionPolicyImpl,
        buying_power_policy: BuyingPowerPolicyImpl,
        risk_policy: RiskPolicyImpl,
    ) -> None:
        """
        Initialize the policy orchestrator.
        
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
    
    def validate_and_adjust_order(
        self, 
        order_request: OrderRequestDTO
    ) -> AdjustedOrderRequestDTO:
        """
        Run all policies on an order request and return aggregated result.
        
        Policies are run in order:
        1. FractionabilityPolicy - adjusts quantities for asset types
        2. PositionPolicy - validates against current positions  
        3. BuyingPowerPolicy - validates against available funds
        4. RiskPolicy - assesses overall risk
        
        Args:
            order_request: The original order request to validate
            
        Returns:
            AdjustedOrderRequestDTO with final validation results
        """
        log_with_context(
            logger,
            logging.INFO,
            f"Starting policy validation for {order_request.symbol}",
            orchestrator=self._orchestrator_name,
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=str(order_request.quantity),
            order_type=order_request.order_type,
        )
        
        # Track aggregated results
        all_warnings: list[PolicyWarningDTO] = []
        all_metadata: dict[str, str] = {}
        total_risk_score = Decimal("0")
        current_request = order_request
        
        # 1. Fractionability Policy
        try:
            fractionability_result = self.fractionability_policy.validate_and_adjust(current_request)
            
            if not fractionability_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Order rejected by fractionability policy",
                    orchestrator=self._orchestrator_name,
                    policy="FractionabilityPolicy",
                    symbol=order_request.symbol,
                    reason=fractionability_result.rejection_reason,
                )
                return fractionability_result
            
            # Update current request with adjustments
            if fractionability_result.quantity != current_request.quantity:
                current_request = OrderRequestDTO(
                    symbol=fractionability_result.symbol,
                    side=fractionability_result.side,
                    quantity=fractionability_result.quantity,
                    order_type=fractionability_result.order_type,
                    time_in_force=fractionability_result.time_in_force,
                    limit_price=fractionability_result.limit_price,
                    client_order_id=fractionability_result.client_order_id,
                )
            
            all_warnings.extend(fractionability_result.warnings)
            all_metadata.update(fractionability_result.policy_metadata)
            total_risk_score += fractionability_result.total_risk_score
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Fractionability policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="FractionabilityPolicy",
                symbol=order_request.symbol,
                error=str(e),
            )
            
            return AdjustedOrderRequestDTO(
                symbol=order_request.symbol,
                side=order_request.side,
                quantity=order_request.quantity,
                order_type=order_request.order_type,
                time_in_force=order_request.time_in_force,
                limit_price=order_request.limit_price,
                client_order_id=order_request.client_order_id,
                is_approved=False,
                rejection_reason=f"Fractionability policy error: {e}",
                total_risk_score=total_risk_score,
            )
        
        # 2. Position Policy
        try:
            position_result = self.position_policy.validate_and_adjust(current_request)
            
            if not position_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Order rejected by position policy",
                    orchestrator=self._orchestrator_name,
                    policy="PositionPolicy",
                    symbol=order_request.symbol,
                    reason=position_result.rejection_reason,
                )
                
                # Include previous warnings in the rejection
                position_result.warnings.extend(all_warnings)
                return position_result
            
            # Update current request with adjustments
            if position_result.quantity != current_request.quantity:
                current_request = OrderRequestDTO(
                    symbol=position_result.symbol,
                    side=position_result.side,
                    quantity=position_result.quantity,
                    order_type=position_result.order_type,
                    time_in_force=position_result.time_in_force,
                    limit_price=position_result.limit_price,
                    client_order_id=position_result.client_order_id,
                )
            
            all_warnings.extend(position_result.warnings)
            all_metadata.update(position_result.policy_metadata)
            total_risk_score += position_result.total_risk_score
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Position policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="PositionPolicy",
                symbol=order_request.symbol,
                error=str(e),
            )
            
            return AdjustedOrderRequestDTO(
                symbol=current_request.symbol,
                side=current_request.side,
                quantity=current_request.quantity,
                order_type=current_request.order_type,
                time_in_force=current_request.time_in_force,
                limit_price=current_request.limit_price,
                client_order_id=current_request.client_order_id,
                is_approved=False,
                rejection_reason=f"Position policy error: {e}",
                warnings=all_warnings,
                total_risk_score=total_risk_score,
            )
        
        # 3. Buying Power Policy
        try:
            buying_power_result = self.buying_power_policy.validate_and_adjust(current_request)
            
            if not buying_power_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Order rejected by buying power policy",
                    orchestrator=self._orchestrator_name,
                    policy="BuyingPowerPolicy",
                    symbol=order_request.symbol,
                    reason=buying_power_result.rejection_reason,
                )
                
                # Include previous warnings in the rejection
                buying_power_result.warnings.extend(all_warnings)
                return buying_power_result
            
            all_warnings.extend(buying_power_result.warnings)
            all_metadata.update(buying_power_result.policy_metadata)
            total_risk_score += buying_power_result.total_risk_score
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Buying power policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="BuyingPowerPolicy",
                symbol=order_request.symbol,
                error=str(e),
            )
            
            return AdjustedOrderRequestDTO(
                symbol=current_request.symbol,
                side=current_request.side,
                quantity=current_request.quantity,
                order_type=current_request.order_type,
                time_in_force=current_request.time_in_force,
                limit_price=current_request.limit_price,
                client_order_id=current_request.client_order_id,
                is_approved=False,
                rejection_reason=f"Buying power policy error: {e}",
                warnings=all_warnings,
                total_risk_score=total_risk_score,
            )
        
        # 4. Risk Policy
        try:
            risk_result = self.risk_policy.validate_and_adjust(current_request)
            
            if not risk_result.is_approved:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Order rejected by risk policy",
                    orchestrator=self._orchestrator_name,
                    policy="RiskPolicy",
                    symbol=order_request.symbol,
                    reason=risk_result.rejection_reason,
                )
                
                # Include previous warnings in the rejection
                risk_result.warnings.extend(all_warnings)
                return risk_result
            
            all_warnings.extend(risk_result.warnings)
            all_metadata.update(risk_result.policy_metadata)
            total_risk_score += risk_result.total_risk_score
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Risk policy failed: {e}",
                orchestrator=self._orchestrator_name,
                policy="RiskPolicy",
                symbol=order_request.symbol,
                error=str(e),
            )
            
            return AdjustedOrderRequestDTO(
                symbol=current_request.symbol,
                side=current_request.side,
                quantity=current_request.quantity,
                order_type=current_request.order_type,
                time_in_force=current_request.time_in_force,
                limit_price=current_request.limit_price,
                client_order_id=current_request.client_order_id,
                is_approved=False,
                rejection_reason=f"Risk policy error: {e}",
                warnings=all_warnings,
                total_risk_score=total_risk_score,
            )
        
        # All policies passed - create final approved result
        final_quantity = current_request.quantity
        has_adjustments = final_quantity != order_request.quantity
        
        log_with_context(
            logger,
            logging.INFO,
            f"All policies approved order",
            orchestrator=self._orchestrator_name,
            symbol=order_request.symbol,
            final_quantity=str(final_quantity),
            original_quantity=str(order_request.quantity),
            has_adjustments=str(has_adjustments),
            total_warnings=str(len(all_warnings)),
            total_risk_score=str(total_risk_score),
        )
        
        return AdjustedOrderRequestDTO(
            symbol=current_request.symbol,
            side=current_request.side,
            quantity=final_quantity,
            order_type=current_request.order_type,
            time_in_force=current_request.time_in_force,
            limit_price=current_request.limit_price,
            client_order_id=current_request.client_order_id,
            is_approved=True,
            original_quantity=order_request.quantity if has_adjustments else None,
            adjustment_reason="Policy adjustments applied" if has_adjustments else None,
            warnings=all_warnings,
            policy_metadata=all_metadata,
            total_risk_score=total_risk_score,
        )
    
    @property
    def orchestrator_name(self) -> str:
        """Get the name of this orchestrator for logging."""
        return self._orchestrator_name