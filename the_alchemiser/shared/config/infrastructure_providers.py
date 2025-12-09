"""Business Unit: utilities; Status: current.

Infrastructure layer providers for dependency injection.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from the_alchemiser.shared.brokers import AlpacaManager
from the_alchemiser.shared.services.market_data_service import MarketDataService

if TYPE_CHECKING:
    from the_alchemiser.shared.types.market_data_port import MarketDataPort


def _create_cached_market_data_adapter(market_data_service: MarketDataService) -> MarketDataPort:
    """Create cached market data adapter if S3 bucket is configured.

    Falls back to original MarketDataService if bucket not configured or import fails.

    Args:
        market_data_service: Original Alpaca-backed market data service (used as fallback
            for lambdas that need live data, e.g., Portfolio/Execution)

    Returns:
        CachedMarketDataAdapter if configured, else original MarketDataService

    """
    bucket = os.environ.get("MARKET_DATA_BUCKET")

    if not bucket:
        # No bucket configured - use original service (requires Alpaca)
        return market_data_service

    try:
        # Import here to avoid circular dependencies and optional fastparquet dependency
        from the_alchemiser.data_v2.cached_market_data_adapter import (
            CachedMarketDataAdapter,
        )
        from the_alchemiser.data_v2.market_data_store import MarketDataStore

        store = MarketDataStore(bucket_name=bucket)
        # Return cached adapter WITHOUT Alpaca fallback
        # Strategy Lambda uses S3 cache only - no live API calls needed
        return CachedMarketDataAdapter(market_data_store=store)
    except ImportError:
        # fastparquet not available (not in this Lambda's layer)
        return market_data_service
    except Exception:
        # Any other error - fall back to original service
        return market_data_service


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

    # Base market data service (direct Alpaca access)
    # Used internally and as fallback for cached adapter
    _base_market_data_service = providers.Singleton(
        MarketDataService,
        market_data_repo=alpaca_manager,
    )

    # Market data service with proper domain boundary (Singleton pattern)
    # If MARKET_DATA_BUCKET is set, uses S3 cache with Alpaca fallback.
    # Otherwise, uses direct Alpaca access.
    market_data_service = providers.Singleton(
        _create_cached_market_data_adapter,
        market_data_service=_base_market_data_service,
    )

    # Backward compatibility aliases (deprecated, will be removed in v3.0.0)
    # These aliases allow legacy code to use old names while we migrate to alpaca_manager
    # All aliases point to the same singleton instance
    trading_repository = alpaca_manager
    market_data_repository = alpaca_manager
    account_repository = alpaca_manager
