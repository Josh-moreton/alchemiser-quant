"""Business Unit: strategy & signal generation; Status: legacy

DEPRECATED: Strategy position model using domain value objects.

This file is deprecated. Use the canonical StrategyPosition from 
strategy.types.strategy instead. All functionality has been moved there.
"""

# Import from canonical location for backward compatibility
from the_alchemiser.strategy.types.strategy import StrategyPosition as StrategyPositionModel

__all__ = ["StrategyPositionModel"]
