"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.

This module defines the service layer container for the dependency injection system.
After v2 migration, most service providers have been moved to their respective modules:
- execution_v2: Order placement and execution services
- portfolio_v2: Position and portfolio management services
- strategy_v2: Market data and signal generation services

The EventBridgeBus is provided here as shared infrastructure that coordinates events
across modules using Amazon EventBridge for durable, distributed event routing.

Architecture:
- Only imports from shared.* (no business module imports)
- Receives infrastructure and config via DependenciesContainer
- EventBridgeBus is singleton for application-wide event coordination
- Events are routed via CloudFormation EventRules, not programmatic subscriptions

Usage:
    container = ServiceProviders()
    container.infrastructure.override(infrastructure_container)
    container.config.override(config_container)
    bus = container.event_bus()
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.shared.events.eventbridge_bus import EventBridgeBus

# Deprecated services migrated to v2 modules:
# - AccountService → the_alchemiser.shared.brokers.AlpacaManager
# - TradingServiceManager → the_alchemiser.execution_v2.core.ExecutionManager
# - OrderService → the_alchemiser.execution_v2.core (see ExecutionManager)
# - PositionService → the_alchemiser.portfolio_v2 (see StateReader)
# - MarketDataService → the_alchemiser.strategy_v2.adapters (see MarketDataAdapter)
# - KLMEngine → the_alchemiser.strategy_v2.engines (see strategy registry)
# See README.md "Module Boundaries" section for architecture details.


def create_event_bus() -> EventBridgeBus:
    """Create EventBridge bus for distributed event routing.

    Returns EventBridgeBus for durable, async, distributed event routing with:
    - Event persistence and replay
    - Automatic retries with exponential backoff
    - Dead-letter queue for failed events
    - CloudWatch observability

    Returns:
        EventBridgeBus instance

    """
    return EventBridgeBus()


class ServiceProviders(containers.DeclarativeContainer):
    """Providers for service layer components.

    This container provides:
    - event_bus: Singleton EventBridgeBus for distributed event-driven workflows
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
    # Uses EventBridgeBus for durable, distributed event routing
    event_bus = providers.Singleton(create_event_bus)
