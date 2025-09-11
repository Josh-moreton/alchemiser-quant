#!/usr/bin/env python3
"""Business Unit: strategy | Status: legacy

Compatibility shim for moved KLM engine.

This module provides backward compatibility for imports of the KLM engine
which has been moved to strategy_v2. This shim will be removed in a future release.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "Importing KLM engine from strategy.engines.klm is deprecated. "
    "Use strategy_v2.engines.klm instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location
from the_alchemiser.strategy_v2.engines.klm.engine import KLMEngine

__all__ = ["KLMEngine"]