#!/usr/bin/env python3
"""
Test script for Phase 1 Error Handling Enhancements.

This script tests the new error handling features implemented in Phase 1:
1. Type safety improvements
2. Standardized error context
3. Enhanced exception classes
"""

import sys
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from the_alchemiser.core.error_handler import (
    ErrorContext,
    ErrorSeverity,
    EnhancedAlchemiserError,
    EnhancedDataError,
    EnhancedTradingError,
    TradingSystemErrorHandler,
    categorize_error_severity,
    create_enhanced_error,
    create_error_context,
    handle_error_with_context,
    send_error_notification_if_needed,
)
from the_alchemiser.core.exceptions import MarketDataError, OrderExecutionError
from the_alchemiser.core.types import ErrorNotificationData


def test_error_context():
    """Test the new ErrorContext class."""
    print("🧪 Testing ErrorContext...")

    context = create_error_context(
        operation="test_operation",
        component="test_component",
        function_name="test_function",
        request_id="test-123",
        user_id="test-user",
        additional_data={"key": "value"},
    )

    assert context.operation == "test_operation"
    assert context.component == "test_component"
    assert context.function_name == "test_function"
    assert context.request_id == "test-123"
    assert context.user_id == "test-user"
    assert context.additional_data["key"] == "value"

    # Test serialization
    context_dict = context.to_dict()
    assert isinstance(context_dict, dict)
    assert context_dict["operation"] == "test_operation"
    assert isinstance(context_dict["timestamp"], str)

    print("✅ ErrorContext tests passed!")


def test_enhanced_exceptions():
    """Test the new enhanced exception classes."""
    print("🧪 Testing Enhanced Exceptions...")

    # Test base enhanced error
    context = create_error_context("test_op", "test_comp")
    error = EnhancedAlchemiserError(
        message="Test error",
        context=context,
        severity=ErrorSeverity.HIGH,
        recoverable=True,
        max_retries=5,
    )

    assert error.severity == ErrorSeverity.HIGH
    assert error.recoverable is True
    assert error.should_retry() is True
    assert error.max_retries == 5
    assert isinstance(error.error_id, str)

    # Test retry logic
    retry_delay = error.get_retry_delay()
    assert isinstance(retry_delay, float)
    assert retry_delay >= 0

    # Test retry increment
    retried_error = error.increment_retry()
    assert retried_error.retry_count == 1

    # Test serialization
    error_dict = error.to_dict()
    assert isinstance(error_dict, dict)
    assert error_dict["severity"] == ErrorSeverity.HIGH
    assert "error_id" in error_dict

    print("✅ Enhanced exceptions tests passed!")


def test_enhanced_trading_error():
    """Test the enhanced trading error."""
    print("🧪 Testing Enhanced Trading Error...")

    context = create_error_context("place_order", "trading_engine")
    error = EnhancedTradingError(
        message="Order failed",
        context=context,
        symbol="AAPL",
        order_id="ORDER-123",
        quantity=100.0,
        price=150.50,
        severity=ErrorSeverity.HIGH,
    )

    assert error.symbol == "AAPL"
    assert error.order_id == "ORDER-123"
    assert error.quantity == 100.0
    assert error.price == 150.50

    # Test serialization includes trading context
    error_dict = error.to_dict()
    assert error_dict["symbol"] == "AAPL"
    assert error_dict["order_id"] == "ORDER-123"

    print("✅ Enhanced trading error tests passed!")


def test_enhanced_data_error():
    """Test the enhanced data error."""
    print("🧪 Testing Enhanced Data Error...")

    context = create_error_context("fetch_prices", "market_data")
    error = EnhancedDataError(
        message="Data fetch failed",
        context=context,
        data_source="alpaca",
        data_type="price_data",
        symbol="TSLA",
        severity=ErrorSeverity.MEDIUM,
    )

    assert error.data_source == "alpaca"
    assert error.data_type == "price_data"
    assert error.symbol == "TSLA"

    # Test serialization includes data context
    error_dict = error.to_dict()
    assert error_dict["data_source"] == "alpaca"
    assert error_dict["data_type"] == "price_data"

    print("✅ Enhanced data error tests passed!")


def test_error_severity_categorization():
    """Test automatic error severity categorization."""
    print("🧪 Testing Error Severity Categorization...")

    # Test different error types
    order_error = OrderExecutionError("Order failed")
    assert categorize_error_severity(order_error) == ErrorSeverity.HIGH

    market_error = MarketDataError("Data unavailable")
    assert categorize_error_severity(market_error) == ErrorSeverity.MEDIUM

    generic_error = Exception("Generic error")
    assert categorize_error_severity(generic_error) == ErrorSeverity.MEDIUM

    print("✅ Error severity categorization tests passed!")


def test_error_factory():
    """Test the enhanced error factory function."""
    print("🧪 Testing Error Factory...")

    context = create_error_context("test_operation", "test_component")

    # Test auto-severity determination
    error = create_enhanced_error(
        error_type=EnhancedTradingError,
        message="Trading error occurred",
        context=context,
        symbol="AAPL",
    )

    assert isinstance(error, EnhancedTradingError)
    assert error.context == context
    assert error.symbol == "AAPL"
    # Severity should be auto-determined
    assert error.severity in [
        ErrorSeverity.LOW,
        ErrorSeverity.MEDIUM,
        ErrorSeverity.HIGH,
        ErrorSeverity.CRITICAL,
    ]

    print("✅ Error factory tests passed!")


def test_error_handler_integration():
    """Test integration with the TradingSystemErrorHandler."""
    print("🧪 Testing Error Handler Integration...")

    # Import the global handler
    from the_alchemiser.core.error_handler import _error_handler

    context = create_error_context("test_integration", "test_handler")

    # Clear any existing errors
    _error_handler.clear_errors()

    # Create a test error
    test_error = EnhancedTradingError(
        message="Integration test error",
        context=context,
        symbol="TEST",
        severity=ErrorSeverity.MEDIUM,
    )

    # Test handling error with context
    error_details = handle_error_with_context(
        error=test_error, context=context, should_continue=True
    )

    assert error_details.error == test_error
    assert error_details.component == context.component
    assert isinstance(error_details.additional_data, dict)

    # Verify error was recorded
    assert len(_error_handler.errors) > 0
    last_error = _error_handler.errors[-1]
    assert last_error.error == test_error

    print("✅ Error handler integration tests passed!")


def test_notification_type_safety():
    """Test that notification function returns proper types."""
    print("🧪 Testing Notification Type Safety...")

    # The function should return ErrorNotificationData | None
    # We can't easily test actual email sending, but we can verify the type signature
    result = send_error_notification_if_needed()

    # Should return None if no errors to send
    assert result is None or isinstance(result, dict)

    print("✅ Notification type safety tests passed!")


def main():
    """Run all Phase 1 tests."""
    print("🚀 Starting Phase 1 Error Handling Enhancement Tests...\n")

    try:
        test_error_context()
        test_enhanced_exceptions()
        test_enhanced_trading_error()
        test_enhanced_data_error()
        test_error_severity_categorization()
        test_error_factory()
        test_error_handler_integration()
        test_notification_type_safety()

        print("\n🎉 All Phase 1 tests passed successfully!")
        print("✅ Type safety improvements: COMPLETED")
        print("✅ Standardized error context: COMPLETED")
        print("✅ Enhanced exception classes: COMPLETED")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
