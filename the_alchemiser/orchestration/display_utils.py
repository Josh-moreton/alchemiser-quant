#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Trading workflow display utilities for tracking and reporting.

Provides formatting and display functions for trading workflow results including
signals summary, rebalance plans, and execution tracking. These are used when
show_tracking is enabled in programmatic execution.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.constants import (
    NO_TRADES_REQUIRED,
    REBALANCE_PLAN_GENERATED,
)
from the_alchemiser.shared.logging.logging_utils import get_logger

logger = get_logger(__name__)


def display_signals_summary(signals_result: dict[str, Any]) -> None:
    """Display a brief summary of generated signals and target allocations.

    Args:
        signals_result: Dictionary containing strategy signals and consolidated portfolio

    """
    try:
        _display_strategy_signals(signals_result)
        _display_target_allocations(signals_result)
    except Exception as e:
        logger.warning(f"Failed to display signals summary: {e}")


def _display_strategy_signals(signals_result: dict[str, Any]) -> None:
    """Display individual strategy signals with their recommended symbols."""
    strategy_signals = signals_result.get("strategy_signals", {})
    if not isinstance(strategy_signals, dict):
        return

    signal_details = []
    for raw_name, data in strategy_signals.items():
        signal_detail = _process_strategy_signal(raw_name, data)
        if signal_detail:
            signal_details.append(signal_detail)

    if signal_details:
        print("\n📡 Strategy Signals:")
        for detail in signal_details:
            print(f"  • {detail}")


def _process_strategy_signal(raw_name: object, data: object) -> str | None:
    """Process a single strategy signal and return formatted string."""
    if not isinstance(data, dict):
        return None

    name = _clean_strategy_name(str(raw_name))
    action = str(data.get("action", "")).upper()

    if action == "HOLD":
        return f"{name}: {action}"

    if action in {"BUY", "SELL"}:
        return _format_buy_sell_signal(name, action, data)

    return None


def _clean_strategy_name(name: str) -> str:
    """Clean strategy name by removing StrategyType prefix if present."""
    if name.startswith("StrategyType."):
        return name.split(".", 1)[1]
    return name


def _format_buy_sell_signal(name: str, action: str, data: dict[str, Any]) -> str:
    """Format BUY/SELL signal with symbol information."""
    if _is_multi_symbol_signal(data):
        return _format_multi_symbol_signal(name, action, data)
    return _format_single_symbol_signal(name, action, data)


def _is_multi_symbol_signal(data: dict[str, Any]) -> bool:
    """Check if signal involves multiple symbols."""
    return bool(data.get("is_multi_symbol")) and isinstance(data.get("symbols"), list)


def _format_multi_symbol_signal(name: str, action: str, data: dict[str, Any]) -> str:
    """Format signal for multiple symbols."""
    symbols = data.get("symbols", [])
    if symbols:
        symbol_str = ", ".join(symbols)
        return f"{name}: {action} {symbol_str}"
    return f"{name}: {action} (no symbols)"


def _format_single_symbol_signal(name: str, action: str, data: dict[str, Any]) -> str:
    """Format signal for single symbol."""
    symbol = data.get("symbol")
    if isinstance(symbol, str) and symbol.strip():
        return f"{name}: {action} {symbol}"
    return f"{name}: {action} (no symbol info)"


def _display_target_allocations(signals_result: dict[str, Any]) -> None:
    """Display consolidated portfolio target allocations."""
    consolidated_portfolio = signals_result.get("consolidated_portfolio", {})
    if not isinstance(consolidated_portfolio, dict):
        return

    target_allocations = consolidated_portfolio.get("target_allocations", {})
    if not (isinstance(target_allocations, dict) and target_allocations):
        return

    print("\n🎯 Target Portfolio Allocations:")
    for symbol, allocation in target_allocations.items():
        if isinstance(allocation, (int, float)) and allocation > 0:
            print(f"  • {symbol}: {allocation:.1%}")


def display_rebalance_plan(trading_result: dict[str, Any]) -> None:
    """Display rebalance plan details if a plan was generated.

    Args:
        trading_result: Dictionary containing trading execution results

    """
    try:
        status = trading_result.get("status", "")

        if status in {REBALANCE_PLAN_GENERATED, NO_TRADES_REQUIRED}:
            rebalance_plan = trading_result.get("rebalance_plan", {})

            if isinstance(rebalance_plan, dict):
                trades = rebalance_plan.get("trades", [])

                if trades:
                    print(f"\n⚖️  Rebalance Plan ({len(trades)} trades):")
                    for trade in trades:
                        if isinstance(trade, dict):
                            symbol = trade.get("symbol", "Unknown")
                            action = str(trade.get("side", "")).upper()
                            quantity = trade.get("qty", 0)
                            print(f"  • {action} {quantity} shares of {symbol}")
                elif status == NO_TRADES_REQUIRED:
                    print("\n⚖️  No rebalancing required - portfolio is already optimally allocated")

    except Exception as e:
        logger.warning(f"Failed to display rebalance plan: {e}")


def display_stale_order_info(trading_result: dict[str, Any]) -> None:
    """Display information about stale orders that were canceled.

    Args:
        trading_result: Dictionary containing trading execution results

    """
    try:
        stale_orders_canceled = trading_result.get("stale_orders_canceled", [])

        if stale_orders_canceled and isinstance(stale_orders_canceled, list):
            print(f"\n🗑️  Canceled {len(stale_orders_canceled)} stale orders:")
            for order in stale_orders_canceled:
                if isinstance(order, dict):
                    symbol = order.get("symbol", "Unknown")
                    side = str(order.get("side", "")).upper()
                    qty = order.get("qty", 0)
                    print(f"  • {side} {qty} shares of {symbol}")

    except Exception as e:
        logger.warning(f"Failed to display stale order info: {e}")


def display_post_execution_tracking(*, paper_trading: bool) -> None:
    """Display post-execution strategy performance tracking.

    Args:
        paper_trading: Whether this is paper trading mode

    """
    try:
        import importlib

        mode_str = "paper trading" if paper_trading else "live trading"
        print(f"\n📊 Strategy Performance Tracking ({mode_str}):")

        module = importlib.import_module("the_alchemiser.shared.utils.strategy_utils")
        func = getattr(module, "display_strategy_performance_tracking", None)

        if callable(func):
            func()
        else:
            logger.warning("Strategy tracking utilities not available")

    except ImportError:
        logger.warning("Strategy tracking utilities not available")
    except Exception as e:
        logger.warning(f"Failed to display post-execution tracking: {e}")


def export_tracking_summary(
    trading_result: dict[str, Any], export_path: str, *, paper_trading: bool
) -> None:
    """Export trading summary and tracking data to JSON file.

    Args:
        trading_result: Dictionary containing trading execution results
        export_path: Path to export JSON file
        paper_trading: Whether this is paper trading mode

    """
    try:
        import json
        from datetime import UTC, datetime
        from pathlib import Path

        # Prepare summary data
        summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "mode": "paper_trading" if paper_trading else "live_trading",
            "status": trading_result.get("status", "unknown"),
            "execution_summary": trading_result.get("execution_summary", {}),
            "rebalance_plan": trading_result.get("rebalance_plan", {}),
            "stale_orders_canceled": trading_result.get("stale_orders_canceled", []),
        }

        # Write to file
        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)

        with export_file.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n💾 Trading summary exported to: {export_path}")

    except Exception as e:
        logger.error(f"Failed to export tracking summary: {e}")
