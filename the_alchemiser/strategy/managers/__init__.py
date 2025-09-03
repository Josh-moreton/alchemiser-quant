"""Business Unit: strategy | Status: current

Strategy managers and orchestrators.

This module contains strategy management classes that coordinate
multiple strategy engines and handle signal aggregation.
"""

from __future__ import annotations

from .typed_strategy_manager import AggregatedSignals, TypedStrategyManager

__all__ = [
    "AggregatedSignals",
    "TypedStrategyManager",
]
