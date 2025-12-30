"""Business Unit: strategy | Status: current.

Dependency wiring for strategy_v2 module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.

The strategy module reads market data directly from S3 Parquet cache.
Data must be pre-populated by the scheduled Data Lambda refresh.

Historical Data Only:
    Indicators use only historical data from S3 Parquet files. For example,
    a 200-day SMA uses the last 200 days of close prices from the cache,
    without appending today's live price.
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
    Data must be pre-populated by the scheduled Data Lambda refresh.

    Indicators use only historical data from parquet files - today's live price
    is NOT appended. For example, a 200-day SMA uses the last 200 days of
    close prices from the cache.

    Args:
        container: The main ApplicationContainer instance

    Example:
        >>> container = ApplicationContainer()
        >>> register_strategy(container)
        >>> registry = container.strategy_registry()
        >>> orchestrator = container.strategy_orchestrator()

    """
    from the_alchemiser.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )
    from the_alchemiser.data_v2.market_data_store import MarketDataStore
    from core.orchestrator import SingleStrategyOrchestrator
    from core.registry import StrategyRegistry

    # Register strategy registry (singleton - shared state for registered strategies)
    container.strategy_registry = providers.Singleton(StrategyRegistry)

    # Register market data store (reads from S3 Parquet)
    container.market_data_store = providers.Singleton(MarketDataStore)

    # Register market data adapter using only historical data from parquet
    # No live bar injection - indicators use only cached historical data
    container.strategy_market_data_adapter = providers.Factory(
        CachedMarketDataAdapter,
        market_data_store=container.market_data_store,
        fallback_adapter=None,
        enable_live_fallback=False,
        append_live_bar=False,
    )

    # Register strategy orchestrator (uses market data adapter)
    container.strategy_orchestrator = providers.Factory(
        SingleStrategyOrchestrator,
        market_data_adapter=container.strategy_market_data_adapter,
    )
