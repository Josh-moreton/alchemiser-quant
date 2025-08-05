"""Registry package for The Alchemiser Quantitative Trading System.

This package provides registry-based factories and patterns to replace
dynamic imports and improve static analysis capabilities.

Modules:
    strategy_registry: Registry for trading strategies
"""

from typing import Any

from .strategy_registry import StrategyConfig, StrategyRegistry, StrategyType

__all__ = ["StrategyRegistry", "StrategyType", "StrategyConfig"]
