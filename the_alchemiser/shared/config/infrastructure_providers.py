"""Business Unit: utilities; Status: current.

Infrastructure layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.shared.brokers import AlpacaManager

# Legacy strategy import commented out to break circular dependency
# from the_alchemiser.strategy.data.market_data_service import MarketDataService


class InfrastructureProviders(containers.DeclarativeContainer):
    """Providers for infrastructure layer components."""

    # Configuration
    config = providers.DependenciesContainer()

    # Repository implementations
    alpaca_manager = providers.Singleton(
        AlpacaManager,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading,
    )

    # Legacy market data service commented out to break circular dependency
    # market_data_service = providers.Singleton(
    #     MarketDataService,
    #     market_data_repo=alpaca_manager,
    # )
    # data_provider = market_data_service

    # Backward compatibility: provide same interface
    trading_repository = alpaca_manager
    market_data_repository = alpaca_manager
    account_repository = alpaca_manager
