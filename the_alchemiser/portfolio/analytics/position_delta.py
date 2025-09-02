"""
DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.domain.portfolio.position.position_delta' is deprecated. "
    "Use 'from the_alchemiser.portfolio.holdings import position_delta' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import all symbols from the new location
from the_alchemiser.portfolio.holdings.position_delta import *