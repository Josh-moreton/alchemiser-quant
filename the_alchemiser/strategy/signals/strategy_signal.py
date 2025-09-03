"""DEPRECATED: Strategy value objects moved to the_alchemiser.strategy.engines.value_objects.

This module provides backward compatibility.
"""

import warnings

from the_alchemiser.strategy.engines.value_objects.strategy_signal import *

warnings.warn(
    "Importing from the_alchemiser.strategy.signals.strategy_signal is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.value_objects.strategy_signal import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)
