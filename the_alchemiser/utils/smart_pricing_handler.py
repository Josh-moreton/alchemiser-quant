#!/usr/bin/env python3
"""
Smart Pricing Handler

This module provides intelligent pricing strategies based on market conditions,
bid/ask spreads, and order aggressiveness settings.
"""

import logging
from typing import Optional
from alpaca.trading.enums import OrderSide


class SmartPricingHandler:
    """
    Handles intelligent price calculation for limit orders.
    """
    
    def __init__(self, data_provider):
        """Initialize with data provider for market data."""
        self.data_provider = data_provider
    
    def get_smart_limit_price(self, symbol: str, side: OrderSide, aggressiveness: float = 0.5) -> Optional[float]:
        """
        Get a smart limit price based on current bid/ask.
        
        Args:
            symbol: Stock symbol
            side: OrderSide.BUY or OrderSide.SELL
            aggressiveness: 0.0 = most conservative, 1.0 = most aggressive (market price)
            
        Returns:
            Calculated limit price, or None if data unavailable
        """
        try:
            bid, ask = self.data_provider.get_latest_quote(symbol)
            
            if bid <= 0 or ask <= 0 or bid >= ask:
                logging.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
                return None
                
            if side == OrderSide.BUY:
                # For buying: bid = conservative, ask = aggressive
                price = bid + (ask - bid) * aggressiveness
            else:
                # For selling: ask = conservative, bid = aggressive  
                price = ask - (ask - bid) * aggressiveness
                
            return round(price, 2)
            
        except Exception as e:
            logging.error(f"Error getting smart limit price for {symbol}: {e}")
            return None

    def get_progressive_pricing(self, symbol: str, side: OrderSide, step: int = 1, total_steps: int = 4) -> Optional[float]:
        """
        Get progressive pricing for multi-step limit order strategies.
        
        Args:
            symbol: Stock symbol
            side: OrderSide.BUY or OrderSide.SELL
            step: Current step (1-based)
            total_steps: Total number of steps
            
        Returns:
            Calculated price for this step, or None if data unavailable
        """
        try:
            bid, ask = self.data_provider.get_latest_quote(symbol)
            
            if bid <= 0 or ask <= 0 or bid >= ask:
                logging.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
                return None
            
            midpoint = (bid + ask) / 2.0
            spread = ask - bid
            
            # Calculate step percentage (0% to 30% through spread)
            step_percentage = min((step - 1) / max(total_steps - 1, 1) * 0.3, 0.3)
            
            if side == OrderSide.BUY:
                # Step from midpoint toward ask
                price = midpoint + (spread / 2 * step_percentage)
            else:
                # Step from midpoint toward bid
                price = midpoint - (spread / 2 * step_percentage)
                
            return round(price, 2)
            
        except Exception as e:
            logging.error(f"Error getting progressive price for {symbol}: {e}")
            return None

    def get_aggressive_sell_price(self, symbol: str, aggressiveness: float = 0.85) -> Optional[float]:
        """
        Get aggressive sell pricing for quick liquidation (favors speed over price).
        
        Args:
            symbol: Stock symbol
            aggressiveness: How aggressive (0.85 = 85% toward bid from ask)
            
        Returns:
            Calculated aggressive sell price, or None if data unavailable
        """
        return self.get_smart_limit_price(symbol, OrderSide.SELL, aggressiveness)

    def get_conservative_buy_price(self, symbol: str, aggressiveness: float = 0.75) -> Optional[float]:
        """
        Get conservative buy pricing for better fill prices (favors price over speed).
        
        Args:
            symbol: Stock symbol
            aggressiveness: How aggressive (0.75 = 75% toward ask from bid)
            
        Returns:
            Calculated conservative buy price, or None if data unavailable
        """
        return self.get_smart_limit_price(symbol, OrderSide.BUY, aggressiveness)
