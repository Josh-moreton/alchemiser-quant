"""Business Unit: strategy | Status: current.

Dependency wiring for strategy_v2 module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.

The strategy module uses a fallback chain for market data:
1. S3 Parquet cache (primary) - fast local reads
2. DataLambdaClient (fallback) - triggers Data Lambda to refresh from Alpaca

This ensures strategies never fail due to missing data - if cache is empty,
the Data Lambda fetches from Alpaca on-demand.
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

    The market data fallback chain:
    - CachedMarketDataAdapter reads from S3 Parquet (fast)
    - On cache miss, delegates to DataLambdaClient
    - DataLambdaClient invokes Data Lambda with refresh_single to fetch from Alpaca
    - Data Lambda stores in S3, then returns bars

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
    from the_alchemiser.strategy_v2.adapters.data_lambda_client import (
        DataLambdaClient,
    )
    from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator
    from the_alchemiser.strategy_v2.core.registry import StrategyRegistry

    # Register strategy registry (singleton - shared state for registered strategies)
    container.strategy_registry = providers.Singleton(StrategyRegistry)

    # Register market data store (reads from S3 Parquet)
    container.market_data_store = providers.Singleton(MarketDataStore)

    # Register Data Lambda client as fallback for on-demand data fetching
    container.data_lambda_client = providers.Singleton(
        DataLambdaClient,
        enable_refresh_on_miss=True,
    )

    # Register market data adapter with fallback chain:
    # S3 cache -> DataLambdaClient (refresh_single) -> Alpaca -> S3
    container.strategy_market_data_adapter = providers.Factory(
        CachedMarketDataAdapter,
        market_data_store=container.market_data_store,
        fallback_adapter=container.data_lambda_client,
        enable_live_fallback=False,  # Use DataLambdaClient instead of direct Alpaca
    )

    # Register strategy orchestrator (uses market data adapter)
    container.strategy_orchestrator = providers.Factory(
        SingleStrategyOrchestrator,
        market_data_adapter=container.strategy_market_data_adapter,
    )
