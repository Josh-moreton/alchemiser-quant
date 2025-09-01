"""DEPRECATED: TECLStrategyEngine moved to the_alchemiser.strategy.engines.

This module provides backward compatibility. Use:
    from the_alchemiser.strategy.engines.tecl_strategy_engine import TECLStrategyEngine
"""

import warnings
from the_alchemiser.strategy.engines.tecl_strategy_engine import TECLStrategyEngine

warnings.warn(
    "Importing from the_alchemiser.domain.strategies.tecl_strategy_engine is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.tecl_strategy_engine import TECLStrategyEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TECLStrategyEngine"]
