"""Business Unit: strategy | Status: current.

Dependency wiring for strategy_v2 module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.

The strategy module reads market data directly from S3 Parquet cache.
Data must be pre-populated by the scheduled Data Lambda refresh.

Live Bar Injection:
    The adapter fetches today's current price from Alpaca Snapshot API and
    appends it to historical data. This enables strategies to use the most
    recent price for indicator computation (e.g., 200-day SMA uses 199
    historical days + today's current price).
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

    Live bar injection is always enabled - today's current price from Alpaca
    Snapshot API is appended to historical data, enabling strategies to compute
    indicators with the most recent price as "today's close".

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
    from the_alchemiser.data_v2.live_bar_provider import LiveBarProvider
    from the_alchemiser.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator
    from the_alchemiser.strategy_v2.core.registry import StrategyRegistry

    # Register strategy registry (singleton - shared state for registered strategies)
    container.strategy_registry = providers.Singleton(StrategyRegistry)

    # Register market data store (reads from S3 Parquet)
    container.market_data_store = providers.Singleton(MarketDataStore)

    # Create live bar provider for fetching today's price from Alpaca
    live_bar_provider = LiveBarProvider()

    # Register market data adapter with live bar injection enabled
    # Fetches today's price from Alpaca and appends to historical data
    container.strategy_market_data_adapter = providers.Factory(
        CachedMarketDataAdapter,
        market_data_store=container.market_data_store,
        fallback_adapter=None,
        enable_live_fallback=False,
        append_live_bar=True,
        live_bar_provider=live_bar_provider,
    )

    # Register strategy orchestrator (uses market data adapter)
    container.strategy_orchestrator = providers.Factory(
        SingleStrategyOrchestrator,
        market_data_adapter=container.strategy_market_data_adapter,
    )
