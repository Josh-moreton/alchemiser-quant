"""DEPRECATED: NuclearTypedEngine moved to the_alchemiser.strategy.engines.

This module provides backward compatibility. Use:
    from the_alchemiser.strategy.engines.nuclear_typed_engine import NuclearTypedEngine
"""

import warnings
from the_alchemiser.strategy.engines.nuclear_typed_engine import NuclearTypedEngine

warnings.warn(
    "Importing from the_alchemiser.domain.strategies.nuclear_typed_engine is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.nuclear_typed_engine import NuclearTypedEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["NuclearTypedEngine"]
