#!/usr/bin/env python3
"""
CLI integration example for StrategyOrderTracker DTO usage.

This module demonstrates how to use the new DTO-based methods
in CLI reporting and display utilities.
"""

from typing import Dict, List
from decimal import Decimal
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from the_alchemiser.application.tracking.strategy_order_tracker import get_strategy_tracker
from the_alchemiser.interfaces.schemas.tracking import (
    StrategyOrderDTO,
    StrategyPositionDTO,
    StrategyPnLDTO,
)


def display_strategy_orders_dto(strategy_name: str, paper_trading: bool = True) -> None:
    """Display strategy orders using DTO interface."""
    console = Console()
    
    try:
        # Get tracker and fetch orders using DTO method
        tracker = get_strategy_tracker(paper_trading=paper_trading)
        orders = tracker.get_orders_for_strategy(strategy_name)
        
        if not orders:
            console.print(f"[yellow]No orders found for strategy {strategy_name}[/yellow]")
            return
        
        # Create rich table
        table = Table(title=f"{strategy_name} Strategy Orders")
        table.add_column("Order ID", style="cyan")
        table.add_column("Symbol", style="magenta")
        table.add_column("Side", style="green")
        table.add_column("Quantity", justify="right", style="blue")
        table.add_column("Price", justify="right", style="yellow")
        table.add_column("Timestamp", style="dim")
        
        for order in orders:
            table.add_row(
                order.order_id,
                order.symbol,
                order.side.upper(),
                f"{order.quantity:,.2f}",
                f"${order.price:,.2f}",
                order.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error displaying strategy orders: {e}[/red]")


def display_positions_summary_dto(paper_trading: bool = True) -> None:
    """Display positions summary using DTO interface."""
    console = Console()
    
    try:
        # Get tracker and fetch positions using DTO method
        tracker = get_strategy_tracker(paper_trading=paper_trading)
        positions = tracker.get_positions_summary()
        
        if not positions:
            console.print("[yellow]No active positions found[/yellow]")
            return
        
        # Create rich table
        table = Table(title="Strategy Positions Summary")
        table.add_column("Strategy", style="cyan")
        table.add_column("Symbol", style="magenta")
        table.add_column("Quantity", justify="right", style="blue")
        table.add_column("Avg Cost", justify="right", style="yellow")
        table.add_column("Total Cost", justify="right", style="green")
        table.add_column("Last Updated", style="dim")
        
        for position in positions:
            table.add_row(
                position.strategy,
                position.symbol,
                f"{position.quantity:,.2f}",
                f"${position.average_cost:,.2f}",
                f"${position.total_cost:,.2f}",
                position.last_updated.strftime("%Y-%m-%d %H:%M:%S")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error displaying positions summary: {e}[/red]")


def display_strategy_pnl_dto(strategy_name: str, current_prices: Dict[str, float] | None = None, paper_trading: bool = True) -> None:
    """Display strategy P&L using DTO interface."""
    console = Console()
    
    try:
        # Get tracker and fetch P&L using DTO method
        tracker = get_strategy_tracker(paper_trading=paper_trading)
        pnl = tracker.get_pnl_summary(strategy_name, current_prices)
        
        # Calculate additional metrics
        total_return_pct = pnl.total_return_pct if pnl.allocation_value > 0 else Decimal("0")
        
        # Create rich panel with P&L info
        pnl_content = f"""
[bold cyan]{strategy_name} Strategy P&L[/bold cyan]

[green]Realized P&L:[/green] ${pnl.realized_pnl:,.2f}
[blue]Unrealized P&L:[/blue] ${pnl.unrealized_pnl:,.2f}
[bold yellow]Total P&L:[/bold yellow] ${pnl.total_pnl:,.2f}

[magenta]Allocation Value:[/magenta] ${pnl.allocation_value:,.2f}
[cyan]Total Return:[/cyan] {total_return_pct:.2f}%

[dim]Positions:[/dim] {pnl.position_count} active positions
        """.strip()
        
        panel = Panel(pnl_content, title=f"{strategy_name} Performance", border_style="blue")
        console.print(panel)
        
        # Show positions if any
        if pnl.positions:
            table = Table(title="Current Positions")
            table.add_column("Symbol", style="magenta")
            table.add_column("Quantity", justify="right", style="blue")
            
            for symbol, quantity in pnl.positions.items():
                table.add_row(symbol, f"{quantity:,.2f}")
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error displaying strategy P&L: {e}[/red]")


def display_all_strategies_pnl_dto(current_prices: Dict[str, float] | None = None, paper_trading: bool = True) -> None:
    """Display P&L for all strategies using DTO interface."""
    console = Console()
    
    try:
        from the_alchemiser.domain.registry import StrategyType
        
        # Get tracker
        tracker = get_strategy_tracker(paper_trading=paper_trading)
        
        # Create summary table
        table = Table(title="All Strategies P&L Summary")
        table.add_column("Strategy", style="cyan")
        table.add_column("Realized P&L", justify="right", style="green")
        table.add_column("Unrealized P&L", justify="right", style="blue")
        table.add_column("Total P&L", justify="right", style="yellow")
        table.add_column("Allocation", justify="right", style="magenta")
        table.add_column("Return %", justify="right", style="cyan")
        table.add_column("Positions", justify="right", style="dim")
        
        total_realized = Decimal("0")
        total_unrealized = Decimal("0")
        total_allocation = Decimal("0")
        
        for strategy in StrategyType:
            try:
                pnl = tracker.get_pnl_summary(strategy.value, current_prices)
                
                total_realized += pnl.realized_pnl
                total_unrealized += pnl.unrealized_pnl
                total_allocation += pnl.allocation_value
                
                return_pct = pnl.total_return_pct if pnl.allocation_value > 0 else Decimal("0")
                
                # Color code P&L
                total_color = "green" if pnl.total_pnl >= 0 else "red"
                
                table.add_row(
                    strategy.value,
                    f"${pnl.realized_pnl:,.2f}",
                    f"${pnl.unrealized_pnl:,.2f}",
                    f"[{total_color}]${pnl.total_pnl:,.2f}[/{total_color}]",
                    f"${pnl.allocation_value:,.2f}",
                    f"{return_pct:.2f}%",
                    str(pnl.position_count)
                )
                
            except Exception as e:
                console.print(f"[red]Error getting P&L for {strategy.value}: {e}[/red]")
        
        console.print(table)
        
        # Show totals
        total_pnl = total_realized + total_unrealized
        total_return = (total_pnl / total_allocation * 100) if total_allocation > 0 else Decimal("0")
        total_color = "green" if total_pnl >= 0 else "red"
        
        totals_content = f"""
[bold]Portfolio Totals[/bold]

[green]Total Realized P&L:[/green] ${total_realized:,.2f}
[blue]Total Unrealized P&L:[/blue] ${total_unrealized:,.2f}
[bold {total_color}]Total P&L:[/bold {total_color}] ${total_pnl:,.2f}

[magenta]Total Allocation:[/magenta] ${total_allocation:,.2f}
[cyan]Portfolio Return:[/cyan] {total_return:.2f}%
        """.strip()
        
        console.print(Panel(totals_content, title="Portfolio Summary", border_style="blue"))
        
    except Exception as e:
        console.print(f"[red]Error displaying all strategies P&L: {e}[/red]")


# Example CLI command integration
def strategy_tracking_report(strategy: str | None = None, paper_trading: bool = True) -> None:
    """Generate comprehensive strategy tracking report using DTOs."""
    console = Console()
    
    console.print("[bold blue]Strategy Tracking Report[/bold blue]")
    console.print("=" * 50)
    
    if strategy:
        # Single strategy report
        display_strategy_pnl_dto(strategy, paper_trading=paper_trading)
        console.print("")
        display_strategy_orders_dto(strategy, paper_trading=paper_trading)
    else:
        # All strategies report
        display_all_strategies_pnl_dto(paper_trading=paper_trading)
        console.print("")
        display_positions_summary_dto(paper_trading=paper_trading)


if __name__ == "__main__":
    # Example usage
    strategy_tracking_report()