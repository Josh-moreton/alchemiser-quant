#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Demo script showing extended hours execution strategy.

This demonstrates the new extended hours trading strategy that:
- Places buy orders at ask price for immediate execution
- Places sell orders at bid price for immediate execution  
- No repricing or repegging - just waits for fills
- Bypasses complex liquidity analysis during extended hours
"""

import asyncio
from decimal import Decimal
from unittest.mock import MagicMock

from the_alchemiser.execution_v2.core.extended_hours_strategy import ExtendedHoursExecutionStrategy
from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartExecutionStrategy,
    SmartOrderRequest,
)
from the_alchemiser.shared.types.market_data import QuoteModel


def demo_extended_hours_strategy():
    """Demonstrate the extended hours execution strategy."""
    print("🌙 Extended Hours Trading Strategy Demo")
    print("=" * 50)
    
    # Mock alpaca manager with extended hours enabled
    mock_alpaca_manager = MagicMock()
    mock_alpaca_manager.extended_hours_enabled = True
    
    # Create the extended hours strategy
    strategy = ExtendedHoursExecutionStrategy(mock_alpaca_manager)
    
    print(f"Extended hours active: {strategy.is_extended_hours_active()}")
    print()
    
    # Show how orders are routed differently during extended hours
    print("📊 Order Routing Logic:")
    print("- BUY orders: placed at ASK price (immediate execution)")
    print("- SELL orders: placed at BID price (immediate execution)")
    print("- No repricing or repegging")
    print("- DAY time-in-force for extended hours compatibility")
    print()


async def demo_smart_execution_integration():
    """Demonstrate how SmartExecutionStrategy integrates with extended hours."""
    print("🔗 Smart Execution Integration Demo")
    print("=" * 50)
    
    # Mock alpaca manager with extended hours enabled
    mock_alpaca_manager = MagicMock()
    mock_alpaca_manager.extended_hours_enabled = True
    
    # Mock successful order result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.order_id = "EH_ORDER_123"
    mock_alpaca_manager.place_limit_order.return_value = mock_result
    
    # Create smart execution strategy (which includes extended hours strategy)
    smart_strategy = SmartExecutionStrategy(
        alpaca_manager=mock_alpaca_manager,
        pricing_service=None,
        config=None,
    )
    
    # Mock quote data for demonstration
    mock_quote = QuoteModel(
        symbol="AAPL",
        bid_price=150.25,
        ask_price=150.35,
        bid_size=100.0,
        ask_size=200.0,
        timestamp=None,
    )
    
    # Mock the extended hours strategy's quote method
    smart_strategy.extended_hours_strategy._get_current_quote = mock_quote_async(mock_quote)
    
    print("📈 Example: Extended Hours BUY Order for AAPL")
    print(f"   Quote: BID ${mock_quote.bid_price} / ASK ${mock_quote.ask_price}")
    
    # Create a buy order request
    buy_request = SmartOrderRequest(
        symbol="AAPL",
        side="BUY",
        quantity=Decimal("10"),
        correlation_id="demo_buy_123",
    )
    
    # Execute the order
    result = await smart_strategy.place_smart_order(buy_request)
    
    print(f"   ✅ Order placed: {result.order_id}")
    print(f"   💰 Execution price: ${result.final_price} (ASK price)")
    print(f"   🎯 Strategy used: {result.execution_strategy}")
    print(f"   🔄 Repegs used: {result.repegs_used}")
    print()
    
    print("📉 Example: Extended Hours SELL Order for AAPL")
    
    # Create a sell order request
    sell_request = SmartOrderRequest(
        symbol="AAPL",
        side="SELL",
        quantity=Decimal("5"),
        correlation_id="demo_sell_456",
    )
    
    # Execute the order
    result = await smart_strategy.place_smart_order(sell_request)
    
    print(f"   ✅ Order placed: {result.order_id}")
    print(f"   💰 Execution price: ${result.final_price} (BID price)")
    print(f"   🎯 Strategy used: {result.execution_strategy}")
    print(f"   🔄 Repegs used: {result.repegs_used}")
    print()


def demo_configuration():
    """Show how to enable extended hours trading."""
    print("⚙️ Configuration Demo")
    print("=" * 50)
    
    print("To enable extended hours trading, set the environment variable:")
    print("   ALPACA__ENABLE_EXTENDED_HOURS=true")
    print()
    print("Supported values: true, false, 1, 0, yes, no")
    print("Default: false (disabled)")
    print()
    print("Example .env file entry:")
    print("   # Enable extended hours trading")
    print("   ALPACA__ENABLE_EXTENDED_HOURS=true")
    print()


def mock_quote_async(quote):
    """Helper to create async mock that returns a quote."""
    async def _get_quote(*args, **kwargs):
        return quote
    return _get_quote


async def main():
    """Run the demo."""
    print("🚀 Extended Hours Trading Strategy Implementation")
    print("=" * 60)
    print()
    
    demo_extended_hours_strategy()
    print()
    
    await demo_smart_execution_integration()
    print()
    
    demo_configuration()
    
    print("🎉 Demo completed!")
    print()
    print("Key Benefits:")
    print("- Simple bid/ask execution during extended hours")
    print("- No complex repricing logic that might fail")
    print("- Immediate execution at market prices")
    print("- Proper integration with existing smart execution system")


if __name__ == "__main__":
    asyncio.run(main())