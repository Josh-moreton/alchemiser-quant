"""Business Unit: utilities; Status: current.

Infrastructure layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.strategy.infrastructure.market_data_service import MarketDataService
from the_alchemiser.infrastructure.repositories.alpaca_manager import AlpacaManager


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

    # Typed market data service (canonical path)
    market_data_service = providers.Singleton(
        MarketDataService,
        market_data_repo=alpaca_manager,
    )

    # Data provider for strategies: use the same typed service (exposes get_data for compat)
    data_provider = market_data_service

    # Backward compatibility: provide same interface
    trading_repository = alpaca_manager
    market_data_repository = alpaca_manager
    account_repository = alpaca_manager
