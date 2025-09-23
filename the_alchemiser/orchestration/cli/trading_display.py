#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Trading workflow display utilities for CLI.

Provides formatting and display functions for trading workflow results including
signals summary, rebalance plans, and execution tracking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

from the_alchemiser.shared.constants import (
    NO_TRADES_REQUIRED,
    REBALANCE_PLAN_GENERATED,
)
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.math.num import floats_equal

logger = get_logger(__name__)


def display_signals_summary(signals_result: dict[str, Any]) -> None:
    """Display a brief summary of generated signals and target allocations.

    Args:
        signals_result: Dictionary containing strategy signals and consolidated portfolio

    """
    try:
        # Extract and display individual strategy signals with their recommended symbols
        strategy_signals = signals_result.get("strategy_signals", {})
        if isinstance(strategy_signals, dict):
            signal_details = []
            for raw_name, data in strategy_signals.items():
                name = str(raw_name)
                if name.startswith("StrategyType."):
                    name = name.split(".", 1)[1]

                if isinstance(data, dict):
                    action = str(data.get("action", "")).upper()
                    if action in {"BUY", "SELL"}:
                        if data.get("is_multi_symbol") and isinstance(data.get("symbols"), list):
                            symbols = data.get("symbols", [])
                            if symbols:
                                symbol_str = ", ".join(symbols)
                                signal_details.append(f"{name}: {action} {symbol_str}")
                        elif data.get("symbol"):
                            signal_details.append(f"{name}: {action} {data.get('symbol')}")

            if signal_details:
                print("📋 Strategy signals generated:")
                for detail in signal_details:
                    print(f"   → {detail}")
            else:
                print("📋 No actionable signals generated")

        # Show consolidated target allocations
        if "consolidated_portfolio" in signals_result:
            portfolio = signals_result["consolidated_portfolio"]
            if isinstance(portfolio, dict):
                non_zero = [
                    (s, float(w)) for s, w in portfolio.items() if not floats_equal(float(w), 0.0)
                ]
                if non_zero:
                    # Sort by allocation percentage descending
                    non_zero.sort(key=lambda x: x[1], reverse=True)
                    allocations = ", ".join(
                        f"{sym} {weight * 100:.1f}%" for sym, weight in non_zero
                    )
                    print(f"🎯 Final recommended allocations: {allocations}")
                else:
                    print("🎯 Final recommended allocations: 100% cash")
    except Exception as e:
        # Non-fatal: summary display is best-effort
        logger.debug(f"Failed to display signals summary: {e}")


def display_rebalance_plan(trading_result: dict[str, Any]) -> None:
    """Display a concise BUY/SELL summary of the rebalance plan.

    Args:
        trading_result: Dictionary containing rebalance plan and execution results

    """
    try:
        rebalance_plan = trading_result.get("rebalance_plan")

        if rebalance_plan is None:
            print(NO_TRADES_REQUIRED)
            return

        # If rebalance_plan is a DTO, get the items
        if hasattr(rebalance_plan, "items"):
            plan_items = rebalance_plan.items
        elif isinstance(rebalance_plan, dict) and "items" in rebalance_plan:
            plan_items = rebalance_plan["items"]
        else:
            # Fallback: no detailed plan available
            print(REBALANCE_PLAN_GENERATED)
            print("   → BUY: (details unavailable)")
            print("   → SELL: (details unavailable)")
            return

        if not plan_items:
            print(NO_TRADES_REQUIRED)
            return

        # Group items by action
        buy_orders = []
        sell_orders = []

        for item in plan_items:
            # Handle both DTO and dict representations
            if hasattr(item, "action"):
                action = item.action
                symbol = item.symbol
                trade_amount = item.trade_amount
            elif isinstance(item, dict):
                action = item.get("action", "").upper()
                symbol = item.get("symbol", "")
                trade_amount = item.get("trade_amount", 0)
            else:
                continue

            if action == "BUY" and float(trade_amount) > 0:
                buy_orders.append(f"{symbol} ${abs(float(trade_amount)):,.0f}")
            elif action == "SELL" and float(trade_amount) < 0:
                sell_orders.append(f"{symbol} ${abs(float(trade_amount)):,.0f}")

        # Display the plan in a concise summary similar to signals
        if buy_orders or sell_orders:
            print(REBALANCE_PLAN_GENERATED)
            if sell_orders:
                print(f"   → SELL: {', '.join(sell_orders)}")
            if buy_orders:
                print(f"   → BUY: {', '.join(buy_orders)}")
        else:
            print(NO_TRADES_REQUIRED)

    except Exception as e:
        # Non-fatal: summary display is best-effort
        logger.debug(f"Failed to display rebalance plan: {e}")
        print(REBALANCE_PLAN_GENERATED)
        print("   → BUY: (details unavailable)")
        print("   → SELL: (details unavailable)")


def display_stale_order_info(trading_result: dict[str, Any]) -> None:
    """Display stale order cancellation information.

    Args:
        trading_result: Dictionary containing execution results

    """
    try:
        execution_result = trading_result.get("execution_result")
        if execution_result and hasattr(execution_result, "metadata") and execution_result.metadata:
            stale_count = execution_result.metadata.get("stale_orders_cancelled", 0)
            if stale_count > 0:
                print(f"🗑️ Cancelled {stale_count} stale order(s)")
    except Exception as e:
        # Non-fatal: stale order display is best-effort
        logger.debug(f"Failed to display stale order info: {e}")


def display_post_execution_tracking(*, paper_trading: bool) -> None:
    """Display strategy performance tracking after execution.

    Args:
        paper_trading: Whether this is paper trading mode

    """
    try:
        from rich.console import Console

        from the_alchemiser.orchestration.cli.strategy_tracking_utils import (
            display_strategy_tracking,
        )

        console = Console()
        console.print("\n")
        display_strategy_tracking(paper_trading=paper_trading)

    except Exception as e:
        logger.warning(f"Failed to display post-execution tracking: {e}")
        try:
            from rich.console import Console
            from rich.panel import Panel

            Console().print(
                Panel(
                    f"[dim yellow]Strategy tracking display unavailable: {e}[/dim yellow]",
                    title="Strategy Performance Tracking",
                    border_style="yellow",
                )
            )
        except ImportError:
            logger.warning("Strategy tracking display unavailable (rich not available)")


def export_tracking_summary(*, export_path: str, paper_trading: bool) -> None:
    """Export tracking summary to JSON file.

    Args:
        export_path: Path where to export the tracking summary
        paper_trading: Whether this is paper trading mode

    """
    try:
        import json
        from pathlib import Path

        from the_alchemiser.orchestration.cli.strategy_tracking_utils import (
            _get_strategy_order_tracker,
        )

        # Create tracker using same mode as execution
        tracker = _get_strategy_order_tracker(paper_trading=paper_trading)

        # Collect strategy data
        strategy_data = {}
        for strategy_name in ["nuclear", "tecl", "klm"]:
            try:
                strategy_summary = tracker.get_strategy_summary(strategy_name)
                if strategy_summary:
                    strategy_data[strategy_name] = {
                        "total_profit_loss": float(strategy_summary.total_profit_loss),
                        "total_orders": strategy_summary.total_orders,
                        "success_rate": strategy_summary.success_rate,
                        "avg_profit_per_trade": float(strategy_summary.avg_profit_per_trade),
                    }
            except Exception as e:
                logger.debug(f"Could not get summary for {strategy_name}: {e}")

        # Export to JSON
        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)

        with export_file.open("w") as f:
            json.dump(strategy_data, f, indent=2)

        logger.info(f"Tracking summary exported to: {export_path}")

    except Exception as e:
        logger.warning(f"Failed to export tracking summary: {e}")
