"""Business Unit: utilities; Status: current.

Infrastructure layer providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.shared.brokers import AlpacaManager
from the_alchemiser.shared.services.market_data_service import MarketDataService


class InfrastructureProviders(containers.DeclarativeContainer):
    """Providers for infrastructure layer components.

    This container manages the lifecycle of infrastructure dependencies including:
    - AlpacaManager: Singleton broker client for Alpaca API interactions
    - MarketDataService: Domain service wrapping market data access

    All providers use Singleton scope to ensure efficient resource usage and
    connection pooling for external APIs.

    Example:
        >>> from the_alchemiser.shared.config.infrastructure_providers import InfrastructureProviders
        >>> container = InfrastructureProviders()
        >>> container.config.alpaca_api_key.override("test_key")
        >>> container.config.alpaca_secret_key.override("test_secret")
        >>> container.config.paper_trading.override(True)
        >>> manager = container.alpaca_manager()  # Singleton instance

    """

    # Configuration dependency injection point
    # Injected by ApplicationContainer with ConfigProviders
    config = providers.DependenciesContainer()

    # Alpaca broker client (Singleton pattern)
    # Ensures single connection pool to Alpaca APIs (trading, market data, account)
    # Implements: TradingRepository, MarketDataRepository, AccountRepository
    alpaca_manager = providers.Singleton(
        AlpacaManager,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading,
    )

    # Market data service with proper domain boundary (Singleton pattern)
    # Wraps AlpacaManager to provide domain-facing interface with:
    # - Timeframe normalization
    # - Error translation to domain exceptions
    # - Symbol type conversion
    market_data_service = providers.Singleton(
        MarketDataService,
        market_data_repo=alpaca_manager,
    )

    # Backward compatibility aliases (deprecated, will be removed in v3.0.0)
    # These aliases allow legacy code to use old names while we migrate to alpaca_manager
    # All aliases point to the same singleton instance
    trading_repository = alpaca_manager
    market_data_repository = alpaca_manager
    account_repository = alpaca_manager
