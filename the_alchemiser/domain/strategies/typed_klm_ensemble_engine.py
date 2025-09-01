"""DEPRECATED: TypedKLMStrategyEngine moved to the_alchemiser.strategy.engines.

This module provides backward compatibility. Use:
    from the_alchemiser.strategy.engines.typed_klm_ensemble_engine import TypedKLMStrategyEngine
"""

import warnings
from the_alchemiser.strategy.engines.typed_klm_ensemble_engine import TypedKLMStrategyEngine

warnings.warn(
    "Importing from the_alchemiser.domain.strategies.typed_klm_ensemble_engine is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.typed_klm_ensemble_engine import TypedKLMStrategyEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TypedKLMStrategyEngine"]
