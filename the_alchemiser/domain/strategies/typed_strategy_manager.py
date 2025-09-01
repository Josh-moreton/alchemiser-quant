"""DEPRECATED: TypedStrategyManager moved to the_alchemiser.strategy.engines.

This module provides backward compatibility. Use:
    from the_alchemiser.strategy.engines.typed_strategy_manager import TypedStrategyManager, AggregatedSignals
"""

import warnings
from the_alchemiser.strategy.engines.typed_strategy_manager import TypedStrategyManager, AggregatedSignals

warnings.warn(
    "Importing from the_alchemiser.domain.strategies.typed_strategy_manager is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.typed_strategy_manager import TypedStrategyManager, AggregatedSignals' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TypedStrategyManager", "AggregatedSignals"]
