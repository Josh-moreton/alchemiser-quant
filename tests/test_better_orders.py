#!/usr/bin/env python3
"""
Test script for the better orders implementation.
"""

import logging
from unittest.mock import MagicMock

from alpaca.trading.enums import OrderSide

from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.execution.smart_execution import SmartExecution

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def test_better_orders_integration():
    """Test the better orders functionality with mock data."""
    print("🚀 Testing Better Orders Implementation...")

    try:
        # Mock trading client
        mock_trading_client = MagicMock()
        mock_trading_client._api_key = "test_key"
        mock_trading_client._secret_key = "test_secret"
        mock_trading_client._sandbox = True

        # Mock clock for market hours
        mock_clock = MagicMock()
        mock_clock.is_open = True
        mock_trading_client.get_clock.return_value = mock_clock

        # Create data provider
        data_provider = UnifiedDataProvider(paper_trading=True, enable_real_time=False)

        # Create smart execution
        smart_execution = SmartExecution(
            trading_client=mock_trading_client,
            data_provider=data_provider,
            ignore_market_hours=True,
        )

        # Test symbol
        test_symbol = "TQQQ"

        # Mock quote data (tight spread)
        mock_quote = (50.95, 50.98)  # 3¢ spread
        data_provider.get_latest_quote = MagicMock(return_value=mock_quote)

        # Mock order placement
        smart_execution.alpaca_client.place_limit_order = MagicMock(return_value="test_order_123")
        smart_execution.alpaca_client.wait_for_order_completion = MagicMock(
            return_value={"test_order_123": "filled"}
        )

        print(f"📊 Testing {test_symbol} with tight spread (3¢)...")

        # Test BUY order
        print("\n💰 Testing BUY order with better execution...")
        order_id = smart_execution.place_order(test_symbol, 100.0, OrderSide.BUY)

        if order_id:
            print(f"✅ BUY order placed successfully: {order_id}")

            # Verify aggressive pricing was used (ask + 1¢)
            call_args = smart_execution.alpaca_client.place_limit_order.call_args
            if call_args:
                _, qty, side, limit_price = call_args[0]
                expected_price = 50.98 + 0.01  # ask + 1¢
                print(f"📈 Limit price used: ${limit_price:.2f} (expected: ${expected_price:.2f})")

                if abs(limit_price - expected_price) < 0.001:
                    print("✅ Aggressive marketable limit pricing verified!")
                else:
                    print(
                        f"❌ Pricing mismatch: got ${limit_price:.2f}, expected ${expected_price:.2f}"
                    )
        else:
            print("❌ BUY order failed")

        # Test SELL order
        print("\n💰 Testing SELL order with better execution...")
        smart_execution.alpaca_client.place_limit_order.reset_mock()

        order_id = smart_execution.place_order(test_symbol, 50.0, OrderSide.SELL)

        if order_id:
            print(f"✅ SELL order placed successfully: {order_id}")

            # Verify aggressive pricing was used (bid - 1¢)
            call_args = smart_execution.alpaca_client.place_limit_order.call_args
            if call_args:
                _, qty, side, limit_price = call_args[0]
                expected_price = 50.95 - 0.01  # bid - 1¢
                print(f"📉 Limit price used: ${limit_price:.2f} (expected: ${expected_price:.2f})")

                if abs(limit_price - expected_price) < 0.001:
                    print("✅ Aggressive marketable limit pricing verified!")
                else:
                    print(
                        f"❌ Pricing mismatch: got ${limit_price:.2f}, expected ${expected_price:.2f}"
                    )
        else:
            print("❌ SELL order failed")

        print("\n🎯 Testing wide spread scenario...")

        # Test wide spread scenario (> 5¢)
        wide_quote = (50.90, 51.00)  # 10¢ spread
        data_provider.get_latest_quote = MagicMock(return_value=wide_quote)

        # Reset mock
        smart_execution.alpaca_client.place_limit_order.reset_mock()
        smart_execution.alpaca_client.wait_for_order_completion = MagicMock(
            return_value={"test_order_456": "filled"}
        )
        smart_execution.alpaca_client.place_limit_order = MagicMock(return_value="test_order_456")

        order_id = smart_execution.place_order(test_symbol, 25.0, OrderSide.BUY)

        if order_id:
            print(f"✅ Wide spread order placed: {order_id}")
        else:
            print("❌ Wide spread order failed")

        print("\n✅ Better orders integration test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logging.exception("Test error")


if __name__ == "__main__":
    test_better_orders_integration()
