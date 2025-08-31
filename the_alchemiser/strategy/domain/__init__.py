"""Business Unit: strategy & signal generation; Status: current.

Strategy domain layer.

Contains pure domain logic for strategy engines, signal generation,
and strategy-related value objects.
"""

from __future__ import annotations

# Import core abstractions that don't have heavy dependencies
from .strategies import StrategyEngine

# Import TypedStrategyManager that uses the registry
from .strategies.typed_strategy_manager import TypedStrategyManager

__all__ = [
    "StrategyEngine",
    "TypedStrategyManager",
]


# Expose strategy engines but allow lazy imports to avoid dependency issues
def get_nuclear_engine():
    """Lazy import for NuclearTypedEngine."""
    from .nuclear import NuclearTypedEngine

    return NuclearTypedEngine


def get_tecl_engine():
    """Lazy import for TECLStrategyEngine."""
    from .tecl import TECLStrategyEngine

    return TECLStrategyEngine


def get_klm_engine():
    """Lazy import for TypedKLMStrategyEngine."""
    from .klm import TypedKLMStrategyEngine

    return TypedKLMStrategyEngine
