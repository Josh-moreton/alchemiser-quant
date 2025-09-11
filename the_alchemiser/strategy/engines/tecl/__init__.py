#!/usr/bin/env python3
"""Business Unit: strategy | Status: legacy

Compatibility shim for moved TECL engine.

This module provides backward compatibility for imports of the TECL engine
which has been moved to strategy_v2. This shim will be removed in a future release.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "Importing TECL engine from strategy.engines.tecl is deprecated. "
    "Use strategy_v2.engines.tecl instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location  
from the_alchemiser.strategy_v2.engines.tecl.engine import TECLEngine

__all__ = ["TECLEngine"]