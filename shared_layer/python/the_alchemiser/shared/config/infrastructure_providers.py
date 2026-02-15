"""Business Unit: utilities; Status: current.

Infrastructure layer providers for dependency injection.

Note: This module uses lazy imports to avoid pulling in alpaca-py for Lambdas
that don't need it (e.g., Strategy Lambda uses S3 cache only).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from dependency_injector import containers, providers

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers import AlpacaManager
    from the_alchemiser.shared.options.adapters import AlpacaOptionsAdapter
    from the_alchemiser.shared.services.market_data_service import MarketDataService
    from the_alchemiser.shared.types.market_data_port import MarketDataPort


def _create_alpaca_manager(api_key: str, secret_key: str, *, paper: bool) -> AlpacaManager:
    """Create AlpacaManager with lazy import.

    This function delays the import of AlpacaManager until it's actually needed,
    allowing Lambdas that don't need Alpaca (like Strategy with S3 cache) to
    avoid importing alpaca-py.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper: Whether to use paper trading

    Returns:
        AlpacaManager instance

    """
    from the_alchemiser.shared.brokers import AlpacaManager

    return AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper)


def _create_alpaca_options_adapter(
    api_key: str, secret_key: str, *, paper: bool
) -> AlpacaOptionsAdapter:
    """Create AlpacaOptionsAdapter with lazy import.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper: Whether to use paper trading

    Returns:
        AlpacaOptionsAdapter instance

    """
    from the_alchemiser.shared.options.adapters import AlpacaOptionsAdapter

    return AlpacaOptionsAdapter(api_key=api_key, secret_key=secret_key, paper=paper)


def _create_market_data_service(market_data_repo: object) -> MarketDataService:
    """Create MarketDataService with lazy import.

    Args:
        market_data_repo: Repository for market data (typically AlpacaManager)

    Returns:
        MarketDataService instance

    """
    from the_alchemiser.shared.services.market_data_service import MarketDataService

    return MarketDataService(market_data_repo=market_data_repo)  # type: ignore[arg-type]


def _create_cached_market_data_adapter(
    api_key: str, secret_key: str, *, paper: bool
) -> MarketDataPort:
    """Create market data adapter based on environment configuration.

    If MARKET_DATA_BUCKET is set, returns S3-backed CachedMarketDataAdapter.
    Otherwise, returns Alpaca-backed MarketDataService (requires alpaca-py).

    This design ensures Strategy Lambda (with MARKET_DATA_BUCKET set) never
    imports alpaca-py, while Execution/Portfolio Lambdas (without bucket or
    needing live data) still get Alpaca access.

    Args:
        api_key: Alpaca API key (only used if falling back to Alpaca)
        secret_key: Alpaca secret key (only used if falling back to Alpaca)
        paper: Whether to use paper trading (only used if falling back to Alpaca)

    Returns:
        CachedMarketDataAdapter if MARKET_DATA_BUCKET set, else MarketDataService

    """
    bucket = os.environ.get("MARKET_DATA_BUCKET")

    if bucket:
        try:
            # Import here to avoid circular dependencies and optional fastparquet dependency
            from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
                CachedMarketDataAdapter,
            )
            from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore

            store = MarketDataStore(bucket_name=bucket)
            # Return cached adapter WITHOUT Alpaca fallback
            # Strategy Lambda uses S3 cache only - no live API calls needed
            return CachedMarketDataAdapter(market_data_store=store)
        except ImportError as e:
            # fastparquet not available - fall through to Alpaca
            # This is expected for Lambdas without data_v2 dependencies
            import logging

            logging.getLogger(__name__).debug(
                "CachedMarketDataAdapter not available (ImportError: %s), using Alpaca", e
            )
        except Exception as e:
            # Unexpected error creating cache adapter - log and fall through to Alpaca
            import logging

            logging.getLogger(__name__).warning(
                "Failed to create CachedMarketDataAdapter: %s, falling back to Alpaca", e
            )

    # No bucket configured or cache creation failed - use Alpaca (requires alpaca-py)
    from the_alchemiser.shared.brokers import AlpacaManager
    from the_alchemiser.shared.services.market_data_service import MarketDataService

    alpaca = AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper)
    return MarketDataService(market_data_repo=alpaca)


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
    # Uses lazy import via factory to avoid importing alpaca-py until actually needed.
    # Ensures single connection pool to Alpaca APIs (trading, market data, account)
    # Implements: TradingRepository, MarketDataRepository, AccountRepository
    alpaca_manager = providers.Singleton(
        _create_alpaca_manager,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading,
    )

    # Base market data service (direct Alpaca access)
    # Uses lazy import to avoid importing alpaca-py for Lambdas that don't need it
    # Used internally and as fallback for cached adapter
    _base_market_data_service = providers.Singleton(
        _create_market_data_service,
        market_data_repo=alpaca_manager,
    )

    # Market data service with proper domain boundary (Singleton pattern)
    # If MARKET_DATA_BUCKET is set, uses S3 cache (no Alpaca import needed).
    # Otherwise, uses direct Alpaca access (imports alpaca-py lazily).
    # This allows Strategy Lambda to run without alpaca-py in its layer.
    market_data_service = providers.Singleton(
        _create_cached_market_data_adapter,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading,
    )

    # Backward compatibility aliases (deprecated, will be removed in v3.0.0)
    # These aliases allow legacy code to use old names while we migrate to alpaca_manager
    # All aliases point to the same singleton instance
    trading_repository = alpaca_manager
    market_data_repository = alpaca_manager
    account_repository = alpaca_manager

    # Alpaca Options adapter (Singleton pattern)
    # Used for options chain queries, quotes, and order placement
    # Implements separate options-specific API endpoints from alpaca_manager
    alpaca_options_adapter = providers.Singleton(
        _create_alpaca_options_adapter,
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.paper_trading,
    )
