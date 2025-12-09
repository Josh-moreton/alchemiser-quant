"""Business Unit: strategy | Status: current.

Dependency wiring for strategy_v2 module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.
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

    Note: Strategy Lambda uses CachedMarketDataAdapter (S3-only) to avoid
    requiring alpaca-py at runtime. Historical data is pre-populated by
    the DataRefresh Lambda.

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
    from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator
    from the_alchemiser.strategy_v2.core.registry import StrategyRegistry

    # Register strategy registry (singleton - shared state for registered strategies)
    container.strategy_registry = providers.Singleton(StrategyRegistry)

    # Register market data store (reads from S3 Parquet)
    container.market_data_store = providers.Singleton(MarketDataStore)

    # Register market data adapter (uses S3 cache, no Alpaca fallback)
    container.strategy_market_data_adapter = providers.Factory(
        CachedMarketDataAdapter,
        market_data_store=container.market_data_store,
    )

    # Register strategy orchestrator (uses market data adapter)
    container.strategy_orchestrator = providers.Factory(
        SingleStrategyOrchestrator,
        market_data_adapter=container.strategy_market_data_adapter,
    )
