#!/usr/bin/env python3
"""Business Unit: strategy | Status: current

Strategy orchestrator factory for easy setup.

Provides factory functions for creating properly configured
strategy orchestrators with market data adapters.
"""

from __future__ import annotations

from ...shared.brokers.alpaca_manager import AlpacaManager
from ..adapters.market_data_adapter import StrategyMarketDataAdapter
from .orchestrator import StrategyOrchestrator


def create_orchestrator(api_key: str, secret_key: str, paper: bool = True) -> StrategyOrchestrator:
    """Create a strategy orchestrator with Alpaca market data.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper: Whether to use paper trading (default: True)

    Returns:
        Configured strategy orchestrator

    """
    # Create Alpaca manager
    alpaca_manager = AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper)

    # Create market data adapter
    market_data_adapter = StrategyMarketDataAdapter(alpaca_manager)

    # Create orchestrator
    return StrategyOrchestrator(market_data_adapter)


def create_orchestrator_with_adapter(
    market_data_adapter: StrategyMarketDataAdapter,
) -> StrategyOrchestrator:
    """Create a strategy orchestrator with existing adapter.

    Args:
        market_data_adapter: Pre-configured market data adapter

    Returns:
        Strategy orchestrator

    """
    return StrategyOrchestrator(market_data_adapter)
