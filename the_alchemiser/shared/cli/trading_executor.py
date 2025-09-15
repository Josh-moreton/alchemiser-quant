"""Business Unit: shared | Status: current.

Trading execution CLI module.

Thin CLI wrapper that delegates to orchestration layer for trading execution workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator
from the_alchemiser.shared.cli.base_cli import BaseCLI
from the_alchemiser.shared.cli.cli_formatter import (
    render_footer,
    render_header,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.protocols.strategy_tracking import (
    StrategyOrderTrackerProtocol,
    StrategyPnLSummaryProtocol,
)


class ExecutionResult(Protocol):
    """Protocol for execution result interface."""

    success_rate: float
    total_trade_value: Decimal
    orders_placed: int
    orders_succeeded: int
    failure_count: int


class TradingExecutor(BaseCLI):
    """Thin CLI wrapper for trading execution workflow."""

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
        *,
        ignore_market_hours: bool = False,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> None:
        """Initialize trading executor.

        Args:
            settings: Application settings
            container: Application container for dependency injection
            ignore_market_hours: Whether to ignore market hours check
            show_tracking: Whether to show strategy tracking
            export_tracking_json: Path to export tracking JSON file

        """
        super().__init__(settings, container)
        self.show_tracking = show_tracking
        self.export_tracking_json = export_tracking_json

        # Delegate orchestration to dedicated orchestrator
        self.orchestrator = TradingOrchestrator(settings, container, ignore_market_hours)

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
            self._display_comprehensive_results(
                strategy_signals,
                consolidated_portfolio,
                account_info,
                current_positions,
                allocation_comparison,
                open_orders,
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

    def _display_execution_results(
        self,
        orders_executed: list[dict[str, Any]],
        execution_result: ExecutionResult | None = None,
    ) -> None:
        """Display comprehensive execution results including order details and summary."""
        from the_alchemiser.shared.cli.cli_formatter import render_orders_executed

        try:
            # Display orders executed using existing formatter
            render_orders_executed(orders_executed)

            # Display detailed order status information
            self._display_order_status_details(orders_executed)

            # Display execution summary if available
            if execution_result:
                try:
                    from rich.console import Console
                    from rich.panel import Panel

                    console = Console()

                    success_rate = (
                        execution_result.success_rate
                        if hasattr(execution_result, "success_rate")
                        else 1.0
                    )
                    total_value = (
                        execution_result.total_trade_value
                        if hasattr(execution_result, "total_trade_value")
                        else Decimal(0)
                    )

                    summary_content = [
                        f"[bold green]Execution Success Rate:[/bold green] {success_rate:.1%}",
                        f"[bold blue]Orders Placed:[/bold blue] {execution_result.orders_placed}",
                        f"[bold green]Orders Succeeded:[/bold green] "
                        f"{execution_result.orders_succeeded}",
                        f"[bold yellow]Total Trade Value:[/bold yellow] ${float(total_value):,.2f}",
                    ]

                    if (
                        hasattr(execution_result, "failure_count")
                        and execution_result.failure_count > 0
                    ):
                        summary_content.append(
                            f"[bold red]Orders Failed:[/bold red] {execution_result.failure_count}"
                        )

                    console.print(
                        Panel(
                            "\n".join(summary_content),
                            title="Execution Summary",
                            style="bold white",
                        )
                    )

                except Exception as e:
                    self.logger.warning(f"Failed to display execution summary: {e}")

        except Exception as e:
            self.logger.warning(f"Failed to display execution results: {e}")

    def _display_order_status_details(self, orders_executed: list[dict[str, Any]]) -> None:
        """Display detailed order status information including order IDs and errors.

        Args:
            orders_executed: List of order execution results

        """
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()

            if not orders_executed:
                return

            # Create detailed status table
            status_table = Table(title="Order Execution Details", show_lines=True)
            status_table.add_column("Symbol", style="cyan", justify="center")
            status_table.add_column("Action", style="bold", justify="center")
            status_table.add_column("Status", style="bold", justify="center")
            status_table.add_column("Order ID", style="dim", justify="center")
            status_table.add_column("Error Details", style="red", justify="left")

            for order in orders_executed:
                status = order.get("status", "UNKNOWN")
                order_id = order.get("order_id") or "N/A"
                error = order.get("error") or ""

                # Style status
                if status == "FILLED":
                    status_display = "[bold green]✅ FILLED[/bold green]"
                elif status == "FAILED":
                    status_display = "[bold red]❌ FAILED[/bold red]"
                else:
                    status_display = f"[yellow]{status}[/yellow]"

                # Style action
                action = order.get("side", "").upper()
                if action == "BUY":
                    action_display = "[green]BUY[/green]"
                elif action == "SELL":
                    action_display = "[red]SELL[/red]"
                else:
                    action_display = action

                status_table.add_row(
                    order.get("symbol", "N/A"),
                    action_display,
                    status_display,
                    order_id,
                    error[:50] + "..." if len(error) > 50 else error,
                )

            console.print(status_table)

        except Exception as e:
            self.logger.warning(f"Failed to display order status details: {e}")

    def _display_post_execution_tracking(self) -> None:
        """Display strategy performance tracking after execution."""
        try:
            from rich.console import Console

            console = Console()
            console.print("\n")

            # Use the shared tracking display method from BaseCLI
            self._display_strategy_tracking(paper_trading=not self.orchestrator.live_trading)

        except Exception as e:
            self.logger.warning(f"Failed to display post-execution tracking: {e}")
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
                self.logger.warning("Strategy tracking display unavailable (rich not available)")

    def _export_tracking_summary(self) -> None:
        """Export tracking summary to JSON file."""
        try:
            from the_alchemiser.shared.cli.strategy_tracking_utils import (
                _get_strategy_order_tracker,
            )

            # Create tracker using same mode as execution
            tracker = _get_strategy_order_tracker(paper_trading=not self.orchestrator.live_trading)

            # Collect strategy data
            summary_data = self._collect_strategy_tracking_data(tracker)

            # Write export file
            self._write_tracking_export(summary_data)

        except Exception as e:
            self._handle_export_error(e)

    def _collect_strategy_tracking_data(
        self, tracker: StrategyOrderTrackerProtocol
    ) -> list[dict[str, Any]]:
        """Collect tracking data for all strategies.
        
        Args:
            tracker: Strategy order tracker instance
            
        Returns:
            List of strategy tracking data dictionaries

        """
        summary_data = []
        strategies = ["nuclear", "tecl", "klm"]

        for strategy_name in strategies:
            try:
                strategy_data = self._get_single_strategy_data(tracker, strategy_name)
                summary_data.append(strategy_data)
            except Exception as e:
                self.logger.warning(f"Error gathering tracking data for {strategy_name}: {e}")
                summary_data.append(self._create_error_strategy_data(strategy_name, e))

        return summary_data

    def _get_single_strategy_data(self, tracker: StrategyOrderTrackerProtocol, strategy_name: str) -> dict[str, Any]:
        """Get tracking data for a single strategy.
        
        Args:
            tracker: Strategy order tracker instance
            strategy_name: Name of strategy to get data for
            
        Returns:
            Strategy tracking data dictionary

        """
        positions = tracker.get_positions_summary()
        
        if strategy_name.lower() not in [pos.strategy.lower() for pos in positions]:
            return self._create_empty_strategy_data(strategy_name)

        pnl_summary = tracker.get_pnl_summary(strategy_name)
        recent_orders = tracker.get_orders_for_strategy(strategy_name)

        # Calculate position count
        strategy_positions = [
            pos for pos in positions
            if pos.strategy.lower() == strategy_name.lower()
        ]
        position_count = len(strategy_positions)

        # Calculate return percentage
        total_pnl = float(pnl_summary.total_pnl)
        return_pct = self._calculate_return_percentage(pnl_summary, total_pnl)

        return {
            "strategy": strategy_name,
            "position_count": position_count,
            "total_pnl": total_pnl,
            "return_pct": return_pct,
            "recent_orders_count": len(recent_orders[-10:]),  # Last 10 orders
            "updated_at": pnl_summary.last_updated.isoformat()
            if hasattr(pnl_summary, "last_updated") and pnl_summary.last_updated
            else None,
        }

    def _calculate_return_percentage(self, pnl_summary: StrategyPnLSummaryProtocol, total_pnl: float) -> float:
        """Calculate return percentage from PnL summary.
        
        Args:
            pnl_summary: PnL summary object
            total_pnl: Total PnL value
            
        Returns:
            Return percentage

        """
        if hasattr(pnl_summary, "cost_basis") and float(pnl_summary.cost_basis) > 0:
            return (total_pnl / float(pnl_summary.cost_basis)) * 100
        return 0.0

    def _create_empty_strategy_data(self, strategy_name: str) -> dict[str, Any]:
        """Create empty data structure for strategy with no positions.
        
        Args:
            strategy_name: Name of strategy
            
        Returns:
            Empty strategy data dictionary

        """
        return {
            "strategy": strategy_name,
            "position_count": 0,
            "total_pnl": 0.0,
            "return_pct": 0.0,
            "recent_orders_count": 0,
            "updated_at": None,
        }

    def _create_error_strategy_data(self, strategy_name: str, error: Exception) -> dict[str, Any]:
        """Create error data structure for failed strategy data collection.
        
        Args:
            strategy_name: Name of strategy
            error: Exception that occurred
            
        Returns:
            Error strategy data dictionary

        """
        data = self._create_empty_strategy_data(strategy_name)
        data["error"] = str(error)
        return data

    def _write_tracking_export(self, summary_data: list[dict[str, Any]]) -> None:
        """Write tracking summary to JSON file.
        
        Args:
            summary_data: List of strategy tracking data

        """
        import json

        if self.export_tracking_json is None:
            raise ValueError("Export path is None")

        output_path = Path(self.export_tracking_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "summary": summary_data,
            "export_timestamp": datetime.now(UTC).isoformat(),
            "trading_mode": "live" if self.orchestrator.live_trading else "paper",
        }

        with output_path.open("w") as f:
            json.dump(export_data, f, indent=2)

        self.logger.info(f"Tracking summary exported to {output_path}")
        self._display_export_success(output_path)

    def _display_export_success(self, output_path: Path) -> None:
        """Display success message for export.
        
        Args:
            output_path: Path where file was exported

        """
        try:
            from rich.console import Console
            Console().print(f"[dim]📄 Tracking summary exported to {output_path}[/dim]")
        except ImportError:
            pass

    def _handle_export_error(self, error: Exception) -> None:
        """Handle export error with logging and display.
        
        Args:
            error: Exception that occurred during export

        """
        self.logger.error(f"Failed to export tracking summary: {error}")
        try:
            from rich.console import Console
            Console().print(
                f"[bold red]Failed to export tracking summary to "
                f"{self.export_tracking_json}: {error}[/bold red]"
            )
        except ImportError:
            pass
