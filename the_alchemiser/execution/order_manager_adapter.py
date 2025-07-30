#!/usr/bin/env python3
"""
OrderManager Compatibility Adapter for SimpleOrderManager.

This adapter provides the same interface as the complex OrderManager but uses
SimpleOrderManager internally for much more reliable order placement.
"""

import logging
import time
from typing import Dict, List, Optional
from alpaca.trading.enums import OrderSide
from alpaca.trading.client import TradingClient

from the_alchemiser.execution.simple_order_manager import SimpleOrderManager


def is_market_open(trading_client: TradingClient) -> bool:
    """Check if the market is currently open."""
    try:
        clock = trading_client.get_clock()
        return getattr(clock, 'is_open', False)
    except Exception:
        return False


class OrderManagerAdapter:
    """
    Adapter to make SimpleOrderManager compatible with existing AlpacaTradingBot code.
    
    This provides the same interface as the old OrderManager but uses SimpleOrderManager
    internally for much more reliable order placement.
    """
    
    def __init__(self, trading_client, data_provider, ignore_market_hours=False, config=None):
        """Initialize with same signature as old OrderManager for compatibility."""
        
        self.config = config or {}
        validate_buying_power = self.config.get('validate_buying_power', False)
        
        self.simple_order_manager = SimpleOrderManager(trading_client, data_provider, validate_buying_power)
        self.ignore_market_hours = ignore_market_hours
        
        # OrderManagerAdapter initialized silently
    
    def place_safe_sell_order(
        self,
        symbol: str,
        target_qty: float,
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: Optional[float] = None
    ) -> Optional[str]:
        """
        Place a safe sell order - delegates to SimpleOrderManager.place_smart_sell_order.
        
        This method provides the same interface as the old OrderManager but uses
        the much more reliable SimpleOrderManager internally.
        """
        # Safe sell order execution
        
        # The SimpleOrderManager handles all the safety checks internally
        return self.simple_order_manager.place_smart_sell_order(symbol, target_qty)
    
    def place_limit_or_market(
        self, 
        symbol: str, 
        qty: float, 
        side: OrderSide, 
        max_retries: int = 3, 
        poll_timeout: int = 30, 
        poll_interval: float = 2.0, 
        slippage_bps: Optional[float] = None,
        notional: Optional[float] = None
    ) -> Optional[str]:
        """
        Place progressive limit order starting at midpoint, stepping toward less favorable price.
        
        Strategy:
        1. Start at midpoint of bid/ask
        2. Wait 10 seconds for fill
        3. Step 10% toward less favorable price (toward ask for BUY, toward bid for SELL)
        4. Repeat steps until reaching the unfavorable extreme
        5. Finally place market order if all limit attempts fail
        """
        import time
        
        # Handle both string and OrderSide enum inputs
        side_str = side.value if hasattr(side, 'value') else str(side)
        
        # Convert string inputs to OrderSide enum if needed
        if isinstance(side, str):
            side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        
        # Handle notional orders for BUY by converting to quantity
        if side == OrderSide.BUY and notional is not None:
            try:
                current_price = self.simple_order_manager.data_provider.get_current_price(symbol)
                if current_price <= 0:
                    logging.warning(f"Invalid price for {symbol}, falling back to market order")
                    return self.simple_order_manager.place_market_order(symbol, side, notional=notional)
                
                # Calculate max quantity we can afford, round down to 6 decimals, then scale to 99%
                raw_qty = notional / current_price
                rounded_qty = int(raw_qty * 1e6) / 1e6  # Round down to 6 decimals
                scaled_qty = rounded_qty * 0.99  # Scale to 99% to avoid buying power issues
                
                if scaled_qty <= 0:
                    logging.warning(f"Calculated quantity too small for {symbol}, falling back to market order")
                    return self.simple_order_manager.place_market_order(symbol, side, notional=notional)
                
                qty = scaled_qty
                
            except Exception as e:
                logging.warning(f"Error calculating quantity for {symbol}: {e}, falling back to market order")
                return self.simple_order_manager.place_market_order(symbol, side, notional=notional)
        elif side == OrderSide.BUY:
            # For quantity orders, round down to 6 decimals and scale to 99%
            rounded_qty = int(qty * 1e6) / 1e6
            qty = rounded_qty * 0.99
        
        # For SELL notional orders, use market order (can't easily implement progressive limits)
        if side == OrderSide.SELL and notional is not None:
            return self.simple_order_manager.place_market_order(symbol, side, notional=notional)
        
        # Get bid/ask for progressive limit order strategy
        try:
            quote = self.simple_order_manager.data_provider.get_latest_quote(symbol)
            if not quote or len(quote) < 2:
                # No quote available, use market order
                from rich.console import Console
                Console().print(f"[yellow]No bid/ask quote available for {symbol}, using market order[/yellow]")
                if notional is not None:
                    return self.simple_order_manager.place_market_order(symbol, side, notional=notional)
                else:
                    return self.simple_order_manager.place_market_order(symbol, side, qty=qty)
            
            bid = float(quote[0])
            ask = float(quote[1])
            
            if not (bid > 0 and ask > 0 and ask > bid):
                # Invalid quote, use market order
                from rich.console import Console
                Console().print(f"[yellow]Invalid bid/ask quote for {symbol} (bid=${bid:.2f}, ask=${ask:.2f}), using market order[/yellow]")
                if notional is not None:
                    return self.simple_order_manager.place_market_order(symbol, side, notional=notional)
                else:
                    return self.simple_order_manager.place_market_order(symbol, side, qty=qty)
            
            # Calculate midpoint and spread
            midpoint = (bid + ask) / 2.0
            spread = ask - bid
            
            from rich.console import Console
            console = Console()
            
            # Progressive limit order strategy
            console.print(f"[cyan]Starting progressive limit order for {side.value} {symbol}[/cyan]")
            console.print(f"[dim]Bid: ${bid:.2f}, Ask: ${ask:.2f}, Midpoint: ${midpoint:.2f}, Spread: ${spread:.2f}[/dim]")
            
            # Define the steps: 0%, 10%, 20%, 30% toward unfavorable price
            steps = [0.0, 0.1, 0.2, 0.3]
            
            for step_idx, step_pct in enumerate(steps):
                # Calculate limit price for this step
                if side == OrderSide.BUY:
                    # For BUY: start at midpoint, step toward ask (less favorable)
                    limit_price = midpoint + (spread / 2 * step_pct)
                    direction_desc = "toward ask"
                else:
                    # For SELL: start at midpoint, step toward bid (less favorable)
                    limit_price = midpoint - (spread / 2 * step_pct)
                    direction_desc = "toward bid"
                
                # Round to cents
                limit_price = round(limit_price, 2)
                
                # Display step information
                step_name = "Midpoint" if step_idx == 0 else f"Step {step_idx} ({step_pct*100:.0f}% {direction_desc})"
                color = "cyan" if side == OrderSide.BUY else "red"
                console.print(f"[{color}]{step_name}: {side.value} {symbol} @ ${limit_price:.2f}[/{color}]")
                
                # Place limit order
                limit_order_id = self.simple_order_manager.place_limit_order(
                    symbol, qty, side, limit_price
                )
                
                if not limit_order_id:
                    console.print(f"[yellow]Failed to place limit order at ${limit_price:.2f}[/yellow]")
                    continue
                
                # Wait 10 seconds for fill using WebSocket notifications
                console.print(f"[dim]Waiting 10 seconds for fill via WebSocket...[/dim]")
                
                order_results = self.simple_order_manager.wait_for_order_completion(
                    [limit_order_id], max_wait_seconds=10
                )
                
                final_status = order_results.get(limit_order_id, '').lower()
                if 'filled' in final_status:
                    console.print(f"[green]✓ {side.value} {symbol} filled @ ${limit_price:.2f} ({step_name})[/green]")
                    return limit_order_id
                else:
                    console.print(f"[yellow]{step_name} not filled ({final_status}), trying next step...[/yellow]")
                    # Order was automatically cancelled by wait_for_order_completion timeout
            
            # All limit order steps failed, use market order as final fallback
            console.print(f"[yellow]All progressive limit orders failed for {symbol}, placing market order[/yellow]")
            
        except Exception as e:
            logging.warning(f"Error in progressive limit order strategy for {symbol}: {e}, using market order")
        
        # Final fallback to market order
        if notional is not None:
            return self.simple_order_manager.place_market_order(symbol, side, notional=notional)
        else:
            return self.simple_order_manager.place_market_order(symbol, side, qty=qty)
    
    def wait_for_settlement(
        self, 
        sell_orders: List[Dict], 
        max_wait_time: int = 60, 
        poll_interval: float = 2.0
    ) -> bool:
        """
        Wait for order settlement - delegates to SimpleOrderManager.wait_for_order_completion.
        """
        if not sell_orders:
            return True
            
        # Extract only valid string order IDs
        order_ids: List[str] = []
        for order in sell_orders:
            order_id = order.get('order_id')
            if order_id is not None and isinstance(order_id, str):
                order_ids.append(order_id)
                
        # If we had orders but no valid order IDs, that's a failure
        if not order_ids:
            logging.warning("No valid order IDs found in settlement data")
            return False
            
        # Wait for order settlement
        
        # Use the SimpleOrderManager's order completion waiting
        completion_statuses = self.simple_order_manager.wait_for_order_completion(
            order_ids, max_wait_time
        )
        
        # Consider orders settled if they're filled, canceled, or rejected
        # Handle both enum values and string representations
        settled_count = sum(
            1 for status in completion_statuses.values() 
            if status in ['filled', 'canceled', 'rejected', 'expired'] or
               str(status).lower() in ['filled', 'canceled', 'rejected', 'expired'] or
               status in ['OrderStatus.FILLED', 'OrderStatus.CANCELED', 'OrderStatus.REJECTED', 'OrderStatus.EXPIRED']
        )
        
        success = settled_count == len(order_ids)
        if success:
            pass  # All orders settled successfully
        else:
            logging.warning(f"Only {settled_count}/{len(order_ids)} orders settled")
            
        return success
    
    def liquidate_position(self, symbol: str) -> Optional[str]:
        """Liquidate position - delegates to SimpleOrderManager."""
        return self.simple_order_manager.liquidate_position(symbol)
    
    def get_position_qty(self, symbol: str) -> float:
        """Get position quantity - delegates to SimpleOrderManager."""
        positions = self.simple_order_manager.get_current_positions()
        return positions.get(symbol, 0.0)
    
    def calculate_dynamic_limit_price(self, side: OrderSide, bid: float, ask: float, 
                                     step: int = 1, tick_size: float = 0.01, 
                                     max_steps: int = 5) -> float:
        """
        Calculate a dynamic limit price based on the bid-ask spread and step.
        
        Test expects:
        - BUY: bid=99.0, ask=101.0, step=1, tick_size=0.2, max_steps=3 -> 100.2
        - SELL: bid=99.0, ask=101.0, step=2, tick_size=0.5, max_steps=3 -> 99.0
        
        Args:
            side: OrderSide.BUY or OrderSide.SELL
            bid: Current bid price
            ask: Current ask price  
            step: Step number (1-based)
            tick_size: Minimum price increment
            max_steps: Maximum number of steps
            
        Returns:
            Calculated limit price
        """
        mid_price = (bid + ask) / 2.0
        
        if side == OrderSide.BUY:
            # For buy orders, step toward ask from mid
            price = mid_price + (step * tick_size)
        else:
            # For sell orders, step toward bid from mid
            price = mid_price - (step * tick_size)
        
        # Round to nearest tick
        return round(price / tick_size) * tick_size
