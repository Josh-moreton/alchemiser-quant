#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy registry for mapping strategy names to callables.

Provides a centralized registry for strategy engines that maps
strategy identifiers to their corresponding engine implementations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from the_alchemiser.shared.schemas.strategy import StrategyAllocation

from ...shared.types.market_data_port import MarketDataPort


class StrategyEngine(Protocol):
    """Protocol for strategy engine implementations."""

    def __call__(
        self, context: datetime | MarketDataPort | dict[str, datetime | MarketDataPort]
    ) -> StrategyAllocation:
        """Execute strategy and return allocation DTO."""
        ...


class StrategyRegistry:
    """Registry for strategy engines."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._strategies: dict[str, StrategyEngine] = {}

    def register(self, strategy_id: str, engine: StrategyEngine) -> None:
        """Register a strategy engine.

        Args:
            strategy_id: Unique identifier for the strategy
            engine: Strategy engine implementation

        """
        self._strategies[strategy_id] = engine

    def get_strategy(self, strategy_id: str) -> StrategyEngine:
        """Get strategy engine by ID.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Strategy engine implementation

        Raises:
            KeyError: If strategy not found

        """
        if strategy_id not in self._strategies:
            available = list(self._strategies.keys())
            raise KeyError(f"Strategy '{strategy_id}' not found. Available strategies: {available}")
        return self._strategies[strategy_id]

    def list_strategies(self) -> list[str]:
        """List all registered strategy IDs."""
        return list(self._strategies.keys())


# Global registry instance
_registry = StrategyRegistry()


def register_strategy(strategy_id: str, engine: StrategyEngine) -> None:
    """Register a strategy in the global registry."""
    _registry.register(strategy_id, engine)


def get_strategy(strategy_id: str) -> StrategyEngine:
    """Get strategy from global registry."""
    return _registry.get_strategy(strategy_id)


def list_strategies() -> list[str]:
    """List all registered strategies."""
    return _registry.list_strategies()
