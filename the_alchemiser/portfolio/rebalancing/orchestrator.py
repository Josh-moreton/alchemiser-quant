"""DEPRECATED: This module has moved to the_alchemiser.portfolio.core
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.application.portfolio.rebalancing_orchestrator' is deprecated. "
    "Use 'from the_alchemiser.portfolio.core import rebalancing_orchestrator' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import all symbols from the new location
from the_alchemiser.portfolio.core.rebalancing_orchestrator import *
