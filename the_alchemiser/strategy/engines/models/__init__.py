"""Business Unit: strategy | Status: legacy.

Legacy strategy domain models package - DEPRECATED.

This package is deprecated. Use the canonical types from strategy.types instead.
All functionality has been consolidated into strategy.types.strategy module.
"""

from __future__ import annotations

# Import from canonical location for backward compatibility
from the_alchemiser.strategy.types.strategy import StrategyPosition as StrategyPositionModel
from the_alchemiser.strategy.types.strategy import StrategySignal as StrategySignalModel

__all__ = [
    "StrategyPositionModel",
    "StrategySignalModel",
]
