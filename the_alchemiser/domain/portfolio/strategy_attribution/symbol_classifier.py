"""
DEPRECATED: This module has moved to the_alchemiser.portfolio.state
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.domain.portfolio.strategy_attribution.symbol_classifier' is deprecated. "
    "Use 'from the_alchemiser.portfolio.state import symbol_classifier' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import all symbols from the new location
from the_alchemiser.portfolio.state.symbol_classifier import *