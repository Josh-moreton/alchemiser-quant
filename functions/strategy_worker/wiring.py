"""Business Unit: strategy | Status: current.

Dependency wiring for strategy_v2 module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.

The strategy module reads market data directly from S3 Parquet cache.
Data must be pre-populated by the scheduled Data Lambda refresh.

Live Bar Injection:
    When append_live_bar=True, the adapter appends today's current bar from
    Alpaca Snapshot API to all historical data. This enables real-time signal
    generation at 3:45 PM ET using current intraday prices.
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

    Live Bar Injection:
        When append_live_bar=True, today's current bar from Alpaca Snapshot API
        is appended to all historical data. This enables real-time signal
        generation at 3:45 PM ET using current intraday prices.

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

    # Register market data adapter with live bar injection and sync refresh enabled
    # This appends today's current bar to all indicator computations
    # Sync refresh: On cache miss, invokes Data Lambda to fetch missing data
    container.strategy_market_data_adapter = providers.Factory(
        CachedMarketDataAdapter,
        market_data_store=container.market_data_store,
        fallback_adapter=None,
        enable_live_fallback=False,
        append_live_bar=True,  # Enable live bar injection for real-time signals
        enable_sync_refresh=True,  # Enable on-demand data fetching via Data Lambda
    )

    # Register strategy orchestrator (uses market data adapter)
    container.strategy_orchestrator = providers.Factory(
        SingleStrategyOrchestrator,
        market_data_adapter=container.strategy_market_data_adapter,
    )
