#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio calculation utilities for allocation analysis and comparison.

This module provides shared calculation functions for portfolio allocation
analysis, avoiding duplication across modules. These utilities are used by
both CLI formatters and orchestrators for consistent allocation calculations.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def build_allocation_comparison(
    consolidated_portfolio: dict[str, float],
    account_dict: dict[str, Any],
    positions_dict: dict[str, float],
) -> dict[str, Any]:
    """Build allocation comparison between target and current portfolio states.

    Args:
        consolidated_portfolio: Target allocation percentages by symbol
        account_dict: Account information including portfolio_value
        positions_dict: Current positions with market values by symbol

    Returns:
        Dictionary containing:
        - target_values: Dict of symbol to target dollar values (Decimal)
        - current_values: Dict of symbol to current dollar values (Decimal)
        - deltas: Dict of symbol to dollar differences (Decimal)

    Raises:
        ValueError: If portfolio value cannot be determined

    """
    # Get portfolio value from account info
    portfolio_value = account_dict.get("portfolio_value")
    if portfolio_value is None:
        portfolio_value = account_dict.get("equity")

    if portfolio_value is None:
        raise ValueError(
            "Portfolio value not available in account info. "
            "Cannot calculate target allocation values without portfolio value."
        )

    # Convert portfolio_value to Decimal for precise calculations
    portfolio_value_decimal = Decimal(str(portfolio_value))

    # Calculate target values in dollars
    target_values = {}
    for symbol, weight in consolidated_portfolio.items():
        target_value = portfolio_value_decimal * Decimal(str(weight))
        target_values[symbol] = target_value

    # Convert current position values to Decimal
    current_values = {}
    for symbol, market_value in positions_dict.items():
        current_values[symbol] = Decimal(str(market_value))

    # Calculate deltas (target - current)
    all_symbols = set(target_values.keys()) | set(current_values.keys())
    deltas = {}
    for symbol in all_symbols:
        target_val = target_values.get(symbol, Decimal("0"))
        current_val = current_values.get(symbol, Decimal("0"))
        deltas[symbol] = target_val - current_val

    return {
        "target_values": target_values,
        "current_values": current_values,
        "deltas": deltas,
    }
