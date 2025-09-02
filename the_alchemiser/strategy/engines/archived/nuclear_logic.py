"""DEPRECATED: Nuclear strategy logic moved to the_alchemiser.strategy.engines.

This module provides backward compatibility. Use:
    from the_alchemiser.strategy.engines.nuclear_logic import *
"""

import warnings

from the_alchemiser.strategy.engines.nuclear_logic import *

warnings.warn(
    "Importing from the_alchemiser.domain.strategies.nuclear_logic is deprecated. "
    "Use 'from the_alchemiser.strategy.engines.nuclear_logic import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)
