#!/usr/bin/env python3
"""
Test Order Validation Module

Simple test to verify the new order validation system works correctly.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_order_validation():
    """Test the new order validation system."""

    print("🧪 Testing Order Validation System...")

    try:
        from the_alchemiser.execution.order_validation import OrderValidator, convert_legacy_orders

        print("✅ Successfully imported order validation modules")
    except Exception as e:
        print(f"❌ Failed to import modules: {e}")
        return False

    # Test 1: Create a valid order
    try:
        validator = OrderValidator()

        valid_order = validator.create_validated_order(
            symbol="AAPL", quantity=100, side="BUY", order_type="MARKET"
        )

        print(
            f"✅ Created valid order: {valid_order.symbol} {valid_order.quantity} {valid_order.side}"
        )

    except Exception as e:
        print(f"❌ Failed to create valid order: {e}")
        return False

    # Test 2: Test legacy order conversion
    try:
        legacy_orders = [
            {
                "symbol": "TSLA",
                "qty": 50,
                "side": "BUY",
                "order_type": "market",
                "id": "test_order_1",
            },
            {
                "symbol": "MSFT",
                "quantity": 25,  # Different quantity field name
                "side": "sell",
                "order_type": "limit",
                "limit_price": 300.50,
                "id": "test_order_2",
            },
            {
                # Invalid order - missing symbol
                "qty": 10,
                "side": "BUY",
            },
        ]

        validated_orders = convert_legacy_orders(legacy_orders)

        print(f"✅ Converted {len(validated_orders)} out of {len(legacy_orders)} legacy orders")

        for order in validated_orders:
            print(
                f"   📋 {order.symbol}: {order.quantity} shares {order.side} @ {order.order_type}"
            )

    except Exception as e:
        print(f"❌ Failed legacy order conversion: {e}")
        return False

    # Test 3: Test validation errors
    try:
        invalid_order_data = {
            "symbol": "",  # Empty symbol should fail
            "qty": -10,  # Negative quantity should fail
            "side": "INVALID_SIDE",
        }

        result = validator.validate_order_structure(invalid_order_data)

        if not result.is_valid:
            print(f"✅ Correctly caught validation errors: {len(result.errors)} errors")
            for error in result.errors:
                print(f"   ⚠️  {error}")
        else:
            print("❌ Should have caught validation errors but didn't")
            return False

    except Exception as e:
        print(f"❌ Error testing validation: {e}")
        return False

    print("🎉 All order validation tests passed!")
    return True


if __name__ == "__main__":
    success = test_order_validation()
    sys.exit(0 if success else 1)
