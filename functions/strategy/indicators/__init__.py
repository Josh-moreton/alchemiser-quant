"""Business Unit: strategy | Status: current.

Technical indicators and market signals.

This module contains technical analysis indicators used by trading strategies
for signal generation and market analysis.
"""

from __future__ import annotations

from indicators.indicator_utils import FALLBACK_INDICATOR_VALUE, safe_get_indicator
from indicators.indicators import TechnicalIndicators

__all__ = [
    "FALLBACK_INDICATOR_VALUE",
    "TechnicalIndicators",
    "safe_get_indicator",
]
