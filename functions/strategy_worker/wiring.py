"""Business Unit: strategy | Status: current.

Dependency wiring for strategy worker module.

Provides register_strategy() function to wire strategy module dependencies
into the main ApplicationContainer. Follows single composition root pattern.

The strategy module reads market data directly from S3 Parquet cache.
Data must be pre-populated by the scheduled Data Lambda refresh (morning +
post-close schedules ensure today's completed bars are available).

The strategy worker also handles rebalance planning and trade enqueue,
operating as an independent per-strategy execution unit.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from dependency_injector import providers

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_strategy(container: ApplicationContainer) -> None:
    """Register strategy module dependencies in the application container.

    This function wires up all strategy module components using constructor
    injection. It accesses infrastructure dependencies from the container
    and registers strategy services.

    Components registered:
    - StrategyRegistry: Strategy file registry
    - MarketDataStore + CachedMarketDataAdapter: S3 Parquet market data
    - StrategyRebalancer: Per-strategy rebalance orchestration

    Args:
        container: The main ApplicationContainer instance

    """
    from core.orchestrator import SingleStrategyOrchestrator
    from core.registry import StrategyRegistry
    from core.strategy_rebalancer import StrategyRebalancer

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

    # Register per-strategy rebalancer
    # Uses AlpacaManager from infrastructure for account equity and prices
    execution_queue_url = os.environ.get("EXECUTION_FIFO_QUEUE_URL", "")
    execution_runs_table = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "")
    trade_ledger_table = os.environ.get("TRADE_LEDGER__TABLE_NAME", "")
    rebalance_plan_table = os.environ.get("REBALANCE_PLAN__TABLE_NAME")

    container.strategy_rebalancer = providers.Factory(
        StrategyRebalancer,
        alpaca_manager=container.infrastructure.alpaca_manager,
        trade_ledger_table=trade_ledger_table,
        execution_queue_url=execution_queue_url,
        execution_runs_table=execution_runs_table,
        rebalance_plan_table=rebalance_plan_table,
    )
