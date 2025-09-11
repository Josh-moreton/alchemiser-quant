#!/usr/bin/env python3
"""Business Unit: strategy | Status: legacy

Compatibility shim for moved indicators.

This module provides backward compatibility for imports of indicators
which have been moved to strategy_v2. This shim will be removed in a future release.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "Importing indicators from strategy.indicators is deprecated. "
    "Use strategy_v2.indicators instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location
from ...strategy_v2.indicators.indicators import TechnicalIndicators
from ...strategy_v2.indicators.indicator_utils import safe_get_indicator

__all__ = ["TechnicalIndicators", "safe_get_indicator"]