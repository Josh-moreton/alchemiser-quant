#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy registry for mapping strategy names to callables.

Provides a centralized registry for strategy engines that maps
strategy identifiers to their corresponding engine implementations.

Thread Safety:
    The global registry instance uses a lock to ensure thread-safe
    access to the registry in concurrent environments.

Lifecycle:
    The global registry is instantiated at module import time and
    persists for the lifetime of the process. Use the module-level
    functions (register_strategy, get_strategy, list_strategies)
    for all operations.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Protocol, runtime_checkable

from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ...shared.types.market_data_port import MarketDataPort
from ..errors import StrategyRegistryError


@runtime_checkable
class StrategyEngine(Protocol):
    """Protocol for strategy engine implementations."""

    def __call__(
        self, context: datetime | MarketDataPort | dict[str, datetime | MarketDataPort]
    ) -> StrategyAllocation:
        """Execute strategy and return allocation schema."""
        ...


class StrategyRegistry:
    """Registry for strategy engines.
    
    Thread-safe registry for managing strategy engine instances.
    All operations are protected by an internal lock.
    """

    def __init__(self) -> None:
        """Initialize empty registry with thread lock."""
        self._strategies: dict[str, StrategyEngine] = {}
        self._lock = threading.RLock()

    def register(self, strategy_id: str, engine: StrategyEngine) -> None:
        """Register a strategy engine.

        Args:
            strategy_id: Unique identifier for the strategy
            engine: Strategy engine implementation

        Raises:
            StrategyRegistryError: If strategy_id is invalid or empty

        """
        with self._lock:
            # Validate strategy_id
            if not strategy_id or not isinstance(strategy_id, str):
                raise StrategyRegistryError(
                    "strategy_id must be a non-empty string",
                    strategy_id=str(strategy_id) if strategy_id else None,
                )
            
            strategy_id = strategy_id.strip()
            if not strategy_id:
                raise StrategyRegistryError(
                    "strategy_id cannot be empty or whitespace-only"
                )
            
            if len(strategy_id) > 100:
                raise StrategyRegistryError(
                    f"strategy_id exceeds maximum length of 100 characters: {len(strategy_id)}",
                    strategy_id=strategy_id[:50],  # Truncate for logging
                )
            
            # Runtime check for Protocol compliance if possible
            if not callable(engine):
                raise StrategyRegistryError(
                    "engine must be callable (implement StrategyEngine protocol)",
                    strategy_id=strategy_id,
                )
            
            self._strategies[strategy_id] = engine

    def get_strategy(self, strategy_id: str) -> StrategyEngine:
        """Get strategy engine by ID.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Strategy engine implementation

        Raises:
            StrategyRegistryError: If strategy not found

        """
        with self._lock:
            if strategy_id not in self._strategies:
                available = list(self._strategies.keys())
                raise StrategyRegistryError(
                    f"Strategy '{strategy_id}' not found. Available strategies: {available}",
                    strategy_id=strategy_id,
                    available_strategies=", ".join(available) if available else "none",
                )
            return self._strategies[strategy_id]

    def list_strategies(self) -> list[str]:
        """List all registered strategy IDs.
        
        Returns:
            List of registered strategy identifiers
            
        """
        with self._lock:
            return list(self._strategies.keys())


# Global registry instance
_registry = StrategyRegistry()


def register_strategy(strategy_id: str, engine: StrategyEngine) -> None:
    """Register a strategy in the global registry.
    
    Args:
        strategy_id: Unique identifier for the strategy
        engine: Strategy engine implementation
        
    Raises:
        StrategyRegistryError: If strategy_id is invalid or engine is not callable
        
    """
    _registry.register(strategy_id, engine)


def get_strategy(strategy_id: str) -> StrategyEngine:
    """Get strategy from global registry.
    
    Args:
        strategy_id: Strategy identifier
        
    Returns:
        Strategy engine implementation
        
    Raises:
        StrategyRegistryError: If strategy not found
        
    """
    return _registry.get_strategy(strategy_id)


def list_strategies() -> list[str]:
    """List all registered strategies.
    
    Returns:
        List of registered strategy identifiers
        
    """
    return _registry.list_strategies()
