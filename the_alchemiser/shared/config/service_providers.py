"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

# Using execution_v2 instead of legacy execution
from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager

# Legacy imports removed to eliminate fallback dependencies
# from the_alchemiser.execution.brokers.account_service import AccountService
# from the_alchemiser.execution.core.trading_services_facade import (
#     TradingServicesFacade as TradingServiceManager,
# )
# from the_alchemiser.execution.orders.service import OrderService
# from the_alchemiser.portfolio.holdings.position_service import PositionService
# from the_alchemiser.strategy.data.market_data_service import MarketDataService
# from the_alchemiser.strategy.engines.klm.engine import KLMEngine


class ServiceProviders(containers.DeclarativeContainer):
    """Providers for service layer components."""

    # Dependencies
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()

    # V2 execution manager (replaces legacy TradingServiceManager)
    execution_manager = providers.Factory(
        ExecutionManager,
        alpaca_manager=infrastructure.alpaca_manager,
    )

    # Legacy services commented out to remove fallback dependencies
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
