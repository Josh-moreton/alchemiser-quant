"""Business Unit: strategy | Status: current.

Core strategy execution engines and orchestration.

This module contains high-level strategy orchestration engines that coordinate
signal generation, execution, and portfolio management across multiple strategies.
"""

from __future__ import annotations

from .trading_engine import TradingEngine

__all__ = [
    "TradingEngine",
]
