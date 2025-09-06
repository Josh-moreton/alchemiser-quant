"""Business Unit: strategy | Status: current.

Strategy implementations (Nuclear, TECL, KLM, etc.).

This module contains the concrete strategy engine implementations that generate
trading signals based on market data and technical indicators.
"""

from __future__ import annotations

from ..managers.typed_strategy_manager import AggregatedSignals, TypedStrategyManager
# from . import core  # Temporarily disabled due to architectural violations
from .engine import StrategyEngine
# from .nuclear_typed_engine import NuclearTypedEngine  # Module doesn't exist
# from .tecl_strategy_engine import TECLStrategyEngine    # Module doesn't exist
# from .typed_klm_ensemble_engine import TypedKLMStrategyEngine  # Module doesn't exist

__all__ = [
    "AggregatedSignals",
    # "NuclearTypedEngine",
    "StrategyEngine", 
    # "TECLStrategyEngine",
    # "TypedKLMStrategyEngine",
    "TypedStrategyManager",
    # "core",
]
