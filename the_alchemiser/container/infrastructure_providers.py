"""Infrastructure layer providers for dependency injection."""

from dependency_injector import containers, providers

from the_alchemiser.services.market_data.market_data_service import MarketDataService
from the_alchemiser.services.market_data.typed_data_provider_adapter import (
    TypedDataProviderAdapter,
)
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager


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

    # Data provider for strategies: typed adapter returning DataFrames (temporary)
    data_provider = providers.Singleton(
        TypedDataProviderAdapter,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
    )

    # Typed market data service (new path)
    market_data_service = providers.Singleton(
        MarketDataService,
        market_data_repo=alpaca_manager,
    )

    # Backward compatibility: provide same interface
    trading_repository = alpaca_manager
    market_data_repository = alpaca_manager
    account_repository = alpaca_manager
