"""Business Unit: shared | Status: current.

Math utilities and helpers for shared computations.

This module provides mathematical and statistical functions used across
the trading system, including:
- Statistical calculations (moving averages, volatility, ensemble scoring)
- Trading calculations (position sizing, rebalancing, limit pricing)
- Numerical utilities (safe float comparison, division, normalization)
- Asset metadata (fractionability detection, asset classification)
"""

from __future__ import annotations

# Asset metadata utilities
from .asset_info import AssetType, FractionabilityDetector

# Statistical and mathematical utilities
from .math_utils import (
    calculate_ensemble_score,
    calculate_moving_average,
    calculate_moving_average_return,
    calculate_percentage_change,
    calculate_rolling_metric,
    calculate_stdev_returns,
    normalize_to_range,
    safe_division,
)

# Float comparison utilities
from .num import floats_equal

# Trading-specific calculations
from .trading_math import (
    TickSizeProvider,
    calculate_allocation_discrepancy,
    calculate_dynamic_limit_price,
    calculate_dynamic_limit_price_with_symbol,
    calculate_position_size,
    calculate_slippage_buffer,
)

__all__ = [
    "AssetType",
    "FractionabilityDetector",
    "TickSizeProvider",
    "calculate_allocation_discrepancy",
    "calculate_dynamic_limit_price",
    "calculate_dynamic_limit_price_with_symbol",
    "calculate_ensemble_score",
    "calculate_moving_average",
    "calculate_moving_average_return",
    "calculate_percentage_change",
    "calculate_position_size",
    "calculate_rolling_metric",
    "calculate_slippage_buffer",
    "calculate_stdev_returns",
    "floats_equal",
    "normalize_to_range",
    "safe_division",
]
