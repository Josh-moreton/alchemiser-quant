"""
DEPRECATED: This module has moved to the_alchemiser.portfolio.core
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.application.portfolio.services.portfolio_management_facade' is deprecated. "
    "Use 'from the_alchemiser.portfolio.core import portfolio_management_facade' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import all symbols from the new location
from the_alchemiser.portfolio.core.portfolio_management_facade import *