#!/usr/bin/env python3
"""Business Unit: strategy & signal generation; Status: current.

Strategy Registry for The Alchemiser Quantitative Trading System.

This module provides a registry-based approach to strategy management, replacing
dynamic imports with explicit registration and factory patterns.

The registry maps strategy names to their corresponding classes, enabling
static analysis while maintaining flexibility in strategy selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from the_alchemiser.strategy.engines.nuclear_typed_engine import NuclearTypedEngine
from the_alchemiser.strategy.engines.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.strategy.engines.typed_klm_ensemble_engine import (
    TypedKLMStrategyEngine,
)


class StrategyType(Enum):
    """Enumeration of available trading strategies."""

    NUCLEAR = "NUCLEAR"
    TECL = "TECL"
    KLM = "KLM"


@dataclass
class StrategyConfig:
    """Configuration for strategy initialization."""

    strategy_type: StrategyType
    engine_class: type
    default_allocation: float
    description: str
    enabled: bool = True


class StrategyRegistry:
    """Registry for managing trading strategy engines.

    This class maintains a mapping of strategy types to their implementations,
    enabling static analysis while providing flexibility in strategy management.
    """

    # Static mapping of strategy types to their configurations
    _strategies: dict[StrategyType, StrategyConfig] = {
        StrategyType.NUCLEAR: StrategyConfig(
            strategy_type=StrategyType.NUCLEAR,
            engine_class=NuclearTypedEngine,
            default_allocation=0.4,
            description="Nuclear energy and volatility hedge strategy",
            enabled=True,
        ),
        StrategyType.TECL: StrategyConfig(
            strategy_type=StrategyType.TECL,
            engine_class=TECLStrategyEngine,
            default_allocation=0.6,
            description="Technology leverage and momentum strategy",
            enabled=True,
        ),
        StrategyType.KLM: StrategyConfig(
            strategy_type=StrategyType.KLM,
            engine_class=TypedKLMStrategyEngine,
            default_allocation=0.2,
            description="Ensemble strategy with multiple variants",
            enabled=True,  # Enable to use the KLM strategy
        ),
    }

    @classmethod
    def get_strategy_config(cls, strategy_type: StrategyType) -> StrategyConfig | None:
        """Get configuration for a specific strategy type.

        Args:
            strategy_type: The strategy type to get config for.

        Returns:
            StrategyConfig if found, None otherwise.

        """
        return cls._strategies.get(strategy_type)

    @classmethod
    def get_enabled_strategies(cls) -> dict[StrategyType, StrategyConfig]:
        """Get all enabled strategy configurations.

        Returns:
            Dictionary mapping strategy types to their configurations.

        """
        return {
            strategy_type: config
            for strategy_type, config in cls._strategies.items()
            if config.enabled
        }

    @classmethod
    def create_strategy_engine(cls, strategy_type: StrategyType, **kwargs: Any) -> Any:
        """Create a strategy engine instance.

        Args:
            strategy_type: The type of strategy to create.
            **kwargs: Additional arguments to pass to the strategy constructor.

        Returns:
            Strategy engine instance.

        Raises:
            ValueError: If strategy type is not registered or disabled.

        """
        config = cls.get_strategy_config(strategy_type)
        if not config:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        if not config.enabled:
            raise ValueError(f"Strategy {strategy_type} is disabled")

        return config.engine_class(**kwargs)

    @classmethod
    def get_default_allocations(cls) -> dict[StrategyType, float]:
        """Get default allocation weights for all enabled strategies.

        Returns:
            Dictionary mapping strategy types to default allocation weights.

        """
        enabled_configs = cls.get_enabled_strategies()

        # Calculate total default allocation
        total_allocation = sum(config.default_allocation for config in enabled_configs.values())

        # Normalize to sum to 1.0
        if total_allocation > 0:
            return {
                strategy_type: config.default_allocation / total_allocation
                for strategy_type, config in enabled_configs.items()
            }

        return {}

    @classmethod
    def is_strategy_enabled(cls, strategy_type: StrategyType) -> bool:
        """Check if a strategy is enabled.

        Args:
            strategy_type: The strategy type to check.

        Returns:
            True if strategy is enabled, False otherwise.

        """
        config = cls.get_strategy_config(strategy_type)
        return config.enabled if config else False

    @classmethod
    def get_all_strategy_types(cls) -> list[StrategyType]:
        """Get all registered strategy types.

        Returns:
            List of all strategy types.

        """
        return list(cls._strategies.keys())

    @classmethod
    def enable_strategy(cls, strategy_type: StrategyType) -> None:
        """Enable a strategy.

        Args:
            strategy_type: The strategy type to enable.

        Raises:
            ValueError: If strategy type is not registered.

        """
        config = cls.get_strategy_config(strategy_type)
        if not config:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        config.enabled = True

    @classmethod
    def disable_strategy(cls, strategy_type: StrategyType) -> None:
        """Disable a strategy.

        Args:
            strategy_type: The strategy type to disable.

        Raises:
            ValueError: If strategy type is not registered.

        """
        config = cls.get_strategy_config(strategy_type)
        if not config:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        config.enabled = False


# Export the registry and types for easy access
__all__ = ["StrategyConfig", "StrategyRegistry", "StrategyType"]
