"""DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.application.portfolio.services.portfolio_rebalancing_service' is deprecated. "
    "Use 'from the_alchemiser.portfolio.allocation import portfolio_rebalancing_service' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import all symbols from the new location
from the_alchemiser.portfolio.allocation.portfolio_rebalancing_service import *
