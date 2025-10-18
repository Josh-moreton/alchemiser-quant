"""Business Unit: shared | Status: current.

Tests for ConnectionCircuitBreaker - WebSocket connection circuit breaker.

Tests verify state machine transitions, rate limiting, timeouts, and reset behavior.
"""

import time

from the_alchemiser.shared.utils.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitState,
    ConnectionCircuitBreaker,
)


class TestConnectionCircuitBreakerBasics:
    """Test basic initialization and configuration."""

    def test_create_with_default_config(self) -> None:
        """Test creating circuit breaker with default configuration."""
        cb = ConnectionCircuitBreaker()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time is None
        assert cb.last_attempt_time == 0
        assert cb.config.failure_threshold == 5
        assert cb.config.timeout_seconds == 60.0
        assert cb.config.success_threshold == 3

    def test_create_with_custom_config(self) -> None:
        """Test creating circuit breaker with custom configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=30.0,
            success_threshold=2,
        )
        cb = ConnectionCircuitBreaker(config=config)

        assert cb.config.failure_threshold == 3
        assert cb.config.timeout_seconds == 30.0
        assert cb.config.success_threshold == 2


class TestConnectionCircuitBreakerStateTransitions:
    """Test state machine transitions."""

    def test_initial_state_allows_connections(self) -> None:
        """Test that initial CLOSED state allows connections."""
        cb = ConnectionCircuitBreaker()
        assert cb.can_attempt_connection() is True

    def test_closed_to_open_after_failures(self) -> None:
        """Test CLOSED → OPEN transition after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = ConnectionCircuitBreaker(config=config)

        # Record failures
        for i in range(3):
            cb.record_failure(f"failure {i + 1}")
            time.sleep(0.01)  # Ensure time advances

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_open_state_blocks_connections(self) -> None:
        """Test that OPEN state blocks connection attempts."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=60.0)
        cb = ConnectionCircuitBreaker(config=config)

        # Open the circuit
        cb.record_failure("failure 1")
        time.sleep(0.01)
        cb.record_failure("failure 2")

        assert cb.state == CircuitState.OPEN
        time.sleep(0.01)
        assert cb.can_attempt_connection() is False

    def test_open_to_half_open_after_timeout(self) -> None:
        """Test OPEN → HALF_OPEN transition after timeout expires."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1)
        cb = ConnectionCircuitBreaker(config=config)

        # Open the circuit
        cb.record_failure("failure 1")
        time.sleep(0.01)
        cb.record_failure("failure 2")

        assert cb.state == CircuitState.OPEN

        # Wait for timeout to expire + rate limit (1.0s)
        time.sleep(1.2)

        # Should transition to HALF_OPEN and allow attempt
        assert cb.can_attempt_connection() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_to_closed_after_successes(self) -> None:
        """Test HALF_OPEN → CLOSED transition after success threshold."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1, success_threshold=2)
        cb = ConnectionCircuitBreaker(config=config)

        # Open the circuit
        cb.record_failure("failure 1")
        time.sleep(0.01)
        cb.record_failure("failure 2")
        assert cb.state == CircuitState.OPEN

        # Wait for timeout + rate limit
        time.sleep(1.2)
        cb.can_attempt_connection()
        assert cb.state == CircuitState.HALF_OPEN

        # Record successes
        cb.record_success()
        time.sleep(0.01)
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self) -> None:
        """Test HALF_OPEN → OPEN transition on failure."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1)
        cb = ConnectionCircuitBreaker(config=config)

        # Open the circuit
        cb.record_failure("failure 1")
        time.sleep(0.01)
        cb.record_failure("failure 2")
        assert cb.state == CircuitState.OPEN

        # Wait for timeout + rate limit
        time.sleep(1.2)
        cb.can_attempt_connection()
        assert cb.state == CircuitState.HALF_OPEN

        # Fail in HALF_OPEN - should reopen
        cb.record_failure("half-open failure")
        assert cb.state == CircuitState.OPEN


class TestConnectionCircuitBreakerRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_blocks_rapid_attempts(self) -> None:
        """Test that rapid connection attempts are rate-limited after recording an attempt."""
        cb = ConnectionCircuitBreaker()

        # First attempt should succeed
        result1 = cb.can_attempt_connection()
        assert result1 is True

        # Record a success to update last_attempt_time
        cb.record_success()

        # Immediate second attempt should be blocked (< 1.0 seconds since last_attempt_time)
        # Need small sleep to ensure time has advanced but still < 1.0s
        time.sleep(0.01)
        result2 = cb.can_attempt_connection()
        assert result2 is False

    def test_rate_limiting_allows_after_interval(self) -> None:
        """Test that attempts are allowed after rate limit interval."""
        cb = ConnectionCircuitBreaker()

        # First attempt
        assert cb.can_attempt_connection() is True

        # Wait for rate limit interval (1.0 seconds + buffer)
        time.sleep(1.1)

        # Should be allowed now
        assert cb.can_attempt_connection() is True


class TestConnectionCircuitBreakerCounters:
    """Test counter behavior."""

    def test_success_in_closed_resets_failure_count(self) -> None:
        """Test that success in CLOSED state resets failure counter."""
        cb = ConnectionCircuitBreaker()

        # Record some failures (not enough to open)
        cb.record_failure("failure 1")
        time.sleep(0.01)
        cb.record_failure("failure 2")
        assert cb.failure_count == 2

        # Record success
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_failure_count_increments_correctly(self) -> None:
        """Test that failure count increments correctly in CLOSED state."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = ConnectionCircuitBreaker(config=config)

        for i in range(4):
            cb.record_failure(f"failure {i + 1}")
            time.sleep(0.01)
            assert cb.failure_count == i + 1
            assert cb.state == CircuitState.CLOSED

        # Fifth failure should open circuit
        cb.record_failure("failure 5")
        assert cb.failure_count == 5
        assert cb.state == CircuitState.OPEN

    def test_success_count_increments_in_half_open(self) -> None:
        """Test success counter in HALF_OPEN state."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1, success_threshold=3)
        cb = ConnectionCircuitBreaker(config=config)

        # Open circuit
        cb.record_failure("f1")
        time.sleep(0.01)
        cb.record_failure("f2")

        # Move to HALF_OPEN (wait for timeout + rate limit)
        time.sleep(1.2)
        cb.can_attempt_connection()
        assert cb.state == CircuitState.HALF_OPEN

        # Record successes
        cb.record_success()
        time.sleep(0.01)
        assert cb.success_count == 1

        cb.record_success()
        time.sleep(0.01)
        assert cb.success_count == 2

        cb.record_success()
        assert cb.success_count == 0  # Reset on transition to CLOSED
        assert cb.state == CircuitState.CLOSED


class TestConnectionCircuitBreakerStateInfo:
    """Test state information reporting."""

    def test_get_state_info_returns_complete_data(self) -> None:
        """Test that get_state_info returns all state information."""
        config = CircuitBreakerConfig(
            failure_threshold=3, timeout_seconds=45.0, success_threshold=2
        )
        cb = ConnectionCircuitBreaker(config=config)

        # Record a failure
        cb.record_failure("test failure")
        time.sleep(0.01)

        info = cb.get_state_info()

        assert info["state"] == "closed"
        assert info["failure_count"] == 1
        assert info["success_count"] == 0
        assert info["failure_threshold"] == 3
        assert info["success_threshold"] == 2
        assert info["timeout_seconds"] == 45.0
        # Type narrow for mypy
        last_failure = info["last_failure_time"]
        assert isinstance(last_failure, (int, float))
        assert last_failure > 0
        last_attempt = info["last_attempt_time"]
        assert isinstance(last_attempt, (int, float))
        assert last_attempt > 0

    def test_get_state_info_handles_no_failures(self) -> None:
        """Test get_state_info when no failures recorded."""
        cb = ConnectionCircuitBreaker()
        info = cb.get_state_info()

        assert info["state"] == "closed"
        assert info["failure_count"] == 0
        assert info["success_count"] == 0
        assert info["last_failure_time"] == 0  # None converts to 0


class TestConnectionCircuitBreakerReset:
    """Test reset functionality."""

    def test_reset_returns_to_initial_state(self) -> None:
        """Test that reset returns circuit breaker to initial state."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = ConnectionCircuitBreaker(config=config)

        # Open the circuit
        cb.record_failure("f1")
        time.sleep(0.01)
        cb.record_failure("f2")
        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()

        # Verify initial state
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time is None
        assert cb.last_attempt_time == 0

    def test_reset_allows_immediate_connections(self) -> None:
        """Test that reset allows connections immediately."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = ConnectionCircuitBreaker(config=config)

        # Open the circuit
        cb.record_failure("f1")
        time.sleep(0.01)
        cb.record_failure("f2")
        time.sleep(0.01)
        assert cb.can_attempt_connection() is False

        # Reset and verify connections allowed
        cb.reset()
        assert cb.can_attempt_connection() is True


class TestConnectionCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_exact_failure_threshold(self) -> None:
        """Test behavior at exact failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = ConnectionCircuitBreaker(config=config)

        # 2 failures - should stay closed
        cb.record_failure("f1")
        time.sleep(0.01)
        cb.record_failure("f2")
        assert cb.state == CircuitState.CLOSED

        # 3rd failure - should open
        time.sleep(0.01)
        cb.record_failure("f3")
        assert cb.state == CircuitState.OPEN

    def test_exact_success_threshold_in_half_open(self) -> None:
        """Test behavior at exact success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1, success_threshold=2)
        cb = ConnectionCircuitBreaker(config=config)

        # Open circuit
        cb.record_failure("f1")
        time.sleep(0.01)
        cb.record_failure("f2")

        # Move to HALF_OPEN (wait for timeout + rate limit)
        time.sleep(1.2)
        cb.can_attempt_connection()

        # 1 success - should stay half-open
        cb.record_success()
        time.sleep(0.01)
        assert cb.state == CircuitState.HALF_OPEN

        # 2nd success - should close
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_multiple_resets(self) -> None:
        """Test that multiple resets are idempotent."""
        cb = ConnectionCircuitBreaker()

        cb.record_failure("f1")
        time.sleep(0.01)
        cb.reset()
        cb.reset()
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_can_attempt_connection_updates_state(self) -> None:
        """Test that can_attempt_connection can trigger state transitions."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1)
        cb = ConnectionCircuitBreaker(config=config)

        # Open circuit
        cb.record_failure("f1")
        time.sleep(0.01)
        cb.record_failure("f2")
        assert cb.state == CircuitState.OPEN

        # Wait for timeout + rate limit
        time.sleep(1.2)

        # Calling can_attempt_connection should transition to HALF_OPEN
        result = cb.can_attempt_connection()
        assert result is True
        assert cb.state == CircuitState.HALF_OPEN
