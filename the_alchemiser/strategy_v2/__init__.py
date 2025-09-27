#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy_v2 module for signal generation and indicator calculation.

This module provides a clean, boundary-enforcing strategy system that:
- Consumes market data via shared Alpaca capabilities
- Outputs pure strategy signal DTOs (StrategyAllocation)
- Maintains strict separation from portfolio and execution concerns
- Communicates exclusively via events in the event-driven architecture

Public API (Event-Driven):
- register_strategy_handlers: Event handler registration for orchestration

Legacy API (Being Phased Out):
- SingleStrategyOrchestrator: Direct access orchestrator (for migration only)
- get_strategy: Registry access for strategy engines (internal use only)
- StrategyContext: Input context for strategy execution (internal use only)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

# Event-driven public API
def register_strategy_handlers(container: ApplicationContainer) -> None:
    """Register strategy event handlers with the orchestration system.
    
    This is the primary integration point for the strategy module in
    the event-driven architecture.
    
    Args:
        container: Application container for dependency injection
    """
    from .handlers import SignalGenerationHandler
    
    # Get event bus from container
    event_bus = container.services.event_bus()
    
    # Initialize and register handlers
    signal_handler = SignalGenerationHandler(container)
    
    # Register handlers for their respective events using event type strings
    event_bus.subscribe("StartupEvent", signal_handler)
    event_bus.subscribe("WorkflowStarted", signal_handler)


# Legacy imports for migration compatibility - these will be removed
from .core.orchestrator import SingleStrategyOrchestrator
from .core.registry import get_strategy, list_strategies, register_strategy
from .models.context import StrategyContext

# Public API exports (transitioning to event-driven only)
__all__ = [
    "register_strategy_handlers",  # Primary event-driven API
    # Legacy exports (being phased out)
    "SingleStrategyOrchestrator",
    "StrategyContext", 
    "get_strategy",
    "list_strategies",
    "register_strategy",
]

# Version for compatibility tracking
__version__ = "2.0.0"
