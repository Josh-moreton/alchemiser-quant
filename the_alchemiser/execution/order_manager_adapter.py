#!/usr/bin/env python3
"""
OrderManager Compatibility Adapter for SimpleOrderManager.

This adapter provides the same interface as the complex OrderManager but uses
SimpleOrderManager internally for much more reliable order placement.
"""

import logging
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
        
        self.simple_order_manager = SimpleOrderManager(trading_client, data_provider)
        self.ignore_market_hours = ignore_market_hours
        self.config = config or {}
        
        logging.info("✅ OrderManagerAdapter initialized with SimpleOrderManager backend")
    
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
        logging.info(f"🔄 Safe sell order: {symbol} {target_qty} shares")
        
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
        slippage_bps: Optional[float] = None
    ) -> Optional[str]:
        """
        Place limit or market order - delegates to SimpleOrderManager.place_market_order.
        
        For simplicity and reliability, we use market orders which execute immediately.
        """
        # Handle both string and OrderSide enum inputs
        side_str = side.value if hasattr(side, 'value') else str(side)
        logging.info(f"🔄 Market order: {side_str} {symbol} {qty} shares")
        
        # Convert string inputs to OrderSide enum if needed
        if isinstance(side, str):
            side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        
        # Use market orders for immediate execution and simplicity
        return self.simple_order_manager.place_market_order(symbol, qty, side)
    
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
                
        if not order_ids:
            return True
            
        logging.info(f"⏳ Waiting for settlement of {len(order_ids)} orders...")
        
        # Use the SimpleOrderManager's order completion waiting
        completion_statuses = self.simple_order_manager.wait_for_order_completion(
            order_ids, max_wait_time
        )
        
        # Consider orders settled if they're filled, canceled, or rejected
        settled_count = sum(
            1 for status in completion_statuses.values() 
            if status in ['filled', 'canceled', 'rejected', 'expired']
        )
        
        success = settled_count == len(order_ids)
        if success:
            logging.info(f"✅ All {len(order_ids)} orders settled successfully")
        else:
            logging.warning(f"⚠️ Only {settled_count}/{len(order_ids)} orders settled")
            
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
