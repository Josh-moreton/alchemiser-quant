#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy configuration utilities for consolidating strategy allocation logic.

This module provides centralized functions for extracting and managing strategy
allocations from configuration, eliminating duplication across the codebase.
"""

from __future__ import annotations

from the_alchemiser.shared.types.strategy_types import StrategyType


def get_strategy_allocations() -> dict[StrategyType, float]:
    """Get strategy allocations with safe defaults.

    This function consolidates the strategy allocation extraction logic that was
    previously duplicated across main.py and trading_executor.py.

    Returns:
        Dictionary mapping StrategyType to allocation percentages

    Example:
        >>> allocations = get_strategy_allocations()
        >>> print(allocations[StrategyType.DSL])
        1.0

    """
    # For this DSL-focused PR, only return DSL allocation
    return {
        StrategyType.DSL: 1.0,
    }
