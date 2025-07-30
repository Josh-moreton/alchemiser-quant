#!/usr/bin/env python3
"""
Test script for the new progressive limit order strategy.

This script demonstrates the enhanced limit order placement that:
1. Starts at the midpoint of bid/ask
2. Waits 10 seconds for fill  
3. Steps 10% toward less favorable price
4. Repeats until all steps exhausted
5. Finally places market order
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from rich.console import Console
from alpaca.trading.enums import OrderSide

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_progressive_limit_orders():
    """Test the new progressive limit order strategy."""
    console = Console()
    console.print("[bold green]🚀 Testing Progressive Limit Order Strategy[/bold green]")
    
    try:
        # Import our components
        from the_alchemiser.core.data.data_provider import UnifiedDataProvider
        from the_alchemiser.execution.smart_execution import SmartExecution
        
        # Initialize data provider
        console.print("[cyan]Initializing data provider with WebSocket pricing...[/cyan]")
        data_provider = UnifiedDataProvider(paper_trading=True, enable_real_time=True)
        
        # Wait for WebSocket connection
        console.print("[dim]Waiting for WebSocket connection...[/dim]")
        time.sleep(2)
        
        # Initialize order manager adapter
        console.print("[cyan]Initializing order manager adapter...[/cyan]")
        order_manager = SmartExecution(
            data_provider.trading_client, 
            data_provider,
            ignore_market_hours=True
        )
        
        # Test symbol
        test_symbol = "UVXY"
        
        # Get current bid/ask to show the progression
        console.print(f"\n[bold]Testing Progressive Strategy for {test_symbol}[/bold]")
        
        quote = data_provider.get_latest_quote(test_symbol)
        if quote and len(quote) >= 2:
            bid, ask = float(quote[0]), float(quote[1])
            midpoint = (bid + ask) / 2.0
            spread = ask - bid
            
            console.print(f"[dim]Current Market Data:[/dim]")
            console.print(f"  Bid: ${bid:.2f}")
            console.print(f"  Ask: ${ask:.2f}")
            console.print(f"  Midpoint: ${midpoint:.2f}")
            console.print(f"  Spread: ${spread:.2f}")
            
            # Show what the progressive strategy would do for BUY
            console.print(f"\n[bold cyan]BUY Order Progression (toward ask):[/bold cyan]")
            steps = [0.0, 0.1, 0.2, 0.3]
            for i, step_pct in enumerate(steps):
                limit_price = midpoint + (spread / 2 * step_pct)
                step_name = "Midpoint" if i == 0 else f"Step {i} ({step_pct*100:.0f}% toward ask)"
                console.print(f"  {step_name}: ${limit_price:.2f}")
            console.print(f"  Final: Market Order")
            
            # Show what the progressive strategy would do for SELL
            console.print(f"\n[bold red]SELL Order Progression (toward bid):[/bold red]")
            for i, step_pct in enumerate(steps):
                limit_price = midpoint - (spread / 2 * step_pct)
                step_name = "Midpoint" if i == 0 else f"Step {i} ({step_pct*100:.0f}% toward bid)"
                console.print(f"  {step_name}: ${limit_price:.2f}")
            console.print(f"  Final: Market Order")
        
        # Test small BUY order (this will actually place orders in paper trading)
        console.print(f"\n[bold yellow]⚠️  LIVE TEST: Placing small BUY order for {test_symbol}[/bold yellow]")
        console.print("[dim]This will place actual orders in paper trading mode[/dim]")
        
        # Small test order
        test_qty = 1.0  # 1 share
        
        # Place the progressive limit order
        console.print(f"\n[cyan]Executing progressive BUY limit order for {test_qty} shares of {test_symbol}...[/cyan]")
        
        order_id = order_manager.place_limit_or_market(
            symbol=test_symbol,
            qty=test_qty,
            side=OrderSide.BUY
        )
        
        if order_id:
            console.print(f"[green]✅ Order completed! Order ID: {order_id}[/green]")
        else:
            console.print(f"[red]❌ Order failed![/red]")
        
        console.print(f"\n[bold green]✅ Progressive Limit Order Strategy Test Complete![/bold green]")
        
        # Show performance summary
        console.print(f"\n[bold]Strategy Benefits:[/bold]")
        console.print(f"✓ Starts at midpoint for best execution")
        console.print(f"✓ Progressive steps toward less favorable price")
        console.print(f"✓ 10-second timeouts with WebSocket notifications")
        console.print(f"✓ Market order fallback ensures execution")
        console.print(f"✓ Optimized for both speed and price improvement")
        
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Test interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in progressive limit order test: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_progressive_limit_orders()
