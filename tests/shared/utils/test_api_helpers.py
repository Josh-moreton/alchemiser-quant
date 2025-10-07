"""Business Unit: shared | Status: current.

Test suite for API Helper Utilities.

Tests rate limiting and timeout decorators.
"""

import time
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.errors.exceptions import RateLimitError, TradingClientError
from the_alchemiser.shared.utils.api_helpers import (
    RateLimiter,
    with_rate_limiting,
    with_timeout,
)


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_init_defaults(self):
        """Test initialization with default parameters."""
        limiter = RateLimiter()
        assert limiter.calls_per_minute == 200
        assert limiter.calls_per_hour == 10000
        assert limiter.backoff_base == 2.0
        assert limiter.max_backoff == 60.0

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        limiter = RateLimiter(
            calls_per_minute=10,
            calls_per_hour=100,
            backoff_base=1.5,
            max_backoff=30.0,
        )
        assert limiter.calls_per_minute == 10
        assert limiter.calls_per_hour == 100
        assert limiter.backoff_base == 1.5
        assert limiter.max_backoff == 30.0

    def test_check_rate_limit_empty(self):
        """Test rate limit check when no calls made."""
        limiter = RateLimiter(calls_per_minute=10)
        can_call, wait_time = limiter.check_rate_limit()
        assert can_call is True
        assert wait_time == 0.0

    def test_check_rate_limit_under_limit(self):
        """Test rate limit check when under limit."""
        limiter = RateLimiter(calls_per_minute=10)
        
        # Make 5 calls
        for _ in range(5):
            limiter.record_call()
        
        can_call, wait_time = limiter.check_rate_limit()
        assert can_call is True
        assert wait_time == 0.0

    def test_check_rate_limit_at_minute_limit(self):
        """Test rate limit check when at minute limit."""
        limiter = RateLimiter(calls_per_minute=5)
        
        # Make 5 calls
        for _ in range(5):
            limiter.record_call()
        
        can_call, wait_time = limiter.check_rate_limit()
        assert can_call is False
        assert wait_time > 0

    def test_cleanup_old_calls(self):
        """Test cleanup of old call timestamps."""
        limiter = RateLimiter(calls_per_minute=10)
        
        # Add old calls (manually set timestamp)
        limiter._minute_calls = [time.time() - 120]  # 2 minutes ago
        limiter._hour_calls = [time.time() - 4000]   # Over 1 hour ago
        
        limiter._cleanup_old_calls()
        
        assert len(limiter._minute_calls) == 0
        assert len(limiter._hour_calls) == 0

    def test_record_error_increments_counter(self):
        """Test error recording increments counter."""
        limiter = RateLimiter()
        
        assert limiter._consecutive_errors == 0
        
        backoff = limiter.record_error()
        assert limiter._consecutive_errors == 1
        assert backoff > 0

    def test_record_error_exponential_backoff(self):
        """Test exponential backoff calculation."""
        limiter = RateLimiter(backoff_base=2.0, max_backoff=100.0)
        
        backoff1 = limiter.record_error()  # 2^1 = 2
        backoff2 = limiter.record_error()  # 2^2 = 4
        backoff3 = limiter.record_error()  # 2^3 = 8
        
        assert backoff1 == 2.0
        assert backoff2 == 4.0
        assert backoff3 == 8.0

    def test_record_error_max_backoff(self):
        """Test backoff caps at max_backoff."""
        limiter = RateLimiter(backoff_base=2.0, max_backoff=10.0)
        
        # Record many errors to exceed max
        for _ in range(10):
            backoff = limiter.record_error()
        
        assert backoff == 10.0

    def test_reset_errors(self):
        """Test error counter reset."""
        limiter = RateLimiter()
        
        limiter.record_error()
        limiter.record_error()
        assert limiter._consecutive_errors == 2
        
        limiter.reset_errors()
        assert limiter._consecutive_errors == 0
        assert limiter._last_error_time is None

    def test_record_call_resets_errors(self):
        """Test successful call resets error counter."""
        limiter = RateLimiter()
        
        limiter.record_error()
        assert limiter._consecutive_errors == 1
        
        limiter.record_call()
        assert limiter._consecutive_errors == 0


class TestWithRateLimiting:
    """Test with_rate_limiting decorator."""

    def test_successful_call(self):
        """Test decorator allows successful calls."""
        # Reset global limiter by creating new one
        from the_alchemiser.shared.utils import api_helpers
        api_helpers._rate_limiter = RateLimiter(calls_per_minute=10)
        
        @with_rate_limiting
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"

    def test_rate_limit_exceeded(self):
        """Test decorator raises RateLimitError when limit exceeded."""
        from the_alchemiser.shared.utils import api_helpers
        api_helpers._rate_limiter = RateLimiter(calls_per_minute=2)
        
        @with_rate_limiting
        def test_func():
            return "success"
        
        # Make calls up to limit
        test_func()
        test_func()
        
        # Next call should be rate limited
        with pytest.raises(RateLimitError) as exc_info:
            test_func()
        
        assert "Rate limit exceeded" in str(exc_info.value)

    def test_api_rate_limit_error_detected(self):
        """Test decorator detects API rate limit errors."""
        from the_alchemiser.shared.utils import api_helpers
        api_helpers._rate_limiter = RateLimiter(calls_per_minute=100)
        
        @with_rate_limiting
        def test_func():
            raise Exception("429 Too Many Requests - rate limit exceeded")
        
        with pytest.raises(RateLimitError) as exc_info:
            test_func()
        
        assert "API rate limit error" in str(exc_info.value)

    def test_non_rate_limit_error_propagated(self):
        """Test decorator propagates non-rate-limit errors."""
        from the_alchemiser.shared.utils import api_helpers
        api_helpers._rate_limiter = RateLimiter(calls_per_minute=100)
        
        @with_rate_limiting
        def test_func():
            raise ValueError("Some other error")
        
        with pytest.raises(ValueError):
            test_func()


class TestWithTimeout:
    """Test with_timeout decorator."""

    def test_successful_call(self):
        """Test decorator allows successful calls."""
        @with_timeout(5.0)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"

    def test_timeout_error_detected(self):
        """Test decorator detects timeout errors."""
        @with_timeout(5.0)
        def test_func():
            raise Exception("Connection timed out")
        
        with pytest.raises(TradingClientError) as exc_info:
            test_func()
        
        assert "timed out" in str(exc_info.value).lower()

    def test_non_timeout_error_propagated(self):
        """Test decorator propagates non-timeout errors."""
        @with_timeout(5.0)
        def test_func():
            raise ValueError("Some other error")
        
        with pytest.raises(ValueError):
            test_func()

    def test_decorator_with_args(self):
        """Test decorator works with function arguments."""
        @with_timeout(5.0)
        def test_func(a, b):
            return a + b
        
        result = test_func(2, 3)
        assert result == 5

    def test_decorator_with_kwargs(self):
        """Test decorator works with keyword arguments."""
        @with_timeout(5.0)
        def test_func(a, b=10):
            return a + b
        
        result = test_func(2, b=5)
        assert result == 7
