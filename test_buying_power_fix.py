#!/usr/bin/env python3
"""
Quick test to verify the buying power calculation fix is working correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unittest.mock import Mock, patch
from src.execution.alpaca_trader import AlpacaTradingBot

def test_buying_power_calculation():
    """Test that rebalance_portfolio uses buying_power instead of cash for purchase calculations"""
    
    bot = AlpacaTradingBot("fake_key", "fake_secret", paper=True)
    
    # Mock the account data with different cash vs buying_power values (like the real scenario)
    mock_account = Mock()
    mock_account.cash = "98.69"  # High cash
    mock_account.buying_power = "14.28"  # Low buying power (the real constraint)
    mock_account.portfolio_value = "100.00"
    
    # Mock positions - empty to force purchases
    mock_positions = {}
    
    # Mock target portfolio wanting to buy LEU
    target_portfolio = {"LEU": 1.0}  # 100% allocation to LEU
    
    # Mock current price
    mock_price = 10.0
    
    with patch.object(bot.api, 'get_account', return_value=mock_account), \
         patch.object(bot.api, 'list_positions', return_value=[]), \
         patch.object(bot, 'get_current_price', return_value=mock_price), \
         patch.object(bot, 'place_order', return_value="test_order_123") as mock_place_order:
        
        # Execute rebalancing
        result = bot.rebalance_portfolio(target_portfolio)
        
        # Verify that an order was attempted
        print(f"Result: {result}")
        print(f"place_order called: {mock_place_order.called}")
        
        if mock_place_order.called:
            call_args = mock_place_order.call_args
            symbol, quantity, side = call_args[0]
            
            # Calculate expected maximum quantity based on buying_power (not cash)
            max_buyable_value = 14.28  # Should use buying_power, not cash (98.69)
            expected_max_qty = max_buyable_value / mock_price
            
            print(f"Order details: symbol={symbol}, qty={quantity}, side={side}")
            print(f"Expected max quantity based on buying_power: {expected_max_qty}")
            print(f"Total order value: {quantity * mock_price}")
            
            # Verify the order respects buying power limits
            order_value = quantity * mock_price
            assert order_value <= 14.28 + 0.01, f"Order value {order_value} exceeds buying power 14.28"
            print("✅ Order respects buying power limits!")
            
        else:
            print("❌ No order was placed - this might indicate an issue")

if __name__ == "__main__":
    test_buying_power_calculation()
    print("Test completed!")
