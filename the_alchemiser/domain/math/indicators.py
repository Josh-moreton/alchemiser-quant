"""Business Unit: utilities | Status: legacy.

DEPRECATED: Technical indicators have moved to the_alchemiser.strategy.indicators.

This module provides backward compatibility shims that redirect imports
to the new strategy module location. Use the new imports for new code:

    from the_alchemiser.strategy.indicators import TechnicalIndicators

This module will be removed in a future version.
"""

from __future__ import annotations

import warnings

# Import from new location and re-export
from the_alchemiser.strategy.indicators.indicators import TechnicalIndicators

# Issue deprecation warning
warnings.warn(
    "Importing from the_alchemiser.domain.math.indicators is deprecated. "
    "Use 'from the_alchemiser.strategy.indicators import TechnicalIndicators' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TechnicalIndicators"]