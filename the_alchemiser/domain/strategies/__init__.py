"""Business Unit: strategy | Status: legacy.

DEPRECATED: Strategy engines have moved to the_alchemiser.strategy.engines.

This module provides backward compatibility shims that redirect imports
to the new strategy module location. Use the new imports for new code:

    from the_alchemiser.strategy.engines import ...

This module will be removed in a future version.
"""

from __future__ import annotations

import warnings

# Import from new location and re-export all strategy components
from the_alchemiser.strategy.engines.engine import StrategyEngine
from the_alchemiser.strategy.engines.nuclear_logic import *
from the_alchemiser.strategy.engines.nuclear_typed_engine import NuclearTypedEngine
from the_alchemiser.strategy.engines.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.strategy.engines.typed_klm_ensemble_engine import TypedKLMStrategyEngine
from the_alchemiser.strategy.engines.typed_strategy_manager import TypedStrategyManager

# Issue deprecation warning
warnings.warn(
    "Importing from the_alchemiser.domain.strategies is deprecated. "
    "Use 'from the_alchemiser.strategy.engines import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "StrategyEngine", 
    "NuclearTypedEngine",
    "TECLStrategyEngine", 
    "TypedKLMStrategyEngine",
    "TypedStrategyManager",
]
