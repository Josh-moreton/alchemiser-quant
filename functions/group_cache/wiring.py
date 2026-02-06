"""Business Unit: group_cache | Status: current.

Dependency wiring for group_cache module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.

The group cache module reads market data directly from S3 Parquet cache.
Data must be pre-populated by the scheduled Data Lambda refresh.
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

    Args:
        container: The main ApplicationContainer instance

    """
    from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )
    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore

    # Register market data store (reads from S3 Parquet)
    container.market_data_store = providers.Singleton(MarketDataStore)

    # Register market data adapter
    container.strategy_market_data_adapter = providers.Factory(
        CachedMarketDataAdapter,
        market_data_store=container.market_data_store,
        fallback_adapter=None,
        enable_live_fallback=False,
        enable_sync_refresh=True,  # Enable on-demand data fetching via Data Lambda
    )
