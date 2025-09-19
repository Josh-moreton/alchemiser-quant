"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig
from the_alchemiser.shared.events.bus import EventBus

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
        execution_config=providers.Factory(ExecutionConfig),
        enable_smart_execution=providers.Factory(
            lambda exec_settings: exec_settings.enable_smart_execution,
            exec_settings=config.execution,
        ),
        enable_trade_ledger=providers.Factory(
            lambda exec_settings: exec_settings.enable_trade_ledger,
            exec_settings=config.execution,
        ),
    )
    # These will be replaced with v2 equivalents as they are migrated
