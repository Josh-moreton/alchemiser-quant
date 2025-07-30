#!/usr/bin/env python3
"""
Demo script for the progressive limit order strategy.

This script demonstrates the enhanced limit order placement logic without placing actual orders.
Shows the progressive pricing strategy for both BUY and SELL orders.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from rich.console import Console
from rich.table import Table
from alpaca.trading.enums import OrderSide

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def demo_progressive_strategy():
    """Demonstrate the progressive limit order strategy without placing orders."""
    console = Console()
    console.print("[bold green]📊 Progressive Limit Order Strategy Demo[/bold green]")
    
    try:
        # Import our components
        from the_alchemiser.core.data.data_provider import UnifiedDataProvider
        
        # Initialize data provider
        console.print("[cyan]Initializing data provider with WebSocket pricing...[/cyan]")
        data_provider = UnifiedDataProvider(paper_trading=True, enable_real_time=True)
        
        # Wait for WebSocket connection
        console.print("[dim]Waiting for WebSocket connection...[/dim]")
        time.sleep(2)
        
        # Test with multiple symbols
        test_symbols = ["UVXY", "SPY", "QQQ", "TSLA"]
        
        for symbol in test_symbols:
            console.print(f"\n[bold]Progressive Strategy Analysis for {symbol}[/bold]")
            
            # Get current bid/ask
            quote = data_provider.get_latest_quote(symbol)
            if not quote or len(quote) < 2:
                console.print(f"[red]No quote data available for {symbol}[/red]")
                continue
                
            bid, ask = float(quote[0]), float(quote[1])
            
            if not (bid > 0 and ask > 0 and ask > bid):
                console.print(f"[red]Invalid quote for {symbol}: bid=${bid:.2f}, ask=${ask:.2f}[/red]")
                continue
            
            midpoint = (bid + ask) / 2.0
            spread = ask - bid
            spread_pct = (spread / midpoint) * 100
            
            # Create market data table
            market_table = Table(title=f"{symbol} Market Data")
            market_table.add_column("Metric", style="cyan")
            market_table.add_column("Value", style="white")
            
            market_table.add_row("Bid", f"${bid:.2f}")
            market_table.add_row("Ask", f"${ask:.2f}")
            market_table.add_row("Midpoint", f"${midpoint:.2f}")
            market_table.add_row("Spread", f"${spread:.2f}")
            market_table.add_row("Spread %", f"{spread_pct:.2f}%")
            
            console.print(market_table)
            
            # Show BUY progression
            buy_table = Table(title=f"{symbol} BUY Order Progression")
            buy_table.add_column("Step", style="cyan")
            buy_table.add_column("Strategy", style="yellow")
            buy_table.add_column("Limit Price", style="green")
            buy_table.add_column("vs Midpoint", style="dim")
            buy_table.add_column("vs Ask", style="dim")
            
            steps = [0.0, 0.1, 0.2, 0.3]
            for i, step_pct in enumerate(steps):
                limit_price = midpoint + (spread / 2 * step_pct)
                vs_midpoint = limit_price - midpoint
                vs_ask = ask - limit_price
                
                if i == 0:
                    step_name = "1"
                    strategy = "Midpoint Start"
                else:
                    step_name = str(i + 1)
                    strategy = f"{step_pct*100:.0f}% toward ask"
                
                buy_table.add_row(
                    step_name,
                    strategy,
                    f"${limit_price:.2f}",
                    f"+${vs_midpoint:.2f}" if vs_midpoint >= 0 else f"-${abs(vs_midpoint):.2f}",
                    f"-${vs_ask:.2f}" if vs_ask >= 0 else f"+${abs(vs_ask):.2f}"
                )
            
            buy_table.add_row("5", "Market Order", "Market", "Market execution", "Guaranteed fill")
            console.print(buy_table)
            
            # Show SELL progression
            sell_table = Table(title=f"{symbol} SELL Order Progression")
            sell_table.add_column("Step", style="cyan")
            sell_table.add_column("Strategy", style="yellow") 
            sell_table.add_column("Limit Price", style="red")
            sell_table.add_column("vs Midpoint", style="dim")
            sell_table.add_column("vs Bid", style="dim")
            
            for i, step_pct in enumerate(steps):
                limit_price = midpoint - (spread / 2 * step_pct)
                vs_midpoint = midpoint - limit_price
                vs_bid = limit_price - bid
                
                if i == 0:
                    step_name = "1"
                    strategy = "Midpoint Start"
                else:
                    step_name = str(i + 1)
                    strategy = f"{step_pct*100:.0f}% toward bid"
                
                sell_table.add_row(
                    step_name,
                    strategy,
                    f"${limit_price:.2f}",
                    f"-${vs_midpoint:.2f}" if vs_midpoint >= 0 else f"+${abs(vs_midpoint):.2f}",
                    f"+${vs_bid:.2f}" if vs_bid >= 0 else f"-${abs(vs_bid):.2f}"
                )
            
            sell_table.add_row("5", "Market Order", "Market", "Market execution", "Guaranteed fill")
            console.print(sell_table)
        
        # Show strategy benefits
        console.print(f"\n[bold green]📈 Progressive Strategy Benefits[/bold green]")
        
        benefits_table = Table()
        benefits_table.add_column("Feature", style="cyan")
        benefits_table.add_column("Benefit", style="green")
        benefits_table.add_column("Impact", style="yellow")
        
        benefits_table.add_row(
            "Midpoint Start",
            "Best possible execution price",
            "Maximizes price improvement opportunity"
        )
        benefits_table.add_row(
            "10-Second Steps", 
            "Quick execution attempts",
            "Balances speed vs price optimization"
        )
        benefits_table.add_row(
            "Progressive Pricing",
            "Gradual move toward market",
            "Increases fill probability each step"
        )
        benefits_table.add_row(
            "WebSocket Notifications",
            "Instant fill detection", 
            "Eliminates polling delays"
        )
        benefits_table.add_row(
            "Market Order Fallback",
            "Guaranteed execution",
            "Ensures order completion"
        )
        
        console.print(benefits_table)
        
        # Show timing analysis
        console.print(f"\n[bold blue]⏱️  Timing Analysis[/bold blue]")
        timing_table = Table()
        timing_table.add_column("Scenario", style="cyan")
        timing_table.add_column("Max Time", style="yellow")
        timing_table.add_column("Typical Time", style="green")
        
        timing_table.add_row("Fill at midpoint", "10 seconds", "< 1 second")
        timing_table.add_row("Fill at step 2 (10%)", "20 seconds", "10-15 seconds")
        timing_table.add_row("Fill at step 3 (20%)", "30 seconds", "20-25 seconds")
        timing_table.add_row("Fill at step 4 (30%)", "40 seconds", "30-35 seconds")
        timing_table.add_row("Market order fallback", "50 seconds", "40-45 seconds")
        
        console.print(timing_table)
        
        console.print(f"\n[bold green]✅ Progressive Limit Order Strategy Demo Complete![/bold green]")
        
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in progressive strategy demo: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_progressive_strategy()
