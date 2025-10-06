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
    # TYPE_CHECKING guards prevent circular imports while preserving type hints
    from the_alchemiser.shared.config.container import ApplicationContainer


# Event-driven public API
def register_strategy_handlers(container: ApplicationContainer) -> None:
    """Register strategy event handlers with the orchestration system.

    This is the primary integration point for the strategy module in
    the event-driven architecture.

    Args:
        container: Application container for dependency injection

    Raises:
        ConfigurationError: If container is missing required services or attributes
        Exception: If handler initialization or event subscription fails

    Example:
        >>> from the_alchemiser.shared.config.container import ApplicationContainer
        >>> container = ApplicationContainer.create_for_environment("development")
        >>> register_strategy_handlers(container)

    """
    from the_alchemiser.shared.errors import ConfigurationError
    from the_alchemiser.shared.logging import get_logger

    from .handlers import SignalGenerationHandler

    logger = get_logger(__name__)

    try:
        # Validate container has required services attribute
        if not hasattr(container, "services"):
            raise ConfigurationError(
                "Container missing required 'services' attribute",
                field="container.services",
                value=str(type(container)),
            )

        # Get event bus from container
        logger.info(
            "Registering strategy event handlers",
            extra={"module": "strategy_v2", "component": "register_strategy_handlers"},
        )
        event_bus = container.services.event_bus()

        # Initialize and register handlers
        signal_handler = SignalGenerationHandler(container)
        logger.debug(
            "Created SignalGenerationHandler instance",
            extra={"module": "strategy_v2", "handler_type": "SignalGenerationHandler"},
        )

        # Register handlers for their respective events using event type strings
        event_bus.subscribe("StartupEvent", signal_handler)
        logger.info(
            "Subscribed handler to StartupEvent",
            extra={
                "module": "strategy_v2",
                "event_type": "StartupEvent",
                "handler_type": "SignalGenerationHandler",
            },
        )

        event_bus.subscribe("WorkflowStarted", signal_handler)
        logger.info(
            "Subscribed handler to WorkflowStarted",
            extra={
                "module": "strategy_v2",
                "event_type": "WorkflowStarted",
                "handler_type": "SignalGenerationHandler",
            },
        )

        logger.info(
            "Strategy event handlers registered successfully",
            extra={
                "module": "strategy_v2",
                "events_registered": ["StartupEvent", "WorkflowStarted"],
            },
        )

    except ConfigurationError:
        # Re-raise configuration errors as-is
        raise
    except Exception as e:
        # Log and re-raise unexpected errors with context
        logger.error(
            f"Failed to register strategy handlers: {e}",
            extra={
                "module": "strategy_v2",
                "error_type": type(e).__name__,
                "component": "register_strategy_handlers",
            },
            exc_info=True,
        )
        raise


def __getattr__(name: str) -> object:
    if name == "SingleStrategyOrchestrator":
        from .core.orchestrator import (
            SingleStrategyOrchestrator as _SingleStrategyOrchestrator,
        )

        return _SingleStrategyOrchestrator
    if name in {"get_strategy", "list_strategies", "register_strategy"}:
        from .core import registry as _registry

        return getattr(_registry, name)
    if name == "StrategyContext":
        from .models.context import StrategyContext as _StrategyContext

        return _StrategyContext

    # Provide helpful error message with available attributes
    available = ", ".join(sorted(__all__))
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}. "
        f"Available attributes: {available}"
    )


# Public API exports (transitioning to event-driven only)
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
