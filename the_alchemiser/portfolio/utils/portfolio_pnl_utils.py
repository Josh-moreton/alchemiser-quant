#!/usr/bin/env python3
"""DEPRECATED: This module has moved to the_alchemiser.portfolio.pnl
This shim maintains backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'the_alchemiser.application.portfolio.portfolio_pnl_utils' is deprecated. "
    "Use 'from the_alchemiser.portfolio.pnl import portfolio_pnl_utils' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import all symbols from the new location
from the_alchemiser.portfolio.pnl.portfolio_pnl_utils import *
