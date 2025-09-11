#!/usr/bin/env python3
"""Business Unit: strategy | Status: legacy

Compatibility shim for moved Nuclear engine.

This module provides backward compatibility for imports of the Nuclear engine
which has been moved to strategy_v2. This shim will be removed in a future release.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "Importing Nuclear engine from strategy.engines.nuclear is deprecated. "
    "Use strategy_v2.engines.nuclear instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location
from the_alchemiser.strategy_v2.engines.nuclear.engine import NuclearEngine

__all__ = ["NuclearEngine"]