"""Business Unit: portfolio assessment & management | Status: current

Use case for generating rebalance plans from strategy signals.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import uuid4

from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import (
    PlannedOrderV1,
    RebalancePlanContractV1,
)
from the_alchemiser.portfolio.application.ports import PlanPublisherPort
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1

logger = logging.getLogger(__name__)


class GeneratePlanUseCase:
    """Generates rebalance plans from strategy signals."""
    
    def __init__(self, plan_publisher: PlanPublisherPort) -> None:
        """Initialize the use case with required dependencies.
        
        Args:
            plan_publisher: Port for publishing generated plans
        """
        self._plan_publisher = plan_publisher
    
    def handle_signal(self, signal: SignalContractV1) -> None:
        """Handle incoming strategy signal and generate rebalance plan.
        
        Args:
            signal: Strategy signal to process
        """
        logger.info(
            "Processing signal for %s %s (correlation_id: %s)",
            signal.symbol,
            signal.action,
            signal.correlation_id
        )
        
        try:
            # TODO: Replace simplified plan generation with proper domain logic
            # FIXME: Move portfolio rebalancing logic to domain layer
            # This is a simplified example - real logic would involve:
            # - Current portfolio state analysis
            # - Risk calculations
            # - Position sizing algorithms
            # - Multi-asset rebalancing optimization
            
            # Create a simple planned order based on the signal
            planned_order = PlannedOrderV1(
                order_id=uuid4(),
                symbol=signal.symbol,
                side=signal.action,
                quantity=Decimal("100"),  # TODO: Replace hardcoded quantity with proper position sizing
                limit_price=None  # Market order for simplicity
            )
            
            # Create rebalance plan
            plan = RebalancePlanContractV1(
                correlation_id=signal.correlation_id,
                causation_id=signal.message_id,  # This plan was caused by the signal
                planned_orders=[planned_order]
            )
            
            # Publish the plan
            self._plan_publisher.publish(plan)
            
            logger.info(
                "Generated and published rebalance plan with %d orders (plan_id: %s, caused_by: %s)",
                len(plan.planned_orders),
                plan.plan_id,
                signal.message_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to generate plan from signal %s: %s",
                signal.message_id,
                e,
                exc_info=True
            )
            raise