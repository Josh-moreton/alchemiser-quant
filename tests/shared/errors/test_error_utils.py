"""Business Unit: shared | Status: current.

Tests for error utility functions including retry and circuit breaker patterns.
"""

import time
from unittest.mock import patch

import pytest

from the_alchemiser.shared.errors.error_types import ErrorSeverity
from the_alchemiser.shared.errors.error_utils import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    categorize_error_severity,
    retry_with_backoff,
)
from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    InsufficientFundsError,
    MarketDataError,
)


class TestRetryWithBackoff:
    """Test retry_with_backoff decorator."""

    def test_retry_succeeds_first_attempt(self):
        """Test that successful function doesn't retry."""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Test that function retries and succeeds."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = eventually_succeeds()
        assert result == "success"
        assert call_count == 3

    def test_retry_fails_after_max_retries(self):
        """Test that function fails after max retries."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()

        assert call_count == 4  # Initial + 3 retries

    def test_retry_specific_exception(self):
        """Test that retry only catches specific exceptions."""

        @retry_with_backoff(exceptions=(ValueError,), max_retries=3, base_delay=0.01)
        def raises_runtime_error():
            raise RuntimeError("Not caught")

        # Should raise immediately, not retry
        with pytest.raises(RuntimeError, match="Not caught"):
            raises_runtime_error()

    def test_retry_multiple_exception_types(self):
        """Test retry with multiple exception types."""
        call_count = 0

        @retry_with_backoff(
            exceptions=(ValueError, RuntimeError),
            max_retries=3,
            base_delay=0.01,
        )
        def raises_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First error")
            if call_count == 2:
                raise RuntimeError("Second error")
            return "success"

        result = raises_different_errors()
        assert result == "success"
        assert call_count == 3

    def test_retry_exponential_backoff(self):
        """Test that retry delays follow exponential backoff."""
        delays = []

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.1,
            backoff_factor=2.0,
            jitter=False,
        )
        def track_delays():
            start = time.time()
            delays.append(start)
            raise ValueError("Retry")

        with pytest.raises(ValueError):
            track_delays()

        # Should have 4 attempts (initial + 3 retries)
        assert len(delays) == 4

        # Check delays are increasing (allowing some tolerance for timing)
        if len(delays) >= 3:
            delay1 = delays[1] - delays[0]
            delay2 = delays[2] - delays[1]
            # Second delay should be roughly double the first
            # Allow significant tolerance due to system timing
            assert delay2 > delay1 * 0.5

    def test_retry_max_delay_cap(self):
        """Test that retry delay is capped at max_delay."""
        call_count = 0

        @retry_with_backoff(
            max_retries=10,
            base_delay=1.0,
            max_delay=2.0,
            backoff_factor=10.0,
            jitter=False,
        )
        def many_retries():
            nonlocal call_count
            call_count += 1
            raise ValueError("Retry")

        start = time.time()
        with pytest.raises(ValueError):
            many_retries()
        elapsed = time.time() - start

        # Even with high backoff, should be capped by max_delay
        # With 10 retries at max 2s each, should be < 25s
        assert elapsed < 25

    def test_retry_with_jitter(self):
        """Test that jitter adds randomness to delays."""
        delays = []

        @retry_with_backoff(
            max_retries=5,
            base_delay=0.1,
            backoff_factor=2.0,
            jitter=True,
        )
        def track_delays_with_jitter():
            start = time.time()
            delays.append(start)
            raise ValueError("Retry")

        with pytest.raises(ValueError):
            track_delays_with_jitter()

        # Delays should not be exact multiples due to jitter
        # This is a weak test since randomness is involved
        assert len(delays) == 6  # Initial + 5 retries


class TestRetryWithBackoffLogging:
    """Test logging behavior of retry decorator."""

    @patch("the_alchemiser.shared.errors.error_utils.logger")
    def test_retry_logs_attempts(self, mock_logger):
        """Test that retry attempts are logged."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        fails_twice()

        # Should log warnings for each retry
        assert mock_logger.warning.call_count == 2

    @patch("the_alchemiser.shared.errors.error_utils.logger")
    def test_retry_logs_final_failure(self, mock_logger):
        """Test that final failure is logged."""

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            always_fails()

        # Should log error on final failure
        mock_logger.error.assert_called_once()


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_create_circuit_breaker(self):
        """Test creating circuit breaker."""
        cb = CircuitBreaker(failure_threshold=3, timeout=30.0)
        assert cb.failure_threshold == 3
        assert cb.timeout == 30.0
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in CLOSED state allows calls."""
        cb = CircuitBreaker(failure_threshold=3)

        @cb
        def working_func():
            return "success"

        result = working_func()
        assert result == "success"
        assert cb.state == "CLOSED"

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1.0)
        call_count = 0

        @cb
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Failed")

        # Fail 3 times to reach threshold
        for i in range(3):
            with pytest.raises(Exception):
                failing_func()

        assert cb.state == "OPEN"
        assert cb.failure_count == 3

    def test_circuit_breaker_open_state_blocks_calls(self):
        """Test that OPEN circuit breaker blocks calls."""
        cb = CircuitBreaker(failure_threshold=2, timeout=1.0)

        @cb
        def failing_func():
            raise Exception("Failed")

        # Fail twice to open circuit
        for i in range(2):
            with pytest.raises(Exception):
                failing_func()

        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            failing_func()

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker moves to HALF_OPEN after timeout."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
        call_count = 0

        @cb
        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Failed")
            return "success"

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                sometimes_fails()

        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(0.15)

        # Should move to HALF_OPEN and succeed
        result = sometimes_fails()
        assert result == "success"
        assert cb.state == "CLOSED"

    def test_circuit_breaker_reopens_on_half_open_failure(self):
        """Test circuit breaker reopens if HALF_OPEN attempt fails."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

        @cb
        def failing_func():
            raise Exception("Failed")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                failing_func()

        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(0.15)

        # Should move to HALF_OPEN, then back to OPEN on failure
        with pytest.raises(Exception):
            failing_func()

        assert cb.state == "OPEN"

    def test_circuit_breaker_with_specific_exception(self):
        """Test circuit breaker with specific exception type."""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)

        @cb
        def raises_value_error():
            raise ValueError("Value error")

        # Should count ValueError
        for i in range(2):
            with pytest.raises(ValueError):
                raises_value_error()

        assert cb.state == "OPEN"

    def test_circuit_breaker_ignores_other_exceptions(self):
        """Test circuit breaker doesn't count unexpected exceptions."""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)
        call_count = 0

        @cb
        def raises_runtime_error():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Runtime error")

        # RuntimeError shouldn't be caught by circuit breaker
        for i in range(3):
            with pytest.raises(RuntimeError):
                raises_runtime_error()

        # Circuit should still be closed (RuntimeError not tracked)
        assert cb.state == "CLOSED"
        assert call_count == 3


class TestCategorizeErrorSeverity:
    """Test categorize_error_severity function."""

    def test_categorize_configuration_error_as_high(self):
        """Test ConfigurationError is categorized as HIGH."""
        error = ConfigurationError("Bad config")
        severity = categorize_error_severity(error)
        assert severity == ErrorSeverity.HIGH

    def test_categorize_insufficient_funds_as_high(self):
        """Test InsufficientFundsError is categorized as HIGH."""
        error = InsufficientFundsError("No funds")
        severity = categorize_error_severity(error)
        assert severity == ErrorSeverity.HIGH

    def test_categorize_data_provider_error_as_medium(self):
        """Test DataProviderError is categorized as MEDIUM."""
        error = DataProviderError("Provider down")
        severity = categorize_error_severity(error)
        assert severity == ErrorSeverity.MEDIUM

    def test_categorize_market_data_error_as_medium(self):
        """Test MarketDataError is categorized as MEDIUM."""
        error = MarketDataError("Data unavailable")
        severity = categorize_error_severity(error)
        assert severity == ErrorSeverity.MEDIUM

    def test_categorize_unknown_error_as_medium(self):
        """Test unknown errors are categorized as MEDIUM."""
        error = ValueError("Unknown error")
        severity = categorize_error_severity(error)
        assert severity == ErrorSeverity.MEDIUM


class TestErrorUtilsIntegration:
    """Test integration scenarios for error utilities."""

    def test_retry_with_circuit_breaker(self):
        """Test combining retry decorator with circuit breaker."""
        # Circuit breaker will open after 3 failures
        # Retry will make 3 attempts (initial + 2 retries)
        # So we need function to succeed on 3rd call
        cb = CircuitBreaker(failure_threshold=5, timeout=0.1)
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        @cb
        def protected_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        # Should eventually succeed after retries
        result = protected_func()
        assert result == "success"

    def test_circuit_breaker_prevents_excessive_retries(self):
        """Test that circuit breaker stops excessive retry attempts."""
        cb = CircuitBreaker(failure_threshold=2, timeout=1.0)
        total_calls = 0

        @cb
        def always_fails():
            nonlocal total_calls
            total_calls += 1
            raise ValueError("Always fails")

        # Fail twice to open circuit
        for i in range(2):
            with pytest.raises(ValueError):
                always_fails()

        # Circuit is now open
        assert cb.state == "OPEN"

        # Further calls should be blocked immediately
        with pytest.raises(CircuitBreakerOpenError):
            always_fails()

        # Total calls should be 2 (not more)
        assert total_calls == 2
