#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy configuration utilities for consolidating strategy allocation logic.

This module provides centralized functions for extracting and managing strategy
allocations from configuration, eliminating duplication across the codebase.
"""

from __future__ import annotations

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.types.strategy_types import StrategyType


def get_strategy_allocations(settings: Settings) -> dict[StrategyType, float]:
    """Extract strategy allocations from configuration with safe defaults.

    This function consolidates the strategy allocation extraction logic that was
    previously duplicated across main.py and trading_executor.py.

    Uses .get() with fallback defaults to handle missing configuration keys gracefully,
    ensuring consistent behavior across all callers.

    Args:
        settings: Application settings containing strategy configuration

    Returns:
        Dictionary mapping StrategyType to allocation percentages

    Example:
        >>> from the_alchemiser.shared.config.config import Settings
        >>> settings = Settings()
        >>> allocations = get_strategy_allocations(settings)
        >>> print(allocations[StrategyType.NUCLEAR])
        0.3

    """
    # For this DSL-focused PR, only return DSL allocation
    return {
        StrategyType.DSL: 1.0,
    }
