#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy registry for mapping strategy names to callables.

Provides a centralized registry for strategy engines that maps
strategy identifiers to their corresponding engine implementations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from the_alchemiser.shared.errors import StrategyExecutionError
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ...shared.types.market_data_port import MarketDataPort


@runtime_checkable
class StrategyCallable(Protocol):
    """Protocol for callable strategy implementations (legacy pattern).

    Note: This is a legacy protocol for the registry pattern. New code should
    use the StrategyEngine protocol from shared.types.strategy_protocol instead.

    This protocol supports callable strategies that accept various context types
    and return allocation schemas. It's maintained for backwards compatibility
    with existing strategy implementations in the registry.
    """

    def __call__(
        self, context: datetime | MarketDataPort | dict[str, datetime | MarketDataPort]
    ) -> StrategyAllocation:
        """Execute strategy and return allocation schema."""
        ...


class StrategyRegistry:
    """Registry for strategy engines."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._strategies: dict[str, StrategyCallable] = {}

    def register(self, strategy_id: str, engine: StrategyCallable) -> None:
        """Register a strategy engine.

        Args:
            strategy_id: Unique identifier for the strategy
            engine: Strategy engine implementation

        """
        self._strategies[strategy_id] = engine

    def get_strategy(self, strategy_id: str) -> StrategyCallable:
        """Get strategy engine by ID.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Strategy engine implementation

        Raises:
            StrategyExecutionError: If strategy not found

        """
        if strategy_id not in self._strategies:
            available = list(self._strategies.keys())
            raise StrategyExecutionError(
                f"Strategy '{strategy_id}' not found. Available strategies: {available}",
                strategy_name=strategy_id,
                operation="get_strategy",
            )
        return self._strategies[strategy_id]

    def list_strategies(self) -> list[str]:
        """List all registered strategy IDs."""
        return list(self._strategies.keys())


# Global registry instance
_registry = StrategyRegistry()


def register_strategy(strategy_id: str, engine: StrategyCallable) -> None:
    """Register a strategy in the global registry."""
    _registry.register(strategy_id, engine)


def get_strategy(strategy_id: str) -> StrategyCallable:
    """Get strategy from global registry."""
    return _registry.get_strategy(strategy_id)


def list_strategies() -> list[str]:
    """List all registered strategies."""
    return _registry.list_strategies()
