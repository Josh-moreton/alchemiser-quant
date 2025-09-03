"""Business Unit: strategy | Status: current.

Strategy implementations (Nuclear, TECL, KLM, etc.).

This module contains the concrete strategy engine implementations that generate
trading signals based on market data and technical indicators.
"""

from __future__ import annotations

from . import core
from .engine import StrategyEngine
from .nuclear_typed_engine import NuclearTypedEngine
from .tecl_strategy_engine import TECLStrategyEngine
from .typed_klm_ensemble_engine import TypedKLMStrategyEngine
from ..managers.typed_strategy_manager import AggregatedSignals, TypedStrategyManager

__all__ = [
    "AggregatedSignals",
    "NuclearTypedEngine",
    "StrategyEngine",
    "TECLStrategyEngine",
    "TypedKLMStrategyEngine",
    "TypedStrategyManager",
    "core",
]
