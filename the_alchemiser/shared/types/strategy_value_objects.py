"""Business Unit: shared | Status: deprecated.

DEPRECATED: This module is deprecated. Use the_alchemiser.shared.schemas.strategy_signal instead.

Strategy value objects used across modules.

This module previously defined StrategySignal, but it has been consolidated into
the canonical version in shared/schemas/strategy_signal.py which includes:
- Event-driven fields (correlation_id, causation_id) for traceability
- Schema versioning for event evolution
- Strong typing (Symbol, ActionLiteral) for type safety

This module now re-exports from the canonical location for backward compatibility.
It will be removed in version 3.0.0.

Migration Guide:
    Old: from the_alchemiser.shared.types import StrategySignal
    New: from the_alchemiser.shared.schemas import StrategySignal
"""

from __future__ import annotations

import warnings

# Re-export from canonical location for backward compatibility
from the_alchemiser.shared.schemas.strategy_signal import (
    ActionLiteral,
    StrategySignal,
)

# Issue deprecation warning
warnings.warn(
    "the_alchemiser.shared.types.strategy_value_objects is deprecated. "
    "Use the_alchemiser.shared.schemas.strategy_signal instead. "
    "This module will be removed in version 3.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["ActionLiteral", "StrategySignal"]
