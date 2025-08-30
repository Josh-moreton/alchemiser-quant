"""Business Unit: order execution/placement | Status: current

Event wiring for Execution context event subscriptions.

This module registers event handlers with the EventBus to enable the Execution context
to receive and process events from other bounded contexts.
"""

from __future__ import annotations

import logging

from the_alchemiser.cross_context.eventing.event_bus import EventBus
from the_alchemiser.execution.application.use_cases.execute_plan import ExecutePlanUseCase
from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import RebalancePlanContractV1

logger = logging.getLogger(__name__)


def wire_execution_event_subscriptions(
    event_bus: EventBus,
    execute_plan_use_case: ExecutePlanUseCase,
) -> None:
    """Wire Execution context event subscriptions.
    
    Registers event handlers with the EventBus to enable Execution context to:
    - Receive RebalancePlanContractV1 events from Portfolio context
    
    Args:
        event_bus: EventBus instance for subscription
        execute_plan_use_case: Use case for executing rebalance plans
    """
    logger.info("Wiring Execution context event subscriptions...")
    
    # Subscribe to rebalance plans from Portfolio context
    event_bus.subscribe(
        RebalancePlanContractV1,
        execute_plan_use_case.handle_plan
    )
    logger.debug("Registered handler for RebalancePlanContractV1 events")
    
    logger.info("Execution context event subscriptions wired successfully")