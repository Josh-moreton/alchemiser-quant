"""
DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.domain.portfolio.rebalancing.rebalance_plan' is deprecated. "
    "Use 'from the_alchemiser.portfolio.allocation import rebalance_plan' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import all symbols from the new location
from the_alchemiser.portfolio.allocation.rebalance_plan import *