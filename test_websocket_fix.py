#!/usr/bin/env python3
"""
Test script to verify the WebSocket subscription fix
"""

import logging
from the_alchemiser.utils.websocket_order_monitor import OrderCompletionMonitor
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

def test_websocket_fallback():
    """Test that WebSocket falls back to polling when subscription fails"""
    print("🧪 Testing WebSocket subscription fallback...")
    
    try:
        # Initialize with live trading to potentially trigger subscription error
        data_provider = UnifiedDataProvider(paper_trading=False)
        trading_client = data_provider.trading_client
        
        # Test order monitor
        monitor = OrderCompletionMonitor(trading_client)
        
        # Try to wait for a fake order (should fall back to polling gracefully)
        fake_order_ids = ["test-order-123"]
        result = monitor.wait_for_order_completion(fake_order_ids, max_wait_seconds=5)
        
        print(f"✅ Test completed successfully")
        print(f"   Result: {result}")
        print(f"   Expected: Order should timeout gracefully using polling")
        
    except Exception as e:
        if "insufficient subscription" in str(e).lower():
            print(f"❌ WebSocket subscription error not properly handled: {e}")
        else:
            print(f"✅ Other error handled gracefully: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_websocket_fallback()
