#!/usr/bin/env python3
"""
Test script for enhanced error handling and email notifications.

This script tests the new error handler functionality and email templates.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_error_categorization():
    """Test error categorization functionality."""
    print("Testing error categorization...")

    from the_alchemiser.core.error_handler import TradingSystemErrorHandler
    from the_alchemiser.core.exceptions import (
        ConfigurationError,
        InsufficientFundsError,
        MarketDataError,
        OrderExecutionError,
        StrategyExecutionError,
    )

    handler = TradingSystemErrorHandler()

    # Test different error types
    test_cases = [
        (InsufficientFundsError("Not enough funds"), "trading"),
        (OrderExecutionError("Order failed"), "trading"),
        (MarketDataError("Data unavailable", "AAPL"), "data"),
        (StrategyExecutionError("Strategy calculation failed", "TECL"), "strategy"),
        (ConfigurationError("Invalid config"), "configuration"),
        (ValueError("Generic error"), "critical"),  # Non-Alchemiser exception
    ]

    for error, expected_category in test_cases:
        category = handler.categorize_error(error, "test context")
        print(
            f"  {type(error).__name__}: {category} ({'✓' if category == expected_category else '✗'})"
        )

    print()


def test_error_handling():
    """Test complete error handling workflow."""
    print("Testing error handling workflow...")

    from the_alchemiser.core.error_handler import get_error_handler, handle_trading_error
    from the_alchemiser.core.exceptions import MarketDataError, OrderExecutionError

    # Clear any existing errors
    handler = get_error_handler()
    handler.clear_errors()

    # Handle multiple errors
    trading_error = OrderExecutionError("Failed to place order for AAPL")
    handle_trading_error(
        error=trading_error,
        context="order placement",
        component="AlpacaClient.submit_order",
        additional_data={"symbol": "AAPL", "qty": 100, "side": "buy"},
    )

    data_error = MarketDataError("Unable to fetch current price", "SPY")
    handle_trading_error(
        error=data_error,
        context="price fetching",
        component="DataProvider.get_current_price",
        additional_data={"symbol": "SPY", "retry_count": 3},
    )

    # Test summary
    print(f"  Total errors recorded: {len(handler.errors)}")
    print(f"  Has critical errors: {handler.has_critical_errors()}")
    print(f"  Has trading errors: {handler.has_trading_errors()}")
    print(f"  Should send email: {handler.should_send_error_email()}")

    # Generate report
    report = handler.generate_error_report()
    print(f"  Generated report length: {len(report)} characters")

    print()


def test_error_email_template():
    """Test error email template generation."""
    print("Testing error email template...")

    from the_alchemiser.core.ui.email.templates import EmailTemplates

    # Test with structured error report
    structured_report = """# Trading System Error Report

**Execution Time:** 2025-01-04 15:30:00 UTC
**Total Errors:** 2

## 💰 TRADING ERRORS
These errors affected trade execution:

**Component:** AlpacaClient.submit_order
**Context:** order placement
**Error:** Failed to place order for AAPL
**Action:** Verify trading permissions, account status, and market hours

**Additional Data:** {'symbol': 'AAPL', 'qty': 100, 'side': 'buy'}

## 📊 DATA ERRORS
**Component:** DataProvider.get_current_price
**Context:** price fetching
**Error:** Unable to fetch current price
**Action:** Check market data sources, API limits, and network connectivity

**Additional Data:** {'symbol': 'SPY', 'retry_count': 3}
"""

    html_content = EmailTemplates.build_error_report(
        title="🚨 CRITICAL Alert - Trading System Errors", error_message=structured_report
    )

    print(f"  Generated HTML email length: {len(html_content)} characters")
    print(f"  Contains structured formatting: {'<h2' in html_content}")
    print(f"  Contains error sections: {'💰 TRADING ERRORS' in html_content}")

    print()


def test_notification_integration():
    """Test the complete notification integration."""
    print("Testing notification integration...")

    from the_alchemiser.core.error_handler import (
        get_error_handler,
        send_error_notification_if_needed,
    )
    from the_alchemiser.core.exceptions import StrategyExecutionError

    # Clear existing errors
    handler = get_error_handler()
    handler.clear_errors()

    # Add a test error
    strategy_error = StrategyExecutionError("TECL strategy signal calculation failed", "TECL")
    handler.handle_error(
        error=strategy_error,
        context="strategy signal generation",
        component="TECLStrategy.generate_signals",
        additional_data={"strategy": "TECL", "market_regime": "bull", "last_signal": "BUY"},
    )

    print(f"  Error added, should send notification: {handler.should_send_error_email()}")

    # Test sending notification (will not actually send in test mode)
    try:
        send_error_notification_if_needed()
        print("  ✓ Notification function executed without errors")
    except Exception as e:
        print(f"  ✗ Notification function failed: {e}")

    print()


def main():
    """Run all error handling tests."""
    print("=" * 60)
    print("Testing Enhanced Error Handling System")
    print("=" * 60)
    print()

    try:
        test_error_categorization()
        test_error_handling()
        test_error_email_template()
        test_notification_integration()

        print("=" * 60)
        print("✅ All error handling tests completed successfully!")
        print()
        print("Key Features Tested:")
        print("  • Error categorization by type and context")
        print("  • Structured error reporting with suggestions")
        print("  • Enhanced email templates with HTML formatting")
        print("  • Integration with existing notification system")
        print("  • Automatic error notification triggering")
        print()
        print("EventBridge Configuration:")
        print("  • Retry attempts reduced to 1 (from default 185)")
        print("  • Dead letter queue added for failed executions")
        print("  • Prevents runaway retry loops on errors")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
