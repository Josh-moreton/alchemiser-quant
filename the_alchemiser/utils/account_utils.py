#!/usr/bin/env python3
"""
Account Data Utilities

This module provides helper functions for extracting and processing account information
from data providers, including portfolio values, P&L calculations, and position data.
"""

import logging
from typing import Any


def extract_comprehensive_account_data(data_provider) -> dict[str, Any]:
    """
    Extract comprehensive account information from a data provider.

    Args:
        data_provider: UnifiedDataProvider instance

    Returns:
        Dict containing comprehensive account information including:
        - Basic account data (equity, cash, buying_power, etc.)
        - Portfolio history and P&L data
        - Open positions
        - Recent closed positions P&L
    """
    try:
        account = data_provider.get_account_info()
        if not account:
            return {}

        portfolio_history = data_provider.get_portfolio_history()
        open_positions = data_provider.get_open_positions()

        # Get recent closed position P&L
        recent_closed_pnl = data_provider.get_recent_closed_positions_pnl(days_back=7)

        return {
            "account_number": getattr(account, "account_number", "N/A"),
            "portfolio_value": float(getattr(account, "portfolio_value", 0) or 0),
            "equity": float(getattr(account, "equity", 0) or 0),
            "buying_power": float(getattr(account, "buying_power", 0) or 0),
            "cash": float(getattr(account, "cash", 0) or 0),
            "day_trade_count": getattr(account, "day_trade_count", 0),
            "status": getattr(account, "status", "unknown"),
            "portfolio_history": portfolio_history,
            "open_positions": open_positions,
            "recent_closed_pnl": recent_closed_pnl,
        }
    except Exception as e:
        logging.error(f"Error extracting account data: {e}")
        return {}


def extract_basic_account_metrics(account_info: dict[str, Any]) -> dict[str, float]:
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


def calculate_portfolio_values(
    target_portfolio: dict[str, float], account_info: dict[str, Any]
) -> dict[str, float]:
    """
    Calculate target dollar values from portfolio weights.

    Args:
        target_portfolio: Dictionary mapping symbols to target weights (0.0-1.0)
        account_info: Account information containing portfolio_value

    Returns:
        Dictionary mapping symbols to target dollar values
    """
    portfolio_value = account_info.get("portfolio_value", 0.0)
    return {symbol: portfolio_value * weight for symbol, weight in target_portfolio.items()}


def extract_current_position_values(current_positions: dict[str, Any]) -> dict[str, float]:
    """
    Extract current market values from position objects.

    Args:
        current_positions: Dictionary mapping symbols to position objects

    Returns:
        Dictionary mapping symbols to current market values
    """
    current_values = {}
    for symbol, pos in current_positions.items():
        try:
            if isinstance(pos, dict):
                current_values[symbol] = float(pos.get("market_value", 0.0))
            else:
                current_values[symbol] = float(getattr(pos, "market_value", 0.0))
        except (ValueError, TypeError, AttributeError):
            current_values[symbol] = 0.0
    return current_values
