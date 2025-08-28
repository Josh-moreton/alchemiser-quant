#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Dashboard Data Utilities.

This module provides helper functions for building structured data
for dashboard consumption, including portfolio metrics, positions,
and performance data.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.domain.types import AccountInfo, PositionInfo


def build_basic_dashboard_structure(paper_trading: bool) -> dict[str, Any]:
    """Build basic dashboard data structure.

    Args:
        paper_trading: Whether using paper trading mode

    Returns:
        Dict with empty dashboard structure

    """
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "execution_mode": "PAPER" if paper_trading else "LIVE",
        "success": False,
        "strategies": {},
        "portfolio": {
            "total_value": 0,
            "total_pl": 0,
            "total_pl_percent": 0,
            "daily_pl": 0,
            "daily_pl_percent": 0,
            "cash": 0,
            "equity": 0,
        },
        "positions": [],
        "recent_trades": [],
        "signals": {},
        "performance": {"last_30_days": {}, "last_7_days": {}, "today": {}},
    }


def extract_portfolio_metrics(account_info: AccountInfo | dict[str, Any]) -> dict[str, float]:
    """Extract portfolio metrics from account information.

    Args:
        account_info: Account information dictionary

    Returns:
        Dict with portfolio metrics

    """
    if not account_info:
        return {}

    portfolio_metrics = {
        "total_value": float(account_info.get("equity", 0)),
        "cash": float(account_info.get("cash", 0)),
        "equity": float(account_info.get("equity", 0)),
    }

    # Extract P&L from portfolio history if available
    portfolio_history = (
        account_info.get("portfolio_history", {})
        if isinstance(account_info, dict)
        else getattr(account_info, "portfolio_history", {})
    )
    if portfolio_history and isinstance(portfolio_history, dict):
        profit_loss = portfolio_history.get("profit_loss", [])
        profit_loss_pct = portfolio_history.get("profit_loss_pct", [])
        if profit_loss:
            latest_pl = profit_loss[-1]  # Sonar: remove tautology
            latest_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
            portfolio_metrics.update(
                {"daily_pl": float(latest_pl), "daily_pl_percent": float(latest_pl_pct) * 100}
            )

    return portfolio_metrics


def extract_positions_data(
    open_positions: list[PositionInfo] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract positions data for dashboard.

    Args:
        open_positions: List of position objects

    Returns:
        List of position dictionaries

    """
    positions_data = []
    for position in open_positions:
        try:
            positions_data.append(
                {
                    "symbol": getattr(position, "symbol", ""),
                    "quantity": float(getattr(position, "qty", 0)),
                    "market_value": float(getattr(position, "market_value", 0)),
                    "unrealized_pl": float(getattr(position, "unrealized_pl", 0)),
                    "unrealized_pl_percent": float(getattr(position, "unrealized_plpc", 0)) * 100,
                    "current_price": float(getattr(position, "current_price", 0)),
                    "avg_entry_price": float(getattr(position, "avg_entry_price", 0)),
                    "side": getattr(position, "side", "long"),
                    "change_today": float(getattr(position, "change_today", 0)),
                }
            )
        except (AttributeError, ValueError, TypeError) as e:
            logging.warning(f"Error extracting position data: {e}")
            continue

    return positions_data


def extract_strategies_data(
    strategy_signals: dict[str, Any], strategy_allocations: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Extract strategies data for dashboard.

    Args:
        strategy_signals: Strategy signals from execution
        strategy_allocations: Strategy allocation weights

    Returns:
        Dict mapping strategy names to strategy data

    """
    strategies_data = {}
    for strategy_type, signal_data in strategy_signals.items():
        strategy_name = (
            strategy_type.value if hasattr(strategy_type, "value") else str(strategy_type)
        )
        strategies_data[strategy_name] = {
            "signal": signal_data.get("action", "HOLD"),
            "symbol": signal_data.get("symbol", ""),
            "reason": signal_data.get("reason", ""),
            "timestamp": signal_data.get("timestamp", datetime.now(UTC).isoformat()),
            "allocation": strategy_allocations.get(strategy_type, 0),
        }

    return strategies_data


def extract_recent_trades_data(
    orders_executed: list[dict[str, Any]], limit: int = 10
) -> list[dict[str, Any]]:
    """Extract recent trades data for dashboard.

    Args:
        orders_executed: List of executed orders
        limit: Maximum number of trades to return

    Returns:
        List of trade dictionaries

    """
    recent_trades = []
    for order in orders_executed[-limit:]:
        try:
            recent_trades.append(
                {
                    "symbol": order.get("symbol", ""),
                    "side": order.get("side", ""),
                    "quantity": float(order.get("qty", 0)),
                    "price": float(order.get("price", 0)),
                    "value": float(order.get("estimated_value", 0)),
                    "timestamp": order.get("timestamp", datetime.now(UTC).isoformat()),
                    "status": order.get("status", "executed"),
                }
            )
        except (ValueError, TypeError) as e:
            logging.warning(f"Error extracting trade data: {e}")
            continue

    return recent_trades


def build_s3_paths(paper_trading: bool) -> tuple[str, str]:
    """Build S3 paths for dashboard data storage.

    Args:
        paper_trading: Whether using paper trading

    Returns:
        Tuple of (latest_path, historical_path)

    """
    if paper_trading:
        latest_path = "s3://the-alchemiser-s3/dashboard/latest_paper_execution.json"
        mode_str = "paper"
    else:
        latest_path = "s3://the-alchemiser-s3/dashboard/latest_execution.json"
        mode_str = "live"

    historical_path = (
        f"s3://the-alchemiser-s3/dashboard/executions/{mode_str}/"
        f"{datetime.now(UTC).strftime('%Y/%m/%d')}/execution_{datetime.now(UTC).strftime('%H%M%S')}.json"
    )

    return latest_path, historical_path
