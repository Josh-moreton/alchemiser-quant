#!/usr/bin/env python3
"""
Account Data Utilities

This module provides helper functions for extracting and processing account information
from data providers, including portfolio values, P&L calculations, and position data.
"""

import logging
from typing import Any

from the_alchemiser.domain.types import AccountInfo, PositionInfo


def extract_comprehensive_account_data(data_provider: Any) -> AccountInfo:
    """
    Extract comprehensive account information from a data provider.

    Args:
        data_provider: Market data provider instance

    Returns:
        AccountInfo containing account information
    """
    try:
        account = data_provider.get_account_info()
        if not account:
            # Return default AccountInfo structure
            return {
                "account_id": "unknown",
                "equity": 0.0,
                "cash": 0.0,
                "buying_power": 0.0,
                "day_trades_remaining": 0,
                "portfolio_value": 0.0,
                "last_equity": 0.0,
                "daytrading_buying_power": 0.0,
                "regt_buying_power": 0.0,
                "status": "INACTIVE",
            }

        # Construct proper AccountInfo from account data
        # Handle both dict and object types for maximum compatibility
        def safe_get(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            else:
                return getattr(obj, key, default)

        return {
            "account_id": safe_get(account, "account_number", "unknown"),
            "equity": float(safe_get(account, "equity", 0) or 0),
            "cash": float(safe_get(account, "cash", 0) or 0),
            "buying_power": float(safe_get(account, "buying_power", 0) or 0),
            "day_trades_remaining": safe_get(account, "daytrade_count", 0),  # Fixed key name
            "portfolio_value": float(safe_get(account, "portfolio_value", 0) or 0),
            "last_equity": float(
                safe_get(account, "last_equity", safe_get(account, "equity", 0)) or 0
            ),  # Use last_equity if available, otherwise current equity
            "daytrading_buying_power": float(safe_get(account, "daytrading_buying_power", 0) or 0),
            "regt_buying_power": float(
                safe_get(account, "regt_buying_power", safe_get(account, "buying_power", 0)) or 0
            ),  # Use regt_buying_power if available, otherwise buying_power
            "status": (
                "ACTIVE"
                if str(safe_get(account, "status", "unknown")).upper() == "ACTIVE"
                else "INACTIVE"
            ),
        }
    except Exception as e:
        logging.error(f"Error extracting account data: {e}")
        # Return default AccountInfo structure on error
        return {
            "account_id": "error",
            "equity": 0.0,
            "cash": 0.0,
            "buying_power": 0.0,
            "day_trades_remaining": 0,
            "portfolio_value": 0.0,
            "last_equity": 0.0,
            "daytrading_buying_power": 0.0,
            "regt_buying_power": 0.0,
            "status": "INACTIVE",
        }


def extract_basic_account_metrics(account_info: AccountInfo) -> dict[str, float]:
    """
    Extract basic portfolio metrics from account info.

    Args:
        account_info: Account information dictionary

    Returns:
        Dict with portfolio_value, equity, cash, buying_power as floats
    """
    return {
        "portfolio_value": float(account_info.get("portfolio_value", 0)),
        "equity": float(account_info.get("equity", 0)),
        "cash": float(account_info.get("cash", 0)),
        "buying_power": float(account_info.get("buying_power", 0)),
    }


def calculate_position_target_deltas(
    target_portfolio: dict[str, float], account_info: AccountInfo
) -> dict[str, float]:
    """
    Calculate target dollar values from portfolio weights.

    Args:
        target_portfolio: Dictionary mapping symbols to target weights (0.0-1.0)
        account_info: Account information containing portfolio_value

    Returns:
        Dictionary mapping symbols to target dollar values
    """
    portfolio_value = float(account_info["portfolio_value"])
    return {symbol: portfolio_value * weight for symbol, weight in target_portfolio.items()}


def extract_current_position_values(current_positions: dict[str, PositionInfo]) -> dict[str, float]:
    """
    Extract current market values from position objects.

    Args:
        current_positions: Dictionary mapping symbols to position objects

    Returns:
        Dictionary mapping symbols to current market values
    """
    current_values: dict[str, float] = {}
    for symbol, pos in current_positions.items():
        try:
            current_values[symbol] = float(pos["market_value"])
        except (ValueError, TypeError, KeyError):
            current_values[symbol] = 0.0
    return current_values
