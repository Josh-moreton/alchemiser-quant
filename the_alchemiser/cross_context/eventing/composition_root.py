"""Business Unit: utilities | Status: current

Composition root for event-driven system initialization.

This module provides the main composition root for wiring together the EventBus,
publisher adapters, and event subscribers across all bounded contexts.
"""

from __future__ import annotations

import logging

from the_alchemiser.cross_context.eventing import InMemoryEventBus
from the_alchemiser.execution.application.use_cases.execute_plan import ExecutePlanUseCase
from the_alchemiser.execution.infrastructure.adapters.event_bus_execution_report_publisher_adapter import (
    EventBusExecutionReportPublisherAdapter,
)
from the_alchemiser.execution.interfaces.event_wiring import wire_execution_event_subscriptions
from the_alchemiser.portfolio.application.use_cases.generate_plan import GeneratePlanUseCase
from the_alchemiser.portfolio.application.use_cases.update_portfolio import UpdatePortfolioUseCase
from the_alchemiser.portfolio.infrastructure.adapters.event_bus_plan_publisher_adapter import (
    EventBusPlanPublisherAdapter,
)
from the_alchemiser.portfolio.interfaces.event_wiring import wire_portfolio_event_subscriptions
from the_alchemiser.strategy.infrastructure.adapters.event_bus_signal_publisher_adapter import (
    EventBusSignalPublisherAdapter,
)
from the_alchemiser.strategy.interfaces.event_wiring import wire_strategy_event_subscriptions

logger = logging.getLogger(__name__)


class EventSystemComposer:
    """Composes the event-driven system with EventBus and all contexts."""
    
    def __init__(self) -> None:
        """Initialize the composer."""
        self._event_bus = InMemoryEventBus()
        self._wired = False
    
    def get_event_bus(self) -> InMemoryEventBus:
        """Get the shared EventBus instance.
        
        Returns:
            The EventBus instance used by all contexts
        """
        return self._event_bus
    
    def create_signal_publisher(self) -> EventBusSignalPublisherAdapter:
        """Create EventBus-based signal publisher for Strategy context.
        
        Returns:
            Signal publisher that uses the shared EventBus
        """
        return EventBusSignalPublisherAdapter(self._event_bus)
    
    def create_plan_publisher(self) -> EventBusPlanPublisherAdapter:
        """Create EventBus-based plan publisher for Portfolio context.
        
        Returns:
            Plan publisher that uses the shared EventBus
        """
        return EventBusPlanPublisherAdapter(self._event_bus)
    
    def create_execution_report_publisher(self) -> EventBusExecutionReportPublisherAdapter:
        """Create EventBus-based execution report publisher for Execution context.
        
        Returns:
            Execution report publisher that uses the shared EventBus
        """
        return EventBusExecutionReportPublisherAdapter(self._event_bus)
    
    def wire_all_subscriptions(self) -> None:
        """Wire all event subscriptions across all bounded contexts.
        
        This method sets up the complete event flow:
        - Strategy signals -> Portfolio plan generation
        - Portfolio plans -> Execution plan execution
        - Execution reports -> Portfolio state updates
        """
        if self._wired:
            logger.warning("Event subscriptions already wired, skipping")
            return
        
        logger.info("Wiring all event subscriptions across bounded contexts...")
        
        # Create use cases that will handle events
        plan_publisher = self.create_plan_publisher()
        execution_report_publisher = self.create_execution_report_publisher()
        
        generate_plan_use_case = GeneratePlanUseCase(plan_publisher)
        update_portfolio_use_case = UpdatePortfolioUseCase()
        execute_plan_use_case = ExecutePlanUseCase(execution_report_publisher)
        
        # Wire each context's subscriptions
        wire_strategy_event_subscriptions(self._event_bus)
        wire_portfolio_event_subscriptions(
            self._event_bus,
            generate_plan_use_case,
            update_portfolio_use_case
        )
        wire_execution_event_subscriptions(
            self._event_bus,
            execute_plan_use_case
        )
        
        self._wired = True
        logger.info("All event subscriptions wired successfully")
    
    def reset_for_testing(self) -> None:
        """Reset the EventBus state for testing purposes.
        
        This clears idempotency tracking but keeps handler registrations.
        """
        self._event_bus.reset()
        logger.debug("EventBus reset for testing")


# Global composer instance for shared use
_global_composer: EventSystemComposer | None = None


def get_event_system_composer() -> EventSystemComposer:
    """Get the global EventSystemComposer instance.
    
    Returns:
        Singleton EventSystemComposer instance
    """
    global _global_composer
    if _global_composer is None:
        _global_composer = EventSystemComposer()
        _global_composer.wire_all_subscriptions()
    return _global_composer