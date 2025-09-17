"""Business Unit: orchestration | Status: current.

Clean CLI output formatter for trading results.

This module provides a clean, professional CLI formatter that renders
TradeRunResultDTO with minimal noise and proper formatting for different
verbosity levels.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from the_alchemiser.shared.dto.trade_run_result_dto import TradeRunResultDTO


class CleanCliFormatter:
    """Clean, professional CLI formatter for trading results."""

    def __init__(self, console: Console | None = None, *, verbose: bool = False):
        """Initialize formatter.
        
        Args:
            console: Rich console instance (creates new if None)
            verbose: Whether to show verbose output
        """
        self.console = console or Console()
        self.verbose = verbose

    def render_header(self, trading_mode: str) -> None:
        """Render clean trading header."""
        mode_color = "red" if trading_mode == "LIVE" else "blue"
        self.console.print(
            f"[bold {mode_color}]Starting {trading_mode} trading...[/bold {mode_color}]"
        )

    def render_progress_step(self, message: str) -> None:
        """Render a progress step message."""
        self.console.print(f"[dim]{message}[/dim]")

    def render_result(self, result: TradeRunResultDTO) -> None:
        """Render trading execution result in clean format.
        
        Args:
            result: Trade execution result DTO
        """
        # Summary line
        status_color = self._get_status_color(result.status)
        self.console.print(
            f"\n[bold {status_color}]{result.status}:[/bold {status_color}] "
            f"Trading execution completed"
        )

        # Execution summary
        summary = result.execution_summary
        if summary.orders_total > 0:
            self.console.print(
                f"[bold]Execution summary:[/bold] "
                f"{summary.orders_succeeded}/{summary.orders_total} succeeded, "
                f"${summary.total_value:,.2f} total"
            )
        else:
            self.console.print(
                "[bold]Execution summary:[/bold] No orders executed "
                "(portfolio already balanced)"
            )

        # Verbose details
        if self.verbose and result.orders:
            self._render_order_details(result.orders)

        # Warnings
        if result.warnings:
            self._render_warnings(result.warnings)

    def render_json(self, result: TradeRunResultDTO) -> None:
        """Render result as JSON to stdout."""
        json.dump(result.to_json_dict(), sys.stdout, indent=2)
        sys.stdout.write("\n")

    def _get_status_color(self, status: str) -> str:
        """Get color for status."""
        color_map = {
            "SUCCESS": "green",
            "PARTIAL": "yellow", 
            "FAILURE": "red"
        }
        return color_map.get(status, "white")

    def _render_order_details(self, orders: list[Any]) -> None:
        """Render detailed order information."""
        if not orders:
            return

        table = Table(title="Order Details", show_header=True, header_style="bold blue")
        table.add_column("Symbol", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_column("Shares", justify="right")
        table.add_column("Amount", justify="right", style="green")
        table.add_column("Price", justify="right")
        table.add_column("Order ID", style="dim")
        table.add_column("Status")

        for order in orders:
            # Choose order ID display based on verbose setting
            order_id = order.order_id_full if self.verbose else order.order_id_redacted
            order_id_display = order_id or "—"

            # Status with color
            status_text = "✅ SUCCESS" if order.success else "❌ FAILED"
            
            # Price display
            price_display = f"${order.price:.2f}" if order.price else "—"

            table.add_row(
                order.symbol,
                order.action,
                f"{order.shares:,.0f}",
                f"${order.trade_amount:,.2f}",
                price_display,
                order_id_display,
                status_text
            )

        self.console.print()
        self.console.print(table)

    def _render_warnings(self, warnings: list[str]) -> None:
        """Render warnings section."""
        if not warnings:
            return

        self.console.print()
        warning_text = Text("Warnings:")
        warning_text.stylize("bold yellow")
        
        for warning in warnings:
            warning_text.append(f"\n  • {warning}")
        
        panel = Panel(
            warning_text,
            border_style="yellow",
            title="⚠️  Non-Critical Issues",
            title_align="left"
        )
        self.console.print(panel)


def render_trade_result(
    result: TradeRunResultDTO, 
    *,
    json_output: bool = False,
    verbose: bool = False,
    console: Console | None = None
) -> None:
    """Render trade result with appropriate formatting.
    
    Args:
        result: Trade execution result
        json_output: Whether to output JSON instead of rich formatting
        verbose: Whether to show verbose details
        console: Rich console (creates new if None)
    """
    if json_output:
        formatter = CleanCliFormatter(console=console, verbose=verbose)
        formatter.render_json(result)
    else:
        formatter = CleanCliFormatter(console=console, verbose=verbose)
        formatter.render_result(result)