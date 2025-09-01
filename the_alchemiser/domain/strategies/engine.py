"""DEPRECATED: Strategy engine base class moved to the_alchemiser.strategy.engines.

This module provides backward compatibility. Use:
    from the_alchemiser.strategy.engines.engine import StrategyEngine
"""

import warnings
from the_alchemiser.strategy.engines.engine import StrategyEngine

warnings.warn(
    "Importing from the_alchemiser.domain.strategies.engine is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.engine import StrategyEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["StrategyEngine"]