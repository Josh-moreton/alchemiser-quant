#!/usr/bin/env python3
"""Business Unit: portfolio assessment & management; Status: current.

Portfolio calculation utilities extracted from TradingEngine.

This module provides calculation functions for portfolio target vs current allocations
without any display logic, supporting the separation of business logic from presentation.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.domain.types import AccountInfo
from the_alchemiser.portfolio.application.account_utils import (
    calculate_position_target_deltas,
    extract_current_position_values,
)


def calculate_target_vs_current_allocations(
    target_portfolio: dict[str, float],
    account_info: AccountInfo | dict[str, Any],
    current_positions: dict[str, Any],
) -> tuple[dict[str, float], dict[str, float]]:
    """Calculate target vs current allocations without display.

    Shows a comparison between target portfolio weights and current position values,
    helping to visualize rebalancing needs.

    Args:
        target_portfolio: Target allocation weights by symbol.
        account_info: Account information including portfolio value.
        current_positions: Current position data by symbol.

    Returns:
        Tuple containing:
            - target_values: Target dollar values by symbol
            - current_values: Current market values by symbol

    """

    # Use helper functions to calculate values
    # Accept both legacy display shape and typed AccountInfo
    def _to_float(v: Any, default: float = 0.0) -> float:
        try:
            if v is None:
                return default
            return float(v)
        except (TypeError, ValueError):
            return default

    def _to_int(v: Any, default: int = 0) -> int:
        try:
            if v is None:
                return default
            return int(v)
        except (TypeError, ValueError):
            return default

    # Safely derive day_trades_remaining from either key
    day_trades_remaining_val = 0
    if isinstance(account_info, dict):
        v1 = account_info.get("day_trades_remaining")
        v2 = account_info.get("day_trade_count")
        for _v in (v1, v2):
            day_trades_remaining_val = _to_int(_v, 0)
            if day_trades_remaining_val != 0:
                break

    account_info_typed: AccountInfo = {
        "account_id": str(
            (account_info.get("account_id") if isinstance(account_info, dict) else None)
            or (account_info.get("account_number") if isinstance(account_info, dict) else None)
            or "unknown"
        ),
        "equity": _to_float(account_info.get("equity", 0.0), 0.0),
        "cash": _to_float(account_info.get("cash", 0.0), 0.0),
        "buying_power": _to_float(account_info.get("buying_power", 0.0), 0.0),
        "day_trades_remaining": day_trades_remaining_val,
        "portfolio_value": _to_float(account_info.get("portfolio_value", 0.0), 0.0),
        "last_equity": _to_float(account_info.get("last_equity", 0.0), 0.0),
        "daytrading_buying_power": _to_float(account_info.get("daytrading_buying_power", 0.0), 0.0),
        "regt_buying_power": _to_float(account_info.get("regt_buying_power", 0.0), 0.0),
        "status": (
            "ACTIVE"
            if str(account_info.get("status", "INACTIVE")).upper() == "ACTIVE"
            else "INACTIVE"
        ),
    }
    target_values = calculate_position_target_deltas(target_portfolio, account_info_typed)
    current_values = extract_current_position_values(current_positions)

    return target_values, current_values
