"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
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
    )
    # These will be replaced with v2 equivalents as they are migrated

    # order_service = providers.Factory(OrderService, trading_repo=infrastructure.trading_repository)
    # position_service = providers.Factory(
    #     PositionService, trading_repo=infrastructure.trading_repository
    # )
    # market_data_service = providers.Factory(
    #     MarketDataService, market_data_repo=infrastructure.market_data_repository
    # )
    # account_service = providers.Factory(
    #     AccountService, account_repository=infrastructure.account_repository
    # )
    # trading_service_manager = providers.Factory(
    #     TradingServiceManager,
    #     api_key=config.alpaca_api_key,
    #     secret_key=config.alpaca_secret_key,
    #     paper=config.paper_trading,
    # )
    # klm_strategy_engine = providers.Factory(
    #     KLMEngine,
    #     market_data_port=infrastructure.market_data_service,
    #     strategy_name="KLM_Ensemble",
    # )
