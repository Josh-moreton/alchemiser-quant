"""Business Unit: utilities; Status: current.

Service layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.domain.strategies.typed_klm_ensemble_engine import TypedKLMStrategyEngine
from the_alchemiser.portfolio.infrastructure.adapters.account_service import AccountService
from the_alchemiser.strategy.infrastructure.market_data.market_data_service import MarketDataService
from the_alchemiser.execution.application.orders.order_service import OrderService
from the_alchemiser.portfolio.application.queries.position_service import PositionService
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


class ServiceProviders(containers.DeclarativeContainer):
    """Providers for service layer components."""

    # Dependencies
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()

    # Enhanced services (inject repositories)
    order_service = providers.Factory(OrderService, trading_repo=infrastructure.trading_repository)

    position_service = providers.Factory(
        PositionService, trading_repo=infrastructure.trading_repository
    )

    market_data_service = providers.Factory(
        MarketDataService, market_data_repo=infrastructure.market_data_repository
    )

    account_service = providers.Factory(
        AccountService, account_repository=infrastructure.account_repository
    )

    # Backward compatibility: provide TradingServiceManager
    trading_service_manager = providers.Factory(
        TradingServiceManager,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading,
    )

    # Typed strategy engines
    typed_klm_strategy_engine = providers.Factory(
        TypedKLMStrategyEngine,
        strategy_name="KLM_Ensemble",
    )
