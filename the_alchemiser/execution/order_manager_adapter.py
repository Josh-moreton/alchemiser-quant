#!/usr/bin/env python3
"""
OrderManager Compatibility Adapter for SimpleOrderManager.

This adapter provides the same interface as the complex OrderManager but uses
SimpleOrderManager internally for much more reliable order placement.
"""

import logging
from typing import Dict, List, Optional
from alpaca.trading.enums import OrderSide

from the_alchemiser.execution.simple_order_manager import SimpleOrderManager


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
        logging.info(f"🔄 Market order: {side.value} {symbol} {qty} shares")
        
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
