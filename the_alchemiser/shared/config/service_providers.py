"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.
"""

from __future__ import annotations

from typing import Any, Protocol

from dependency_injector import containers, providers

from the_alchemiser.shared.events.bus import EventBus


class ExecutionManagerProtocol(Protocol):
    """Protocol for execution manager to avoid direct imports."""
    
    def execute_orders(self, orders: Any) -> Any:  # type: ignore[misc]
        """Execute orders - implementation in execution_v2 module."""
        ...

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

    # V2 execution manager
    execution_manager = providers.Factory(
        ExecutionManager,
        alpaca_manager=infrastructure.alpaca_manager,
        enable_smart_execution=providers.Factory(
            lambda exec_settings: exec_settings.enable_smart_execution,
            exec_settings=config.execution,
        ),
    )
    # These will be replaced with v2 equivalents as they are migrated
