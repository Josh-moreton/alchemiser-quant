#!/usr/bin/env python3
"""
Test script for Phase 2 Error Recovery and Resilience.

This script tests the new error recovery features implemented in Phase 2:
1. Automatic Error Recovery strategies
2. Circuit Breaker patterns
3. Smart Retry mechanisms
"""

import sys
import time
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from the_alchemiser.core.error_handler import (
    EnhancedDataError,
    EnhancedTradingError,
    ErrorSeverity,
    create_error_context,
)
from the_alchemiser.core.error_recovery import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    DataErrorRecovery,
    ErrorRecoveryManager,
    ExponentialBackoffStrategy,
    FibonacciBackoffStrategy,
    FixedIntervalStrategy,
    LinearBackoffStrategy,
    RecoveryResult,
    SmartRetryManager,
    TradingErrorRecovery,
    get_recovery_manager,
    with_circuit_breaker,
    with_resilience,
    with_retry,
)
from the_alchemiser.core.exceptions import (
    RateLimitError,
)


def test_recovery_strategies():
    """Test automatic error recovery strategies."""
    print("🧪 Testing Recovery Strategies...")

    # Test trading error recovery
    trading_recovery = TradingErrorRecovery()

    # Test rate limit recovery
    context = create_error_context("api_call", "trading_client")
    rate_limit_error = RateLimitError("Rate limit exceeded", retry_after=30)
    enhanced_rate_limit = EnhancedTradingError(
        message="Rate limit error",
        context=context,
        severity=ErrorSeverity.MEDIUM,
    )

    assert trading_recovery.can_recover(enhanced_rate_limit)
    # Note: We can't directly test with RateLimitError as it's not an EnhancedAlchemiserError
    # In practice, the system would wrap it as an EnhancedTradingError

    # Test order execution recovery
    order_error = EnhancedTradingError(
        message="Order temporarily unavailable",
        context=context,
        symbol="AAPL",
        severity=ErrorSeverity.HIGH,
    )

    recovery_result = trading_recovery.recover(order_error)
    assert isinstance(recovery_result, RecoveryResult)
    assert recovery_result.retry_recommended

    # Test data error recovery
    data_recovery = DataErrorRecovery()
    data_context = create_error_context("fetch_data", "market_data")
    market_error = EnhancedDataError(
        message="Connection failed",
        context=data_context,
        data_source="alpaca",
        severity=ErrorSeverity.MEDIUM,
    )

    assert data_recovery.can_recover(market_error)
    data_recovery_result = data_recovery.recover(market_error)
    assert isinstance(data_recovery_result, RecoveryResult)

    print("✅ Recovery strategies tests passed!")


def test_circuit_breaker():
    """Test circuit breaker functionality."""
    print("🧪 Testing Circuit Breaker...")

    circuit_breaker = CircuitBreaker(
        name="test_circuit",
        failure_threshold=3,
        recovery_timeout=1.0,  # Short timeout for testing
    )

    # Test normal operation (CLOSED state)
    assert circuit_breaker.get_state() == CircuitState.CLOSED

    def successful_operation():
        return "success"

    result = circuit_breaker.call(successful_operation)
    assert result == "success"
    assert circuit_breaker.get_state() == CircuitState.CLOSED

    # Test failure accumulation
    def failing_operation():
        raise ValueError("Test failure")

    failure_count = 0
    for i in range(3):
        try:
            circuit_breaker.call(failing_operation)
        except ValueError:
            failure_count += 1

    # Circuit should now be OPEN
    assert circuit_breaker.get_state() == CircuitState.OPEN

    # Test that OPEN circuit blocks calls
    try:
        circuit_breaker.call(successful_operation)
        assert False, "Should have raised CircuitBreakerOpenError"
    except CircuitBreakerOpenError:
        pass  # Expected

    # Wait for recovery timeout and test HALF_OPEN state
    time.sleep(1.1)  # Wait for recovery timeout

    # First call after timeout should move to HALF_OPEN and succeed
    result = circuit_breaker.call(successful_operation)
    assert result == "success"
    assert circuit_breaker.get_state() == CircuitState.CLOSED  # Should close after success

    print("✅ Circuit breaker tests passed!")


def test_retry_strategies():
    """Test different retry strategies."""
    print("🧪 Testing Retry Strategies...")

    # Test exponential backoff
    exp_strategy = ExponentialBackoffStrategy(base_delay=1.0, max_delay=10.0, factor=2.0)
    assert exp_strategy.get_delay(0) == 1.0
    assert exp_strategy.get_delay(1) == 2.0
    assert exp_strategy.get_delay(2) == 4.0
    assert exp_strategy.get_delay(10) == 10.0  # Should cap at max_delay

    # Test linear backoff
    linear_strategy = LinearBackoffStrategy(base_delay=2.0, max_delay=10.0)
    assert linear_strategy.get_delay(0) == 2.0
    assert linear_strategy.get_delay(1) == 4.0
    assert linear_strategy.get_delay(2) == 6.0
    assert linear_strategy.get_delay(10) == 10.0  # Should cap at max_delay

    # Test fixed interval
    fixed_strategy = FixedIntervalStrategy(delay=5.0)
    assert fixed_strategy.get_delay(0) == 5.0
    assert fixed_strategy.get_delay(5) == 5.0
    assert fixed_strategy.get_delay(100) == 5.0

    # Test Fibonacci backoff
    fib_strategy = FibonacciBackoffStrategy(base_delay=1.0, max_delay=20.0)
    assert fib_strategy.get_delay(0) == 1.0  # fib(1) = 1
    assert fib_strategy.get_delay(1) == 1.0  # fib(2) = 1
    assert fib_strategy.get_delay(2) == 2.0  # fib(3) = 2
    assert fib_strategy.get_delay(3) == 3.0  # fib(4) = 3
    assert fib_strategy.get_delay(4) == 5.0  # fib(5) = 5

    print("✅ Retry strategies tests passed!")


def test_smart_retry_manager():
    """Test smart retry manager."""
    print("🧪 Testing Smart Retry Manager...")

    retry_manager = SmartRetryManager()

    # Test successful retry
    attempt_count = 0

    def sometimes_failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("Temporary failure")
        return "success"

    # Reset counter
    attempt_count = 0
    result = retry_manager.retry_with_strategy(
        func=sometimes_failing_function,
        strategy="fixed",
        max_retries=3,
        exceptions=(ValueError,),
        jitter=False,  # Disable for predictable testing
    )

    assert result == "success"
    assert attempt_count == 3  # Should have tried 3 times

    # Test exhausted retries
    attempt_count = 0

    def always_failing_function():
        nonlocal attempt_count
        attempt_count += 1
        raise ValueError("Always fails")

    try:
        retry_manager.retry_with_strategy(
            func=always_failing_function,
            strategy="fixed",
            max_retries=2,
            exceptions=(ValueError,),
            jitter=False,
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        assert attempt_count == 3  # Initial attempt + 2 retries

    print("✅ Smart retry manager tests passed!")


def test_recovery_manager():
    """Test the central error recovery manager."""
    print("🧪 Testing Recovery Manager...")

    recovery_manager = ErrorRecoveryManager()

    # Test recovery from trading error
    context = create_error_context("place_order", "trading_engine")
    trading_error = EnhancedTradingError(
        message="Order execution failed temporarily",
        context=context,
        symbol="TSLA",
        severity=ErrorSeverity.HIGH,
    )

    recovery_result = recovery_manager.recover_from_error(trading_error)
    assert isinstance(recovery_result, RecoveryResult)

    # Test getting circuit breaker
    circuit_breaker = recovery_manager.get_circuit_breaker("test_service")
    assert isinstance(circuit_breaker, CircuitBreaker)
    assert circuit_breaker.name == "test_service"

    # Test getting same circuit breaker (should be cached)
    same_circuit_breaker = recovery_manager.get_circuit_breaker("test_service")
    assert circuit_breaker is same_circuit_breaker

    # Test execute with resilience
    call_count = 0

    def test_resilient_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("First call fails")
        return "resilient_success"

    result = recovery_manager.execute_with_resilience(
        func=test_resilient_function,
        circuit_breaker_name="resilient_test",
        retry_strategy="exponential",
        max_retries=3,
        exceptions=(ValueError,),
    )

    assert result == "resilient_success"

    # Test recovery statistics
    stats = recovery_manager.get_recovery_statistics()
    assert isinstance(stats, dict)

    print("✅ Recovery manager tests passed!")


def test_decorators():
    """Test resilience decorators."""
    print("🧪 Testing Resilience Decorators...")

    # Test with_retry decorator
    call_count = 0

    @with_retry(strategy="fixed", max_retries=2, exceptions=(ValueError,))
    def retry_decorated_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Retry test")
        return "retry_success"

    call_count = 0
    result = retry_decorated_function()
    assert result == "retry_success"
    assert call_count == 3

    # Test with_circuit_breaker decorator
    @with_circuit_breaker("decorator_test", failure_threshold=2)
    def circuit_decorated_function(should_fail=False):
        if should_fail:
            raise RuntimeError("Circuit test failure")
        return "circuit_success"

    # Should work normally
    result = circuit_decorated_function(should_fail=False)
    assert result == "circuit_success"

    # Test with_resilience decorator
    resilience_call_count = 0

    @with_resilience(
        circuit_breaker_name="resilience_test",
        retry_strategy="exponential",
        max_retries=2,
        exceptions=(ValueError,),
    )
    def resilience_decorated_function():
        nonlocal resilience_call_count
        resilience_call_count += 1
        if resilience_call_count < 2:
            raise ValueError("Resilience test")
        return "resilience_success"

    resilience_call_count = 0
    result = resilience_decorated_function()
    assert result == "resilience_success"

    print("✅ Decorator tests passed!")


def test_integration():
    """Test integration between all recovery components."""
    print("🧪 Testing Recovery Integration...")

    # Get global recovery manager
    recovery_manager = get_recovery_manager()

    # Test complex scenario with multiple failures and recovery
    integration_call_count = 0

    def complex_operation():
        nonlocal integration_call_count
        integration_call_count += 1

        if integration_call_count == 1:
            # First call: trading error that should be recoverable
            context = create_error_context("complex_trade", "integration_test")
            raise EnhancedTradingError(
                message="Temporary trading issue",
                context=context,
                symbol="INTEG",
                severity=ErrorSeverity.MEDIUM,
            )
        elif integration_call_count == 2:
            # Second call: data error that should be recoverable
            context = create_error_context("fetch_data", "integration_test")
            raise EnhancedDataError(
                message="Connection timeout",
                context=context,
                data_source="test_source",
                severity=ErrorSeverity.MEDIUM,
            )
        else:
            # Third call: success
            return "integration_success"

    integration_call_count = 0
    result = recovery_manager.execute_with_resilience(
        func=complex_operation,
        circuit_breaker_name="integration_circuit",
        retry_strategy="exponential",
        max_retries=3,
        exceptions=(EnhancedTradingError, EnhancedDataError),
    )

    assert result == "integration_success"
    assert integration_call_count == 3

    # Also test direct recovery to ensure statistics are tracked
    test_error = EnhancedTradingError(
        message="Test for stats",
        context=create_error_context("test_op", "test_comp"),
        symbol="STAT",
        severity=ErrorSeverity.MEDIUM,
    )
    recovery_result = recovery_manager.recover_from_error(test_error)
    assert recovery_result.success

    # Verify recovery statistics were updated
    stats = recovery_manager.get_recovery_statistics()
    assert len(stats) > 0

    print("✅ Integration tests passed!")


def main():
    """Run all Phase 2 tests."""
    print("🚀 Starting Phase 2 Error Recovery and Resilience Tests...\n")

    try:
        test_recovery_strategies()
        test_circuit_breaker()
        test_retry_strategies()
        test_smart_retry_manager()
        test_recovery_manager()
        test_decorators()
        test_integration()

        print("\n🎉 All Phase 2 tests passed successfully!")
        print("✅ Automatic Error Recovery: COMPLETED")
        print("✅ Circuit Breaker Patterns: COMPLETED")
        print("✅ Smart Retry Mechanisms: COMPLETED")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
