"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.persistence.factory import create_persistence_handler
from the_alchemiser.shared.registry.handler_registry import EventHandlerRegistry

# - AccountService → Use AlpacaManager directly
# - TradingServiceManager → Use ExecutionManager from execution_v2
# - OrderService → Use execution_v2.core components
# - PositionService → Use portfolio_v2 components
# - MarketDataService → Use strategy_v2.data components
# - KLMEngine → Use strategy_v2.engines components


class ServiceProviders(containers.DeclarativeContainer):
    """Providers for service layer components."""

    # Dependencies
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()

    # Event bus (singleton for the application)
    event_bus = providers.Singleton(EventBus)

    # Event handler registry (singleton for the application)
    event_handler_registry = providers.Singleton(EventHandlerRegistry)

    # Persistence handler (shared across modules) - used for idempotency stores, etc.
    # Decides implementation (local vs S3) based on config.paper_trading
    persistence_handler = providers.Singleton(
        create_persistence_handler, paper_trading=config.paper_trading
    )

    # Execution providers will be injected from execution_v2 module
    # This maintains the layered architecture by preventing shared -> execution_v2 imports
    # These will be replaced with v2 equivalents as they are migrated
