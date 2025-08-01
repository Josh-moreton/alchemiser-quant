#!/usr/bin/env python3
"""
Better Orders Demo Script

Demonstrates how to use the enhanced execution system.
"""

def demo_better_orders():
    """Demonstrate better orders functionality."""
    print("🚀 Better Orders Demo")
    print("=" * 50)
    
    # 1. Configuration
    print("\n📋 1. Configuration")
    from the_alchemiser.config.better_orders_config import get_better_orders_config, update_better_orders_config
    
    # Update configuration
    update_better_orders_config(
        enabled=True,
        max_slippage_bps=20.0,
        aggressive_timeout_seconds=2.5
    )
    
    config = get_better_orders_config()
    print(f"✅ Better orders enabled: {config.enabled}")
    print(f"✅ Max slippage: {config.max_slippage_bps} bps")
    print(f"✅ Timeout: {config.aggressive_timeout_seconds}s")
    
    # 2. Symbol Classification
    print("\n🏷️ 2. Symbol Classification")
    test_symbols = ["TQQQ", "SPY", "AAPL", "QQQ", "MSFT", "TECL"]
    
    for symbol in test_symbols:
        should_use = config.should_use_better_orders(symbol)
        slippage = config.get_slippage_tolerance(symbol)
        print(f"{symbol:6} → Better orders: {should_use:5} | Slippage: {slippage:4.1f} bps")
    
    # 3. Market Timing Engine
    print("\n⏰ 3. Market Timing Engine")
    from the_alchemiser.utils.market_timing_utils import MarketOpenTimingEngine
    from datetime import datetime, time
    import pytz
    
    timing_engine = MarketOpenTimingEngine()
    
    # Test different times
    et_tz = pytz.timezone('US/Eastern')
    test_times = [
        datetime.now(et_tz).replace(hour=9, minute=31),   # 9:31 ET
        datetime.now(et_tz).replace(hour=9, minute=33),   # 9:33 ET  
        datetime.now(et_tz).replace(hour=10, minute=0),   # 10:00 ET
    ]
    
    for test_time in test_times:
        strategy = timing_engine.get_execution_strategy(test_time)
        should_execute = timing_engine.should_execute_immediately(4.0, strategy)  # 4¢ spread
        wait_time = timing_engine.get_wait_time_seconds(strategy, 4.0)
        
        print(f"{test_time.strftime('%H:%M')} ET → {strategy.value:15} | Execute: {should_execute:5} | Wait: {wait_time}s")
    
    # 4. Spread Assessment
    print("\n📊 4. Spread Assessment")
    from the_alchemiser.utils.spread_assessment import SpreadAssessment, SpreadQuality
    
    # Mock data provider for demo
    class MockDataProvider:
        def get_latest_quote(self, symbol):
            return (50.95, 50.98) if symbol == "TQQQ" else (100.99, 101.04)
    
    mock_provider = MockDataProvider()
    spread_assessor = SpreadAssessment(mock_provider)
    
    test_symbols = ["TQQQ", "AAPL"]
    for symbol in test_symbols:
        bid, ask = mock_provider.get_latest_quote(symbol)
        analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
        
        print(f"{symbol:6} → Bid: ${bid:6.2f} | Ask: ${ask:6.2f} | Spread: {analysis.spread_cents:4.1f}¢ ({analysis.spread_quality.value})")
    
    # 5. Aggressive Pricing
    print("\n💰 5. Aggressive Marketable Limit Pricing")
    from the_alchemiser.utils.smart_pricing_handler import SmartPricingHandler
    from alpaca.trading.enums import OrderSide
    
    pricing_handler = SmartPricingHandler(mock_provider)
    
    # Test aggressive pricing for both sides
    bid, ask = 50.95, 50.98
    
    buy_price = pricing_handler.get_aggressive_marketable_limit("TQQQ", OrderSide.BUY, bid, ask)
    sell_price = pricing_handler.get_aggressive_marketable_limit("TQQQ", OrderSide.SELL, bid, ask)
    
    print(f"TQQQ Market: ${bid:.2f} x ${ask:.2f}")
    print(f"BUY  aggressive limit: ${buy_price:.2f}  (ask + 1¢)")
    print(f"SELL aggressive limit: ${sell_price:.2f}  (bid - 1¢)")
    
    # 6. Portfolio Integration
    print("\n🎯 6. Portfolio Integration")
    print("Portfolio rebalancer now automatically uses:")
    print("  ✅ Better orders for leveraged ETFs (TQQQ, SPXL, etc.)")
    print("  ✅ Better orders for high-volume ETFs (SPY, QQQ, etc.)")
    print("  ✅ Standard execution for individual stocks")
    print("  ✅ Configuration-based symbol routing")
    print("  ✅ Symbol-specific slippage tolerance")
    
    # 7. Usage Example
    print("\n📝 7. Usage Example")
    print("""
# Direct usage in your code:
from the_alchemiser.execution.smart_execution import SmartExecution

# Create execution engine (with your real clients)
order_manager = SmartExecution(alpaca_client, data_provider)

# Place better order (automatically uses 5-step execution ladder)
order_id = order_manager.place_better_order(
    symbol="TQQQ",
    qty=100.0, 
    side=OrderSide.BUY,
    max_slippage_bps=20.0
)

# Portfolio rebalancing automatically uses better orders
target_portfolio = {"TQQQ": 0.6, "SPY": 0.4}
orders = trading_engine.rebalance_portfolio(target_portfolio)
""")
    
    print("\n🎉 Better Orders system is ready for production!")
    print("\nKey benefits:")
    print("  ⚡ 2-3 second execution timeouts")
    print("  🎯 Aggressive marketable limit pricing")
    print("  ⏰ Market open timing optimization")
    print("  📊 Spread-aware execution decisions")
    print("  🔧 Configuration-driven automation")
    print("  🛡️ Comprehensive fallback mechanisms")

if __name__ == "__main__":
    demo_better_orders()
