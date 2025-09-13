"""Business Unit: shared | Status: current.

Trading execution CLI module.

Thin CLI wrapper that delegates to orchestration layer for trading execution workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator
from the_alchemiser.shared.cli.cli_formatter import (
    render_comprehensive_trading_results,
    render_footer,
    render_header,
    render_strategy_summary,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger


class TradingExecutor:
    """Thin CLI wrapper for trading execution workflow."""

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
        live_trading: bool = False,  # DEPRECATED - determined by stage
        ignore_market_hours: bool = False,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> None:
        self.settings = settings
        self.container = container
        self.show_tracking = show_tracking
        self.export_tracking_json = export_tracking_json
        self.logger = get_logger(__name__)

        # Delegate orchestration to dedicated orchestrator
        self.orchestrator = TradingOrchestrator(
            settings, container, live_trading, ignore_market_hours
        )

    def run(self) -> bool:
        """Execute trading strategy."""
        render_header("Analyzing market conditions...", "Multi-Strategy Trading")

        # Delegate to orchestration layer
        result = self.orchestrator.execute_trading_workflow_with_details()

        if result is None:
            render_footer("Trading execution failed - check logs for details")
            return False

        # Extract signal data for display
        strategy_signals = result.get("strategy_signals", {})
        consolidated_portfolio = result.get("consolidated_portfolio", {})
        account_info = result.get("account_info")
        current_positions = result.get("current_positions")
        allocation_comparison = result.get("allocation_comparison")
        orders_executed = result.get("orders_executed", [])
        execution_result = result.get("execution_result")
        open_orders = result.get("open_orders", [])
        success = bool(result.get("success", False))

        # Display strategy signals and comprehensive portfolio information
        if strategy_signals or consolidated_portfolio or account_info:
            self._display_trading_results(
                strategy_signals, 
                consolidated_portfolio,
                account_info,
                current_positions,
                allocation_comparison,
                open_orders
            )

        # Display execution results if trades were made
        if orders_executed:
            self._display_execution_results(orders_executed, execution_result)

        # Display tracking if requested
        if self.show_tracking:
            self._display_post_execution_tracking()

        # Export tracking summary if requested
        if self.export_tracking_json:
            self._export_tracking_summary()

        if success:
            render_footer("Trading execution completed successfully!")
        else:
            render_footer("Trading execution failed - check logs for details")

        return success

    def _display_trading_results(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
        account_info: dict[str, Any] | None = None,
        current_positions: dict[str, Any] | None = None,
        allocation_comparison: dict[str, Any] | None = None,
        open_orders: list[dict[str, Any]] | None = None,
    ) -> None:
        """Display comprehensive trading strategy results including account info and allocations."""
        # Use shared display function to avoid code duplication
        render_comprehensive_trading_results(
            strategy_signals,
            consolidated_portfolio,
            account_info,
            current_positions,
            allocation_comparison,
            open_orders
        )

        # Display strategy summary
        allocations = self.settings.strategy.default_strategy_allocations
        render_strategy_summary(strategy_signals, consolidated_portfolio, allocations)

    def _display_execution_results(
        self,
        orders_executed: list[dict[str, Any]],
        execution_result: Any = None,
    ) -> None:
        """Display comprehensive execution results including order details and summary."""
        from the_alchemiser.shared.cli.cli_formatter import render_orders_executed
        
        try:
            # Display orders executed using existing formatter
            render_orders_executed(orders_executed)
            
            # Display execution summary if available
            if execution_result:
                try:
                    from rich.console import Console
                    from rich.panel import Panel
                    
                    console = Console()
                    
                    success_rate = execution_result.success_rate if hasattr(execution_result, "success_rate") else 1.0
                    total_value = execution_result.total_trade_value if hasattr(execution_result, "total_trade_value") else 0
                    
                    summary_content = [
                        f"[bold green]Execution Success Rate:[/bold green] {success_rate:.1%}",
                        f"[bold blue]Orders Placed:[/bold blue] {execution_result.orders_placed}",
                        f"[bold green]Orders Succeeded:[/bold green] {execution_result.orders_succeeded}",
                        f"[bold yellow]Total Trade Value:[/bold yellow] ${float(total_value):,.2f}",
                    ]
                    
                    if hasattr(execution_result, "failure_count") and execution_result.failure_count > 0:
                        summary_content.append(f"[bold red]Orders Failed:[/bold red] {execution_result.failure_count}")
                    
                    console.print(Panel(
                        "\n".join(summary_content),
                        title="Execution Summary",
                        style="bold white"
                    ))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to display execution summary: {e}")
            
        except Exception as e:
            self.logger.warning(f"Failed to display execution results: {e}")

    def _display_post_execution_tracking(self) -> None:
        """Display strategy performance tracking after execution."""
        try:
            from rich.console import Console
            from rich.panel import Panel

            from the_alchemiser.shared.cli.signal_analyzer import SignalAnalyzer

            console = Console()
            console.print("\n")

            # Create a signal analyzer instance to reuse the tracking display logic
            analyzer = SignalAnalyzer(self.settings, self.container)
            analyzer._display_strategy_tracking()

        except Exception as e:
            self.logger.warning(f"Failed to display post-execution tracking: {e}")
            try:
                from rich.console import Console

                Console().print(
                    Panel(
                        f"[dim yellow]Strategy tracking display unavailable: {e}[/dim yellow]",
                        title="Strategy Performance Tracking",
                        border_style="yellow",
                    )
                )
            except ImportError:
                self.logger.warning("Strategy tracking display unavailable (rich not available)")

    def _export_tracking_summary(self) -> None:
        """Export tracking summary to JSON file."""
        try:
            import json
            from pathlib import Path

            from the_alchemiser.portfolio.pnl.strategy_order_tracker import (
                StrategyOrderTracker,
            )

            # Create tracker using same mode as execution
            tracker = StrategyOrderTracker(paper_trading=not self.orchestrator.live_trading)

            # Get summary data for all strategies
            summary_data = []
            strategies = ["nuclear", "tecl", "klm"]

            for strategy_name in strategies:
                try:
                    positions = tracker.get_positions_summary()
                    if strategy_name.lower() in [pos.strategy.lower() for pos in positions]:
                        pnl_summary = tracker.get_pnl_summary(strategy_name)
                        recent_orders = tracker.get_orders_for_strategy(strategy_name)

                        # Calculate position count
                        strategy_positions = [
                            pos
                            for pos in positions
                            if pos.strategy.lower() == strategy_name.lower()
                        ]
                        position_count = len(strategy_positions)

                        # Calculate return percentage
                        total_pnl = float(pnl_summary.total_pnl)
                        if hasattr(pnl_summary, "cost_basis") and float(pnl_summary.cost_basis) > 0:
                            return_pct = (total_pnl / float(pnl_summary.cost_basis)) * 100
                        else:
                            return_pct = 0.0

                        summary_data.append(
                            {
                                "strategy": strategy_name,
                                "position_count": position_count,
                                "total_pnl": total_pnl,
                                "return_pct": return_pct,
                                "recent_orders_count": len(recent_orders[-10:]),  # Last 10 orders
                                "updated_at": pnl_summary.last_updated.isoformat()
                                if hasattr(pnl_summary, "last_updated") and pnl_summary.last_updated
                                else None,
                            }
                        )
                except Exception as e:
                    self.logger.warning(f"Error gathering tracking data for {strategy_name}: {e}")
                    summary_data.append(
                        {
                            "strategy": strategy_name,
                            "position_count": 0,
                            "total_pnl": 0.0,
                            "return_pct": 0.0,
                            "recent_orders_count": 0,
                            "updated_at": None,
                            "error": str(e),
                        }
                    )

            # Write to file
            if self.export_tracking_json is None:
                raise ValueError("Export path is None")

            output_path = Path(self.export_tracking_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w") as f:
                json.dump(
                    {
                        "summary": summary_data,
                        "export_timestamp": datetime.now(UTC).isoformat(),
                        "trading_mode": "live" if self.orchestrator.live_trading else "paper",
                    },
                    f,
                    indent=2,
                )

            self.logger.info(f"Tracking summary exported to {output_path}")

            try:
                from rich.console import Console

                Console().print(f"[dim]📄 Tracking summary exported to {output_path}[/dim]")
            except ImportError:
                pass

        except Exception as e:
            self.logger.error(f"Failed to export tracking summary: {e}")
            try:
                from rich.console import Console

                Console().print(
                    f"[bold red]Failed to export tracking summary to {self.export_tracking_json}: {e}[/bold red]"
                )
            except ImportError:
                pass
