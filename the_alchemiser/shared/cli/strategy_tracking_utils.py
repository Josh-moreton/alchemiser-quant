"""Business Unit: shared | Status: current.

Strategy tracking display utilities.

Shared utility functions for displaying strategy tracking information across CLI modules.
Eliminates code duplication between CLI components that need to show strategy performance data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.logging.logging_utils import get_logger

if TYPE_CHECKING:
    from rich.console import Console
    from rich.table import Table

# Style constants for consistent Rich formatting
BOLD_MAGENTA_STYLE = "bold magenta"


def _add_strategy_row(
    tracking_table: Table, tracker: Any, strategy_name: str, logger: logging.Logger  # noqa: ANN401
) -> None:
    """Add a single strategy row to tracking table.

    Extracts the logic for adding one strategy row to reduce cognitive complexity.

    Args:
        tracking_table: Rich Table object to add row to
        tracker: StrategyOrderTracker instance
        strategy_name: Name of the strategy
        logger: Logger instance for error reporting

    """
    try:
        # Get P&L summary
        pnl_summary = tracker.get_pnl_summary(strategy_name)

        # Get recent orders count
        recent_orders = tracker.get_orders_for_strategy(strategy_name)

        # Color code P&L
        total_pnl = float(pnl_summary.total_pnl)
        pnl_color = "green" if total_pnl >= 0 else "red"
        pnl_sign = "+" if total_pnl >= 0 else ""

        return_pct = float(pnl_summary.total_return_pct)
        return_color = "green" if return_pct >= 0 else "red"
        return_sign = "+" if return_pct >= 0 else ""

        tracking_table.add_row(
            strategy_name,
            str(pnl_summary.position_count),
            f"[{pnl_color}]{pnl_sign}${total_pnl:.2f}[/{pnl_color}]",
            f"[{return_color}]{return_sign}{return_pct:.2f}%[/{return_color}]",
            f"{len(recent_orders)} orders",
        )

    except Exception as e:
        logger.warning(f"Error getting tracking data for {strategy_name}: {e}")
        tracking_table.add_row(
            strategy_name, "Error", "[red]Error[/red]", "[red]Error[/red]", "Error"
        )


def _add_strategy_pnl_row(
    strategy_pnl_table: Table, tracker: Any, strategy_name: str, console: Console  # noqa: ANN401
) -> None:
    """Add a single strategy P&L row to table.

    Extracts the logic for adding one strategy P&L row to reduce cognitive complexity.

    Args:
        strategy_pnl_table: Rich Table object to add row to
        tracker: StrategyOrderTracker instance
        strategy_name: Name of the strategy
        console: Rich Console instance for error display

    """
    try:
        pnl_summary = tracker.get_pnl_summary(strategy_name)

        # Color code P&L
        total_pnl = float(pnl_summary.total_pnl)
        pnl_color = "green" if total_pnl >= 0 else "red"
        pnl_sign = "+" if total_pnl >= 0 else ""

        return_pct = float(pnl_summary.total_return_pct)
        return_color = "green" if return_pct >= 0 else "red"
        return_sign = "+" if return_pct >= 0 else ""

        strategy_pnl_table.add_row(
            strategy_name,
            f"${float(pnl_summary.realized_pnl):.2f}",
            f"${float(pnl_summary.unrealized_pnl):.2f}",
            f"[{pnl_color}]{pnl_sign}${total_pnl:.2f}[/{pnl_color}]",
            f"[{return_color}]{return_sign}{return_pct:.2f}%[/{return_color}]",
        )
    except Exception as e:
        console.print(
            f"[dim yellow]Error getting P&L for {strategy_name}: {e}[/dim yellow]"
        )


def display_strategy_tracking(*, paper_trading: bool) -> None:
    """Display strategy tracking information from StrategyOrderTracker.

    Utility function that can be called from any CLI component to show
    strategy performance tracking without code duplication.

    Args:
        paper_trading: Whether to use paper trading mode for the tracker.

    """
    logger = get_logger(__name__)

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        from the_alchemiser.portfolio.pnl.strategy_order_tracker import (
            StrategyOrderTracker,
        )

        console = Console()

        # Create tracker
        tracker = StrategyOrderTracker(paper_trading=paper_trading)

        # Get all positions
        positions = tracker.get_positions_summary()

        if not positions:
            console.print(
                Panel(
                    "[dim yellow]No strategy tracking data available[/dim yellow]",
                    title="Strategy Performance History",
                    border_style="yellow",
                )
            )
            return

        # Create tracking table
        tracking_table = Table(title="Strategy Performance Tracking", show_lines=True, expand=True)
        tracking_table.add_column("Strategy", style=BOLD_MAGENTA_STYLE)
        tracking_table.add_column("Positions", justify="center")
        tracking_table.add_column("Total P&L", justify="right")
        tracking_table.add_column("Return %", justify="right")
        tracking_table.add_column("Recent Orders", justify="center")

        # Group positions by strategy
        strategies_with_data = {pos.strategy for pos in positions}

        for strategy_name in sorted(strategies_with_data):
            _add_strategy_row(tracking_table, tracker, strategy_name, logger)

        console.print()
        console.print(tracking_table)

        # Add summary insight
        total_strategies = len(strategies_with_data)
        profitable_strategies = sum(
            1
            for strategy_name in strategies_with_data
            if float(tracker.get_pnl_summary(strategy_name).total_pnl) > 0
        )

        insight = f"📊 {profitable_strategies}/{total_strategies} strategies profitable"
        console.print(Panel(insight, title="Performance Insight", border_style="blue"))

    except Exception as e:
        # Non-fatal - tracking is enhancement, not critical
        logger.warning(f"Strategy tracking display unavailable: {e}")


def display_detailed_strategy_positions(*, paper_trading: bool) -> None:
    """Display detailed strategy positions and P&L summary.

    Utility function that shows individual positions and aggregated P&L data,
    complementing the basic strategy tracking display.

    Args:
        paper_trading: Whether to use paper trading mode for the tracker.

    """
    logger = get_logger(__name__)

    try:
        from rich.console import Console
        from rich.table import Table

        from the_alchemiser.portfolio.pnl.strategy_order_tracker import (
            StrategyOrderTracker,
        )

        console = Console()

        tracker = StrategyOrderTracker(paper_trading=paper_trading)

        # Get positions summary
        positions_summary = tracker.get_positions_summary()

        if positions_summary:
            strategy_table = Table(
                title="Strategy Positions (Tracked)", show_lines=True, expand=True
            )
            strategy_table.add_column("Strategy", style=BOLD_MAGENTA_STYLE)
            strategy_table.add_column("Symbol", style="bold cyan")
            strategy_table.add_column("Qty", justify="right")
            strategy_table.add_column("Avg Cost", justify="right")
            strategy_table.add_column("Total Cost", justify="right")
            strategy_table.add_column("Last Updated", justify="center")

            for position in positions_summary:
                # Format timestamp for display
                last_updated = position.last_updated.strftime("%m/%d %H:%M")

                strategy_table.add_row(
                    position.strategy,
                    position.symbol,
                    f"{float(position.quantity):.4f}",
                    f"${float(position.average_cost):.2f}",
                    f"${float(position.total_cost):.2f}",
                    last_updated,
                )

            console.print()
            console.print(strategy_table)

            # Show P&L summary for each strategy with positions
            strategy_pnl_table = Table(title="Strategy P&L Summary", show_lines=True, expand=True)
            strategy_pnl_table.add_column("Strategy", style=BOLD_MAGENTA_STYLE)
            strategy_pnl_table.add_column("Realized P&L", justify="right")
            strategy_pnl_table.add_column("Unrealized P&L", justify="right")
            strategy_pnl_table.add_column("Total P&L", justify="right")
            strategy_pnl_table.add_column("Return %", justify="right")

            strategies_with_data = {pos.strategy for pos in positions_summary}
            for strategy_name in strategies_with_data:
                _add_strategy_pnl_row(strategy_pnl_table, tracker, strategy_name, console)

            if strategy_pnl_table.rows:
                console.print()
                console.print(strategy_pnl_table)
        else:
            console.print()
            console.print("[dim yellow]No strategy positions found in tracking system[/dim yellow]")

    except Exception as e:  # Non-fatal UI enhancement
        logger.warning(f"Strategy detailed positions display unavailable: {e}")
