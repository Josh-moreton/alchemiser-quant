"""Business Unit: strategy & signal generation; Status: legacy

DEPRECATED: Strategy signal model using domain value objects.

This file is deprecated. Use the canonical StrategySignal from
strategy.types.strategy instead. All functionality has been moved there.
"""

# Import from canonical location for backward compatibility
from the_alchemiser.strategy.types.strategy import StrategySignal as StrategySignalModel

__all__ = ["StrategySignalModel"]
