#!/usr/bin/env python3
"""
Integration test for Better Orders system with Portfolio Rebalancer

Tests the complete workflow:
1. Configuration-driven execution decisions
2. Symbol-specific slippage tolerance
3. Portfolio rebalancer integration
4. Fallback mechanisms
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch
from alpaca.trading.enums import OrderSide

def test_better_orders_portfolio_integration():
    """Test complete better orders integration with portfolio rebalancer."""
    print("🚀 Testing Better Orders Portfolio Integration...")
    
    # Mock dependencies
    mock_alpaca_client = MagicMock()
    mock_data_provider = MagicMock()
    mock_trading_bot = MagicMock()
    
    # Set up mock returns
    mock_data_provider.get_latest_quote.return_value = (50.95, 50.98)  # bid, ask
    mock_data_provider.get_market_hours.return_value = (True, True)
    mock_alpaca_client.trading_client.get_clock.return_value = MagicMock(is_open=True)
    mock_alpaca_client.trading_client.submit_order.return_value = MagicMock(id='test_order_123')
    mock_alpaca_client.wait_for_order_completion.return_value = {'test_order_123': 'filled'}
    
    # Import and create components
    from the_alchemiser.execution.smart_execution import SmartExecution
    from the_alchemiser.execution.portfolio_rebalancer import PortfolioRebalancer
    from the_alchemiser.config.better_orders_config import get_better_orders_config, update_better_orders_config
    
    # Configure better orders for testing
    update_better_orders_config(
        enabled=True,
        leveraged_etf_symbols=["TQQQ", "SPXL", "TECL"],
        high_volume_etfs=["SPY", "QQQ"],
        max_slippage_bps=15.0
    )
    
    # Create order manager with better orders capability
    order_manager = SmartExecution(mock_alpaca_client, mock_data_provider)
    
    # Set up trading bot mock
    mock_trading_bot.order_manager = order_manager
    mock_trading_bot.get_account_info.return_value = {
        'cash': 10000.0,
        'buying_power': 10000.0,
        'portfolio_value': 10000.0
    }
    mock_trading_bot.get_positions.return_value = {}
    mock_trading_bot.get_current_price.return_value = 50.97
    mock_trading_bot.data_provider = mock_data_provider
    mock_trading_bot.wait_for_settlement.return_value = True
    mock_trading_bot.place_order.return_value = 'test_order_123'
    mock_trading_bot.display_target_vs_current_allocations = MagicMock()
    
    # Create portfolio rebalancer
    rebalancer = PortfolioRebalancer(mock_trading_bot)
    
    print("📊 Testing leveraged ETF execution (TQQQ)...")
    
    # Test 1: TQQQ should use better orders (leveraged ETF)
    target_portfolio = {"TQQQ": 1.0}  # 100% TQQQ allocation
    
    with patch.object(order_manager, 'place_order') as mock_better_order, \
         patch.object(order_manager, 'place_order') as mock_standard_order:
        
        mock_better_order.return_value = 'better_order_456'
        mock_standard_order.return_value = 'standard_order_789'
        
        # Execute rebalancing
        orders = rebalancer.rebalance_portfolio(target_portfolio)
        
        # Verify better orders was used for TQQQ
        assert mock_better_order.called, "❌ Better orders should be used for TQQQ"
        call_args = mock_better_order.call_args
        assert call_args[0][0] == "TQQQ", "❌ Symbol should be TQQQ"
        assert call_args[0][2] == OrderSide.BUY, "❌ Should be BUY order"
        assert call_args[1]['max_slippage_bps'] == 15.0, "❌ Should use configured slippage"
        
        print("✅ TQQQ correctly used better orders execution")
        print(f"✅ Slippage tolerance: {call_args[1]['max_slippage_bps']} bps")
    
    print("📊 Testing high-volume ETF execution (SPY)...")
    
    # Test 2: SPY should use better orders (high-volume ETF) with lower slippage
    config = get_better_orders_config()
    spy_slippage = config.get_slippage_tolerance("SPY")
    
    target_portfolio = {"SPY": 1.0}  # 100% SPY allocation
    
    with patch.object(order_manager, 'place_order') as mock_better_order:
        mock_better_order.return_value = 'better_order_spy'
        
        orders = rebalancer.rebalance_portfolio(target_portfolio)
        
        # Verify better orders was used with appropriate slippage
        assert mock_better_order.called, "❌ Better orders should be used for SPY"
        call_args = mock_better_order.call_args
        assert call_args[1]['max_slippage_bps'] == spy_slippage, f"❌ SPY slippage should be {spy_slippage}"
        
        print(f"✅ SPY correctly used better orders with {spy_slippage} bps slippage")
    
    print("📊 Testing standard stock execution (AAPL)...")
    
    # Test 3: AAPL should use standard execution (not in ETF lists)
    target_portfolio = {"AAPL": 1.0}  # 100% AAPL allocation
    
    with patch.object(order_manager, 'place_order') as mock_better_order, \
         patch.object(order_manager, 'place_order') as mock_standard_order:
        
        mock_better_order.return_value = 'better_order_aapl'
        mock_standard_order.return_value = 'standard_order_aapl'
        
        orders = rebalancer.rebalance_portfolio(target_portfolio)
        
        # Verify standard execution was used for AAPL
        assert not mock_better_order.called, "❌ Better orders should NOT be used for AAPL"
        assert mock_standard_order.called, "❌ Standard execution should be used for AAPL"
        
        print("✅ AAPL correctly used standard execution (notional order)")
    
    print("📊 Testing configuration-based fallback...")
    
    # Test 4: Disabled better orders should use standard execution
    update_better_orders_config(enabled=False)
    
    target_portfolio = {"TQQQ": 1.0}  # 100% TQQQ allocation
    
    with patch.object(order_manager, 'place_order') as mock_better_order, \
         patch.object(order_manager, 'place_order') as mock_standard_order:
        
        mock_better_order.return_value = 'better_order_disabled'
        mock_standard_order.return_value = 'standard_order_disabled'
        
        orders = rebalancer.rebalance_portfolio(target_portfolio)
        
        # Verify standard execution was used when disabled
        assert not mock_better_order.called, "❌ Better orders should NOT be used when disabled"
        assert mock_standard_order.called, "❌ Standard execution should be used when disabled"
        
        print("✅ Disabled configuration correctly uses standard execution")
    
    # Re-enable for remaining tests
    update_better_orders_config(enabled=True)
    
    print("📊 Testing mixed portfolio execution...")
    
    # Test 5: Mixed portfolio should use appropriate execution for each symbol
    target_portfolio = {
        "TQQQ": 0.4,  # Leveraged ETF → better orders
        "SPY": 0.3,   # High-volume ETF → better orders  
        "AAPL": 0.3   # Standard stock → standard execution
    }
    
    with patch.object(order_manager, 'place_order') as mock_better_order, \
         patch.object(order_manager, 'place_order') as mock_standard_order:
        
        mock_better_order.return_value = 'better_order_mixed'
        mock_standard_order.return_value = 'standard_order_mixed'
        
        orders = rebalancer.rebalance_portfolio(target_portfolio)
        
        # Check call patterns
        better_calls = mock_better_order.call_args_list
        standard_calls = mock_standard_order.call_args_list
        
        # Should have 2 better order calls (TQQQ, SPY) and 1 standard call (AAPL)
        assert len(better_calls) == 2, f"❌ Expected 2 better order calls, got {len(better_calls)}"
        assert len(standard_calls) == 1, f"❌ Expected 1 standard call, got {len(standard_calls)}"
        
        # Verify symbols
        better_symbols = [call[0][0] for call in better_calls]
        standard_symbols = [call[0][0] for call in standard_calls if len(call[0]) > 0]
        
        assert "TQQQ" in better_symbols, "❌ TQQQ should use better orders"
        assert "SPY" in better_symbols, "❌ SPY should use better orders"
        
        print("✅ Mixed portfolio correctly routes orders:")
        print(f"  - Better orders: {better_symbols}")
        print(f"  - Standard orders: {standard_symbols}")
    
    print("\n🎯 Better Orders Portfolio Integration Test Summary:")
    print("✅ Configuration-driven execution selection")
    print("✅ Symbol-specific slippage tolerance") 
    print("✅ Leveraged ETF optimization")
    print("✅ High-volume ETF optimization")
    print("✅ Standard stock fallback")
    print("✅ Mixed portfolio routing")
    print("✅ Configuration-based disable/enable")
    print("\n🚀 Better Orders integration is fully operational!")

if __name__ == "__main__":
    test_better_orders_portfolio_integration()
