"""Signal processing and generation.

Business Unit: strategy | Status: current

Strategy signal generation and processing.
"""

from __future__ import annotations

# Re-export from canonical location
from ..engines.value_objects.strategy_signal import Action, StrategySignal

__all__ = [
    "Action",
    "StrategySignal",
]
