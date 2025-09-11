#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy Registry for The Alchemiser Quantitative Trading System.

This module provides a registry-based approach to strategy management, replacing
dynamic imports with explicit registration and factory patterns.

The registry maps strategy names to their corresponding classes, enabling
static analysis while maintaining flexibility in strategy selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Direct imports from strategy_v2 to avoid circular dependencies  
# NOTE: This is a temporary bridge until CLI migration to strategy_v2 is complete
from the_alchemiser.strategy.types.strategy_type import StrategyType

# Remove the local StrategyType definition since it's now in shared
# class StrategyType(Enum):
#     """Enumeration of available trading strategies."""
#     NUCLEAR = "NUCLEAR"
#     TECL = "TECL"
#     KLM = "KLM"


@dataclass
class StrategyConfig:
    """Configuration for strategy initialization."""

    strategy_type: StrategyType
    engine_module_path: str  # Changed from engine_class to module path for lazy loading
    default_allocation: float
    description: str
    enabled: bool = True
    
    def get_engine_class(self) -> type:
        """Lazy load engine class to avoid circular imports."""
        # Direct imports from strategy_v2 to avoid circular dependency
        if self.strategy_type == StrategyType.NUCLEAR:
            from the_alchemiser.strategy_v2.engines.nuclear.engine import NuclearEngine
            return NuclearEngine
        elif self.strategy_type == StrategyType.KLM:
            from the_alchemiser.strategy_v2.engines.klm.engine import KLMEngine
            return KLMEngine
        elif self.strategy_type == StrategyType.TECL:
            from the_alchemiser.strategy_v2.engines.tecl.engine import TECLEngine
            return TECLEngine
        else:
            raise ValueError(f"Unknown strategy type: {self.strategy_type}")


class StrategyRegistry:
    """Registry for managing trading strategy engines.

    This class maintains a mapping of strategy types to their implementations,
    enabling static analysis while providing flexibility in strategy management.
    """

    # Static mapping of strategy types to their configurations
    _strategies: dict[StrategyType, StrategyConfig] = {
        StrategyType.NUCLEAR: StrategyConfig(
            strategy_type=StrategyType.NUCLEAR,
            engine_module_path="the_alchemiser.strategy_v2.engines.nuclear.engine",
            default_allocation=0.4,
            description="Nuclear energy and volatility hedge strategy",
            enabled=True,
        ),
        StrategyType.TECL: StrategyConfig(
            strategy_type=StrategyType.TECL,
            engine_module_path="the_alchemiser.strategy_v2.engines.tecl.engine",
            default_allocation=0.6,
            description="Technology leverage and momentum strategy",
            enabled=True,
        ),
        StrategyType.KLM: StrategyConfig(
            strategy_type=StrategyType.KLM,
            engine_module_path="the_alchemiser.strategy_v2.engines.klm.engine",
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
    def create_strategy_engine(cls, strategy_type: StrategyType, **kwargs: Any) -> Any:  # noqa: ANN401  # Strategy factory with dynamic parameters and return types
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

        return config.get_engine_class()(**kwargs)

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
