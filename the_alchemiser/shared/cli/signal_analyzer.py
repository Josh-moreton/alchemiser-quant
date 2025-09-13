"""Business Unit: shared | Status: current.

Signal analysis CLI module.

Thin CLI wrapper that delegates to orchestration layer for signal analysis workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.signal_orchestrator import SignalOrchestrator
from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator
from the_alchemiser.shared.cli.cli_formatter import (
    render_comprehensive_trading_results,
    render_footer,
    render_header,
    render_strategy_summary,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger


class SignalAnalyzer:
    """Thin CLI wrapper for signal analysis workflow."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)

        # Delegate orchestration to dedicated orchestrator
        self.orchestrator = SignalOrchestrator(settings, container)

        # Also create trading orchestrator for enhanced signal analysis with account info
        self.trading_orchestrator = TradingOrchestrator(settings, container, live_trading=False)

    def _display_results(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
        show_tracking: bool,
        account_info: dict[str, Any] | None = None,
        current_positions: dict[str, Any] | None = None,
        allocation_comparison: dict[str, Any] | None = None,
        open_orders: list[dict[str, Any]] | None = None,
    ) -> None:
        """Display comprehensive signal analysis results including account info."""
        # Use shared display function to avoid code duplication
        render_comprehensive_trading_results(
            strategy_signals,
            consolidated_portfolio,
            account_info,
            current_positions,
            allocation_comparison,
            open_orders,
        )

    def _display_strategy_tracking(self) -> None:
        """Display strategy tracking information from StrategyOrderTracker."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            from the_alchemiser.portfolio.pnl.strategy_order_tracker import (
                StrategyOrderTracker,
            )

            console = Console()

            # Use paper trading mode for signal analysis
            tracker = StrategyOrderTracker(paper_trading=True)

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
            tracking_table = Table(
                title="Strategy Performance Tracking", show_lines=True, expand=True
            )
            tracking_table.add_column("Strategy", style="bold magenta")
            tracking_table.add_column("Positions", justify="center")
            tracking_table.add_column("Total P&L", justify="right")
            tracking_table.add_column("Return %", justify="right")
            tracking_table.add_column("Recent Orders", justify="center")

            # Group positions by strategy
            strategies_with_data = {pos.strategy for pos in positions}

            for strategy_name in sorted(strategies_with_data):
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
                    self.logger.warning(f"Error getting tracking data for {strategy_name}: {e}")
                    tracking_table.add_row(
                        strategy_name, "Error", "[red]Error[/red]", "[red]Error[/red]", "Error"
                    )

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
            self.logger.warning(f"Strategy tracking display unavailable: {e}")

    def _display_strategy_summary(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
    ) -> None:
        """Display strategy allocation summary."""
        # Use shared function to avoid code duplication
        allocations = self.settings.strategy.default_strategy_allocations
        render_strategy_summary(strategy_signals, consolidated_portfolio, allocations)

    def run(self, show_tracking: bool = False) -> bool:
        """Run signal analysis with enhanced account information display.

        Args:
            show_tracking: When True, include strategy performance tracking table (opt-in to keep
                default output closer to original minimal signal view).

        """
        render_header("MULTI-STRATEGY SIGNAL ANALYSIS", f"Analysis at {datetime.now(UTC)}")

        # Use enhanced trading orchestrator for comprehensive signal analysis with account info
        result = self.trading_orchestrator.execute_strategy_signals()

        if result is None:
            self.logger.error("Signal analysis failed")
            return False

        # Extract comprehensive result data
        strategy_signals = result.get("strategy_signals", {})
        consolidated_portfolio = result.get("consolidated_portfolio", {})
        account_info = result.get("account_info")
        current_positions = result.get("current_positions")
        allocation_comparison = result.get("allocation_comparison")
        open_orders = result.get("open_orders", [])

        # Display results with enhanced account information
        self._display_results(
            strategy_signals,
            consolidated_portfolio,
            show_tracking,
            account_info,
            current_positions,
            allocation_comparison,
            open_orders,
        )

        # Display strategy summary
        self._display_strategy_summary(strategy_signals, consolidated_portfolio)

        # Display tracking if requested
        if show_tracking:
            self._display_strategy_tracking()

        render_footer("Signal analysis completed successfully!")
        return True
