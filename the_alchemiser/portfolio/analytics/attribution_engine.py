"""DEPRECATED: This module has moved to the_alchemiser.portfolio.state
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.domain.portfolio.strategy_attribution.attribution_engine' is deprecated. "
    "Use 'from the_alchemiser.portfolio.state import attribution_engine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import all symbols from the new location
from the_alchemiser.portfolio.state.attribution_engine import *
