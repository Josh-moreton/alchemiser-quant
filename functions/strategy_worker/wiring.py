"""Business Unit: strategy | Status: current.

Dependency wiring for strategy_v2 module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.

The strategy module reads market data directly from S3 Parquet cache.
Data must be pre-populated by the scheduled Data Lambda refresh (morning +
post-close schedules ensure today's completed bars are available).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import providers

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_strategy(container: ApplicationContainer) -> None:
    """Register strategy module dependencies in the application container.

    This function wires up all strategy module components using constructor
    injection. It accesses infrastructure dependencies from the container
    and registers strategy services.

    Market data is read directly from S3 Parquet cache by CachedMarketDataAdapter.
    Data must be pre-populated by the scheduled Data Lambda refresh (morning +
    post-close schedules ensure today's completed bars are available).

    Args:
        container: The main ApplicationContainer instance

    Example:
        >>> container = ApplicationContainer()
        >>> register_strategy(container)
        >>> registry = container.strategy_registry()
        >>> orchestrator = container.strategy_orchestrator()

    """
    from core.orchestrator import SingleStrategyOrchestrator
    from core.registry import StrategyRegistry

    from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )
    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore

    # Register strategy registry (singleton - shared state for registered strategies)
    container.strategy_registry = providers.Singleton(StrategyRegistry)

    # Register market data store (reads from S3 Parquet)
    container.market_data_store = providers.Singleton(MarketDataStore)

    # Register market data adapter with sync refresh enabled
    # Sync refresh: On cache miss, invokes Data Lambda to fetch missing data
    container.strategy_market_data_adapter = providers.Factory(
        CachedMarketDataAdapter,
        market_data_store=container.market_data_store,
        fallback_adapter=None,
        enable_live_fallback=False,
        enable_sync_refresh=True,  # Enable on-demand data fetching via Data Lambda
    )

    # Register strategy orchestrator (uses market data adapter)
    container.strategy_orchestrator = providers.Factory(
        SingleStrategyOrchestrator,
        market_data_adapter=container.strategy_market_data_adapter,
    )
