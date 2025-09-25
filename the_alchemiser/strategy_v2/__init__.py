#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy_v2 module for signal generation and indicator calculation.

This module provides a clean, boundary-enforcing strategy system that:
- Consumes market data via shared Alpaca capabilities
- Outputs pure strategy signal DTOs (StrategyAllocation)
- Maintains strict separation from portfolio and execution concerns

Public API:
- SingleStrategyOrchestrator: Main entry point for running strategies
- get_strategy: Registry access for strategy engines
- StrategyContext: Input context for strategy execution
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.registry.handler_registry import EventHandlerRegistry
    from the_alchemiser.strategy_v2.handlers.signal_generation_handler import (
        SignalGenerationHandler,
    )

# Core imports
from .core.orchestrator import SingleStrategyOrchestrator
from .core.registry import get_strategy, list_strategies, register_strategy
from .models.context import StrategyContext

# Public API exports
__all__ = [
    "SingleStrategyOrchestrator",
    "StrategyContext",
    "get_strategy",
    "list_strategies",
    "register_strategy",
    "register_strategy_handlers",
]

# Version for compatibility tracking
__version__ = "2.0.0"


def register_strategy_handlers(
    container: ApplicationContainer, registry: EventHandlerRegistry
) -> None:
    """Register strategy event handlers with the handler registry.
    
    Args:
        container: Application DI container
        registry: Event handler registry

    """
    from .handlers.signal_generation_handler import SignalGenerationHandler
    
    def signal_handler_factory() -> SignalGenerationHandler:
        """Create SignalGenerationHandler."""
        return SignalGenerationHandler(container)
    
    # Register handlers for events this module can handle
    registry.register_handler(
        event_type="StartupEvent",
        handler_factory=signal_handler_factory,
        module_name="strategy_v2",
        priority=100,
        metadata={"description": "Generates strategy signals on startup"}
    )
    
    registry.register_handler(
        event_type="WorkflowStarted",
        handler_factory=signal_handler_factory,
        module_name="strategy_v2",
        priority=100,
        metadata={"description": "Generates strategy signals on workflow start"}
    )
