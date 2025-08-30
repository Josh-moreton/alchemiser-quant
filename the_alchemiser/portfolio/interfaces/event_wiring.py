"""Business Unit: portfolio assessment & management | Status: current

Event wiring for Portfolio context event subscriptions.

This module registers event handlers with the EventBus to enable the Portfolio context
to receive and process events from other bounded contexts.
"""

from __future__ import annotations

import logging

from the_alchemiser.cross_context.eventing.event_bus import EventBus
from the_alchemiser.execution.application.contracts.execution_report_contract_v1 import (
    ExecutionReportContractV1,
)
from the_alchemiser.portfolio.application.use_cases.generate_plan import GeneratePlanUseCase
from the_alchemiser.portfolio.application.use_cases.update_portfolio import UpdatePortfolioUseCase
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1

logger = logging.getLogger(__name__)


def wire_portfolio_event_subscriptions(
    event_bus: EventBus,
    generate_plan_use_case: GeneratePlanUseCase,
    update_portfolio_use_case: UpdatePortfolioUseCase,
) -> None:
    """Wire Portfolio context event subscriptions.
    
    Registers event handlers with the EventBus to enable Portfolio context to:
    - Receive SignalContractV1 events from Strategy context
    - Receive ExecutionReportContractV1 events from Execution context
    
    Args:
        event_bus: EventBus instance for subscription
        generate_plan_use_case: Use case for generating plans from signals
        update_portfolio_use_case: Use case for updating portfolio from execution reports

    """
    logger.info("Wiring Portfolio context event subscriptions...")
    
    # Subscribe to strategy signals to generate rebalance plans
    event_bus.subscribe(
        SignalContractV1,
        generate_plan_use_case.handle_signal
    )
    logger.debug("Registered handler for SignalContractV1 events")
    
    # Subscribe to execution reports to update portfolio state
    event_bus.subscribe(
        ExecutionReportContractV1,
        update_portfolio_use_case.handle_execution_report
    )
    logger.debug("Registered handler for ExecutionReportContractV1 events")
    
    logger.info("Portfolio context event subscriptions wired successfully")