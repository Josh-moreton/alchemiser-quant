"""DEPRECATED: Strategy value objects moved to the_alchemiser.strategy.engines.value_objects.

This module provides backward compatibility.
"""

from the_alchemiser.strategy.engines.value_objects.strategy_signal import *

import warnings
warnings.warn(
    "Importing from the_alchemiser.domain.strategies.value_objects.strategy_signal is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.value_objects.strategy_signal import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)