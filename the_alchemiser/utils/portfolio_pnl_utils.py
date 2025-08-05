#!/usr/bin/env python3
"""
Portfolio P&L Utilities

This module provides helper functions for calculating and extracting
profit and loss data from strategy tracking and portfolio positions.
"""

import logging
from typing import Any

from the_alchemiser.tracking.strategy_order_tracker import get_strategy_tracker

# TODO: Phase 12 - Types available for future migration to structured performance data
# from the_alchemiser.core.types import PerformanceMetrics, PortfolioSnapshot, StrategyPnLSummary, TradeAnalysis


def calculate_strategy_pnl_summary(
    paper_trading: bool, current_prices: dict[str, float]
) -> dict[str, Any]:
    """
    Calculate P&L summary for all strategies.

    Args:
        paper_trading: Whether using paper trading
        current_prices: Dict mapping symbols to current prices

    Returns:
        Dict containing P&L summary with totals and per-strategy data
    """
    try:
        tracker = get_strategy_tracker(paper_trading=paper_trading)
        all_strategy_pnl = tracker.get_all_strategy_pnl(current_prices)

        # Calculate overall totals
        total_realized_pnl = sum(pnl.realized_pnl for pnl in all_strategy_pnl.values())
        total_unrealized_pnl = sum(pnl.unrealized_pnl for pnl in all_strategy_pnl.values())
        total_pnl = total_realized_pnl + total_unrealized_pnl
        total_allocation_value = sum(pnl.allocation_value for pnl in all_strategy_pnl.values())

        return {
            "all_strategy_pnl": all_strategy_pnl,
            "summary": {
                "total_realized_pnl": round(total_realized_pnl, 2),
                "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                "total_pnl": round(total_pnl, 2),
                "total_allocation_value": round(total_allocation_value, 2),
            },
        }
    except Exception as e:
        logging.warning(f"Failed to calculate strategy P&L: {e}")
        return {
            "all_strategy_pnl": {},
            "summary": {
                "total_realized_pnl": 0.0,
                "total_unrealized_pnl": 0.0,
                "total_pnl": 0.0,
                "total_allocation_value": 0.0,
            },
        }


def extract_trading_summary(orders_executed: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Extract trading summary from executed orders.

    Args:
        orders_executed: List of executed order dictionaries

    Returns:
        Dict containing trading summary statistics
    """
    total_trades = len(orders_executed)
    buy_orders: list[dict[str, Any]] = (
        []
    )  # TODO: Phase 12 - Consider migrating to OrderDetails type
    sell_orders: list[dict[str, Any]] = (
        []
    )  # TODO: Phase 12 - Consider migrating to OrderDetails type

    for order in orders_executed:
        side = order.get("side")
        if side:
            if hasattr(side, "value"):
                side_value = side.value.upper()
            else:
                side_value = str(side).upper()
            if side_value == "BUY":
                buy_orders.append(order)
            elif side_value == "SELL":
                sell_orders.append(order)

    total_buy_value = sum(o.get("estimated_value", 0) for o in buy_orders)
    total_sell_value = sum(o.get("estimated_value", 0) for o in sell_orders)

    return {
        "total_trades": total_trades,
        "buy_orders": len(buy_orders),
        "sell_orders": len(sell_orders),
        "total_buy_value": total_buy_value,
        "total_sell_value": total_sell_value,
    }


def build_strategy_summary(
    strategy_signals: dict[str, Any],
    strategy_allocations: dict[str, Any],
    all_strategy_pnl: dict[str, Any],
) -> dict[str, Any]:
    """
    Build strategy summary with P&L data.

    Args:
        strategy_signals: Strategy signals from execution
        strategy_allocations: Strategy allocation weights
        all_strategy_pnl: P&L data for all strategies

    Returns:
        Dict mapping strategy names to summary data
    """
    strategy_summary = {}

    for strategy_type, signal_data in strategy_signals.items():
        strategy_name = (
            strategy_type.value if hasattr(strategy_type, "value") else str(strategy_type)
        )

        # Get P&L data for this strategy
        strategy_pnl = all_strategy_pnl.get(strategy_type)
        pnl_data = {}
        if strategy_pnl:
            pnl_data = {
                "realized_pnl": round(strategy_pnl.realized_pnl, 2),
                "unrealized_pnl": round(strategy_pnl.unrealized_pnl, 2),
                "total_pnl": round(strategy_pnl.total_pnl, 2),
                "allocation_value": round(strategy_pnl.allocation_value, 2),
                "positions": strategy_pnl.positions,
            }

        strategy_summary[strategy_name] = {
            "signal": signal_data.get("action", "HOLD"),
            "symbol": signal_data.get("symbol", "N/A"),
            "allocation": strategy_allocations.get(strategy_type, 0.0),
            **pnl_data,
        }

    return strategy_summary


def build_allocation_summary(
    consolidated_portfolio: dict[str, float],
) -> dict[str, dict[str, float]]:
    """
    Build allocation summary from consolidated portfolio.

    Args:
        consolidated_portfolio: Dict mapping symbols to weights

    Returns:
        Dict mapping symbols to allocation data
    """
    return {
        symbol: {"target_percent": weight * 100}
        for symbol, weight in consolidated_portfolio.items()
    }
