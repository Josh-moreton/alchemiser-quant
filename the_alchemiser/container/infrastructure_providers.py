"""Infrastructure layer providers for dependency injection."""

from dependency_injector import containers, providers

# Use the facade implementation for all data provider access
from the_alchemiser.infrastructure.data_providers.unified_data_provider_facade import (
    UnifiedDataProvider,
)
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

    # Underlying data provider facade
    _unified_data_provider = providers.Singleton(
        UnifiedDataProvider,
        paper_trading=config.paper_trading,
    )

    # Typed data provider adapter for strategies
    data_provider = providers.Singleton(
        TypedDataProviderAdapter,
        underlying_provider=_unified_data_provider,
    )

    # Backward compatibility: provide same interface
    trading_repository = alpaca_manager
    market_data_repository = alpaca_manager
    account_repository = alpaca_manager
