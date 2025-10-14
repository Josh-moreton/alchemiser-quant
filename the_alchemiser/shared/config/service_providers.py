"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.

This module defines the service layer container for the dependency injection system.
After v2 migration, most service providers have been moved to their respective modules:
- execution_v2: Order placement and execution services
- portfolio_v2: Position and portfolio management services
- strategy_v2: Market data and signal generation services

The EventBus remains here as shared infrastructure that coordinates events across modules.

Architecture:
- Only imports from shared.* (no business module imports)
- Receives infrastructure and config via DependenciesContainer
- EventBus is singleton for application-wide event coordination
- Supports both in-memory EventBus and EventBridge-backed EventBridgeBus

Usage:
    container = ServiceProviders()
    container.infrastructure.override(infrastructure_container)
    container.config.override(config_container)
    bus = container.event_bus()
"""

from __future__ import annotations

import os

from dependency_injector import containers, providers

from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.eventbridge_bus import EventBridgeBus

# Deprecated services migrated to v2 modules:
# - AccountService → the_alchemiser.shared.brokers.AlpacaManager
# - TradingServiceManager → the_alchemiser.execution_v2.core.ExecutionManager
# - OrderService → the_alchemiser.execution_v2.core (see ExecutionManager)
# - PositionService → the_alchemiser.portfolio_v2 (see StateReader)
# - MarketDataService → the_alchemiser.strategy_v2.adapters (see MarketDataAdapter)
# - KLMEngine → the_alchemiser.strategy_v2.engines (see strategy registry)
# See README.md "Module Boundaries" section for architecture details.


def create_event_bus() -> EventBus | EventBridgeBus:
    """Create appropriate event bus based on environment.

    Returns EventBridgeBus if USE_EVENTBRIDGE=true environment variable is set,
    otherwise returns standard in-memory EventBus.

    Returns:
        EventBus or EventBridgeBus instance

    """
    use_eventbridge = os.environ.get("USE_EVENTBRIDGE", "false").lower() == "true"

    if use_eventbridge:
        return EventBridgeBus()
    return EventBus()


class ServiceProviders(containers.DeclarativeContainer):
    """Providers for service layer components.

    This container provides:
    - event_bus: Singleton EventBus for event-driven workflows
    - infrastructure: Injected infrastructure dependencies (AlpacaManager, etc.)
    - config: Injected configuration dependencies (settings, credentials, etc.)

    Business module providers (execution, strategy, portfolio) are registered
    via wiring functions in the ApplicationContainer.

    Example:
        services = ServiceProviders()
        services.infrastructure.override(infrastructure_container)
        services.config.override(config_container)
        bus = services.event_bus()

    """

    # Dependencies
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()

    # Event bus (singleton for the application)
    # Uses factory to support both in-memory and EventBridge implementations
    event_bus = providers.Singleton(create_event_bus)
