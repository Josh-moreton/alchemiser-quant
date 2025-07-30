#!/usr/bin/env python3
"""
Test the Simple Order Manager to show its robustness and simplicity.
"""

import logging
from unittest.mock import Mock, MagicMock
from alpaca.trading.enums import OrderSide

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

from the_alchemiser.execution.alpaca_client import AlpacaClient


def test_simple_order_flow():
    """Test the simple, straightforward order flow."""
    print("🚀 Testing Simple Order Manager")
    
    # Mock dependencies
    mock_trading_client = Mock()
    mock_data_provider = Mock()
    
    # Create order manager
    order_manager = AlpacaClient(mock_trading_client, mock_data_provider)
    
    print("\n🧪 Test 1: Get current positions")
    # Mock position data
    mock_position1 = Mock()
    mock_position1.symbol = "AAPL"
    mock_position1.qty = "10.5"
    
    mock_position2 = Mock()
    mock_position2.symbol = "TSLA" 
    mock_position2.qty = "5.0"
    
    mock_trading_client.get_all_positions.return_value = [mock_position1, mock_position2]
    
    positions = order_manager.get_current_positions()
    print(f"   Current positions: {positions}")
    assert positions == {"AAPL": 10.5, "TSLA": 5.0}
    print("   ✅ Position retrieval works correctly")
    
    print("\n🧪 Test 2: Cancel existing orders")
    mock_trading_client.cancel_orders.return_value = None
    result = order_manager.cancel_all_orders()
    assert result == True
    mock_trading_client.cancel_orders.assert_called_once()
    print("   ✅ Order cancellation works correctly")
    
    print("\n🧪 Test 3: Liquidate entire position")
    mock_liquidation_order = Mock()
    mock_liquidation_order.id = "liquidation-123"
    mock_trading_client.close_position.return_value = mock_liquidation_order
    
    order_id = order_manager.liquidate_position("AAPL")
    assert order_id == "liquidation-123"
    mock_trading_client.close_position.assert_called_with("AAPL")
    print("   ✅ Position liquidation works correctly")
    
    print("\n🧪 Test 4: Place market order")
    mock_market_order = Mock()
    mock_market_order.id = "market-456"
    mock_trading_client.submit_order.return_value = mock_market_order
    
    order_id = order_manager.place_market_order("NVDA", OrderSide.BUY, qty=2.5)
    assert order_id == "market-456"
    print("   ✅ Market order placement works correctly")
    
    print("\n🧪 Test 5: Smart sell order (partial position)")
    # Reset mocks
    mock_trading_client.reset_mock()
    mock_trading_client.get_all_positions.return_value = [mock_position1, mock_position2]
    
    # Mock market order for partial sale
    mock_trading_client.submit_order.return_value = mock_market_order
    
    order_id = order_manager.place_smart_sell_order("AAPL", 5.0)  # Sell 5 out of 10.5 shares
    assert order_id == "market-456"
    print("   ✅ Partial position sale uses market order correctly")
    
    print("\n🧪 Test 6: Smart sell order (full position)")
    # Reset mocks
    mock_trading_client.reset_mock()
    mock_trading_client.get_all_positions.return_value = [mock_position1, mock_position2]
    mock_trading_client.close_position.return_value = mock_liquidation_order
    
    order_id = order_manager.place_smart_sell_order("AAPL", 10.5)  # Sell entire position
    assert order_id == "liquidation-123"
    mock_trading_client.close_position.assert_called_with("AAPL")
    print("   ✅ Full position sale uses liquidation API correctly")
    
    print("\n🧪 Test 7: Execute rebalance plan")
    # Mock current prices
    mock_data_provider.get_current_price.side_effect = lambda symbol: {
        "TECL": 50.0,
        "UVXY": 15.0
    }.get(symbol, 100.0)
    
    # Mock successful orders
    mock_buy_order1 = Mock()
    mock_buy_order1.id = "buy-tecl-789"
    mock_buy_order2 = Mock()
    mock_buy_order2.id = "buy-uvxy-790"
    
    mock_trading_client.submit_order.side_effect = [mock_buy_order1, mock_buy_order2]
    mock_trading_client.close_position.return_value = mock_liquidation_order
    
    # Test rebalance plan: sell AAPL, buy TECL and UVXY
    target_allocations = {
        "AAPL": 0.0,    # Sell entire position
        "TECL": 0.5,    # 50% allocation
        "UVXY": 0.5     # 50% allocation
    }
    
    results = order_manager.execute_rebalance_plan(target_allocations, 1000.0)
    
    print(f"   Rebalance results: {results}")
    assert results["AAPL"] == "liquidation-123"  # Liquidation order
    assert results["TECL"] == "buy-tecl-789"     # Buy order
    assert results["UVXY"] == "buy-uvxy-790"     # Buy order
    print("   ✅ Rebalance plan execution works correctly")


def test_error_handling():
    """Test error handling scenarios."""
    print("\n🧪 Testing Error Handling")
    
    mock_trading_client = Mock()
    mock_data_provider = Mock()
    order_manager = AlpacaClient(mock_trading_client, mock_data_provider)
    
    print("\n   Test: Selling non-existent position")
    mock_trading_client.get_all_positions.return_value = []
    
    order_id = order_manager.place_smart_sell_order("NONEXISTENT", 10.0)
    assert order_id is None
    print("   ✅ Correctly handles selling non-existent position")
    
    print("\n   Test: Invalid quantity")
    order_id = order_manager.place_market_order("AAPL", OrderSide.BUY, qty=0)
    assert order_id is None
    print("   ✅ Correctly handles invalid quantity")


def main():
    """Run all tests."""
    test_simple_order_flow()
    test_error_handling()
    
    print("\n" + "="*80)
    print("🎉 All tests passed! Simple Order Manager is robust and straightforward.")
    print("="*80)
    
    print("\n📋 Key Benefits of Simple Order Manager:")
    print("   • Uses Alpaca APIs directly - no complex retry logic")
    print("   • Liquidation API for full position sales (prevents overselling)")
    print("   • Clear error handling with fail-fast approach")
    print("   • Straightforward rebalancing workflow")
    print("   • Easy to understand and debug")
    print("   • Robust position validation before trading")


if __name__ == "__main__":
    main()
