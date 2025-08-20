#!/usr/bin/env python3
"""
Error Recovery and Resilience Framework for The Alchemiser Trading System.

This module implements Phase 2 of the error handling enhancement plan:
- Automatic Error Recovery strategies
- Circuit Breaker patterns for preventing cascading failures
- Smart Retry mechanisms with multiple strategies
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from .handler import EnhancedAlchemiserError, ErrorSeverity
from .exceptions import (
    MarketDataError,
    OrderExecutionError,
    RateLimitError,
    TradingClientError,
)

F = TypeVar("F", bound=Callable[..., Any])


class RecoveryResult:
    """Result of an error recovery attempt."""

    def __init__(
        self,
        success: bool,
        message: str,
        recovered_data: Any = None,
        retry_recommended: bool = False,
        retry_delay: float = 0.0,
    ):
        self.success = success
        self.message = message
        self.recovered_data = recovered_data
        self.retry_recommended = retry_recommended
        self.retry_delay = retry_delay
        self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert recovery result to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "recovered_data": self.recovered_data,
            "retry_recommended": self.retry_recommended,
            "retry_delay": self.retry_delay,
            "timestamp": self.timestamp.isoformat(),
        }


class ErrorRecoveryStrategy(ABC):
    """Abstract base class for error recovery strategies."""

    @abstractmethod
    def can_recover(self, error: EnhancedAlchemiserError) -> bool:
        """Check if this strategy can recover from the given error."""
        pass

    @abstractmethod
    def recover(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Attempt to recover from the error."""
        pass

    def get_strategy_name(self) -> str:
        """Get the name of this recovery strategy."""
        return self.__class__.__name__


class TradingErrorRecovery(ErrorRecoveryStrategy):
    """Recovery strategies for trading-related errors."""

    def can_recover(self, error: EnhancedAlchemiserError) -> bool:
        """Check if we can recover from trading errors."""
        # Check for original exception types
        if isinstance(error, OrderExecutionError | RateLimitError | TradingClientError):
            return True

        # Check for enhanced error types by class name and attributes
        error_type = error.__class__.__name__
        if error_type == "EnhancedTradingError":
            return True

        # Check if it has trading-related attributes
        trading_attrs = ["symbol", "order_id", "quantity", "price"]
        return any(hasattr(error, attr) for attr in trading_attrs)

    def recover(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Attempt to recover from trading errors."""
        # Handle enhanced trading errors by examining their attributes and message
        error_type = error.__class__.__name__
        error_message = str(error).lower()

        if isinstance(error, RateLimitError) or "rate limit" in error_message:
            return self._handle_rate_limit(error)
        elif isinstance(error, OrderExecutionError) or error_type == "EnhancedTradingError":
            return self._handle_order_failure(error)
        elif isinstance(error, TradingClientError) or hasattr(error, "symbol"):
            return self._handle_client_error(error)

        return RecoveryResult(
            success=False,
            message=f"No recovery strategy for {type(error).__name__}",
        )

    def _handle_rate_limit(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Handle rate limit errors with appropriate delays."""
        retry_delay = getattr(error, "retry_after", None) or 60.0

        return RecoveryResult(
            success=True,
            message=f"Rate limit recovery: waiting {retry_delay}s",
            retry_recommended=True,
            retry_delay=retry_delay,
        )

    def _handle_order_failure(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Handle order execution failures."""
        error_message = str(error).lower()

        # Check if it's a temporary failure
        if "temporarily unavailable" in error_message or "temporary" in error_message:
            return RecoveryResult(
                success=True,
                message="Temporary order failure - retry recommended",
                retry_recommended=True,
                retry_delay=30.0,
            )

        # Check if it's insufficient funds - can't automatically recover
        if "insufficient" in error_message:
            return RecoveryResult(
                success=False,
                message="Insufficient funds - manual intervention required",
            )

        # Default retry for other order failures (including enhanced trading errors)
        retry_delay = 5.0
        if hasattr(error, "get_retry_delay"):
            retry_delay = error.get_retry_delay()

        return RecoveryResult(
            success=True,
            message="Order failure - retry with exponential backoff",
            retry_recommended=True,
            retry_delay=retry_delay,
        )

    def _handle_client_error(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Handle general trading client errors."""
        return RecoveryResult(
            success=True,
            message="Trading client error - retry recommended",
            retry_recommended=True,
            retry_delay=10.0,
        )


class DataErrorRecovery(ErrorRecoveryStrategy):
    """Recovery strategies for data-related errors."""

    def can_recover(self, error: EnhancedAlchemiserError) -> bool:
        """Check if we can recover from data errors."""
        # Check for original exception types
        if isinstance(error, MarketDataError):
            return True

        # Check for enhanced error types by class name and attributes
        error_type = error.__class__.__name__
        if error_type == "EnhancedDataError":
            return True

        # Check if it has data-related attributes
        data_attrs = ["data_source", "data_type", "symbol"]
        return any(hasattr(error, attr) for attr in data_attrs)

    def recover(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Attempt to recover from data errors."""
        # Handle enhanced data errors and original market data errors
        error_type = error.__class__.__name__

        if isinstance(error, MarketDataError) or error_type == "EnhancedDataError":
            return self._handle_market_data_failure(error)

        return RecoveryResult(
            success=False,
            message=f"No recovery strategy for {type(error).__name__}",
        )

    def _handle_market_data_failure(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Handle market data failures."""
        error_message = str(error).lower()

        # Try alternative data source or cached data
        if "connection" in error_message:
            return RecoveryResult(
                success=True,
                message="Network issue - retry with backoff",
                retry_recommended=True,
                retry_delay=15.0,
            )

        return RecoveryResult(
            success=True,
            message="Market data error - retry recommended",
            retry_recommended=True,
            retry_delay=5.0,
        )


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Blocking calls
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerOpenError(EnhancedAlchemiserError):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str):
        super().__init__(message, severity=ErrorSeverity.HIGH)
        self.circuit_name = circuit_name


class CircuitBreaker:
    """Circuit breaker for error rate protection."""

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED
        self.logger = logging.getLogger(__name__)

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN", self.name)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.logger.info(f"Circuit breaker {self.name} CLOSED - recovery successful")

    def _on_failure(self) -> None:
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"Circuit breaker {self.name} OPENED after {self.failure_count} failures"
            )

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.logger.info(f"Circuit breaker {self.name} manually reset")


class RetryStrategy(ABC):
    """Abstract base class for retry strategies."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay for given attempt number."""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff retry strategy."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, factor: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.factor = factor

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.base_delay * (self.factor**attempt)
        return min(delay, self.max_delay)


class LinearBackoffStrategy(RetryStrategy):
    """Linear backoff retry strategy."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """Calculate linear backoff delay."""
        delay = self.base_delay * (attempt + 1)
        return min(delay, self.max_delay)


class FixedIntervalStrategy(RetryStrategy):
    """Fixed interval retry strategy."""

    def __init__(self, delay: float = 5.0):
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        """Return fixed delay."""
        return self.delay


class FibonacciBackoffStrategy(RetryStrategy):
    """Fibonacci backoff retry strategy."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """Calculate Fibonacci backoff delay."""
        fib = self._fibonacci(attempt + 1)
        delay = self.base_delay * fib
        return min(delay, self.max_delay)

    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


class SmartRetryManager:
    """Intelligent retry management with multiple strategies."""

    def __init__(self) -> None:
        self.strategies = {
            "exponential": ExponentialBackoffStrategy(),
            "linear": LinearBackoffStrategy(),
            "fixed": FixedIntervalStrategy(),
            "fibonacci": FibonacciBackoffStrategy(),
        }
        self.logger = logging.getLogger(__name__)

    def retry_with_strategy(
        self,
        func: Callable[..., Any],
        strategy: str = "exponential",
        max_retries: int = 3,
        exceptions: tuple[type[Exception], ...] = (Exception,),
        jitter: bool = True,
        recovery_strategies: list[ErrorRecoveryStrategy] | None = None,
    ) -> Any:
        """Execute function with smart retry strategy."""
        if strategy not in self.strategies:
            raise ValueError(f"Unknown retry strategy: {strategy}")

        retry_strategy = self.strategies[strategy]
        recovery_strategies = recovery_strategies or []

        for attempt in range(max_retries + 1):
            try:
                return func()
            except exceptions as e:
                if attempt == max_retries:
                    raise

                # Try recovery strategies first
                if isinstance(e, EnhancedAlchemiserError):
                    for recovery_strategy in recovery_strategies:
                        if recovery_strategy.can_recover(e):
                            recovery_result = recovery_strategy.recover(e)
                            if recovery_result.success and recovery_result.retry_recommended:
                                delay = recovery_result.retry_delay
                                break
                    else:
                        delay = retry_strategy.get_delay(attempt)
                else:
                    delay = retry_strategy.get_delay(attempt)

                # Add jitter if requested
                if jitter:
                    jitter_factor = 0.5 + random.random() * 0.5  # ±50% jitter
                    delay *= jitter_factor

                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                time.sleep(delay)

    def add_strategy(self, name: str, strategy: RetryStrategy) -> None:
        """Add a custom retry strategy."""
        self.strategies[name] = strategy


class ErrorRecoveryManager:
    """Central manager for error recovery operations."""

    def __init__(self) -> None:
        self.recovery_strategies: list[ErrorRecoveryStrategy] = [
            TradingErrorRecovery(),
            DataErrorRecovery(),
        ]
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_manager = SmartRetryManager()
        self.recovery_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"attempts": 0, "successes": 0, "failures": 0}
        )
        self.logger = logging.getLogger(__name__)

    def recover_from_error(self, error: EnhancedAlchemiserError) -> RecoveryResult:
        """Attempt to recover from an error using available strategies."""
        strategy_name = "unknown"

        for strategy in self.recovery_strategies:
            if strategy.can_recover(error):
                strategy_name = strategy.get_strategy_name()
                self.recovery_stats[strategy_name]["attempts"] += 1

                try:
                    result = strategy.recover(error)
                    if result.success:
                        self.recovery_stats[strategy_name]["successes"] += 1
                    else:
                        self.recovery_stats[strategy_name]["failures"] += 1

                    self.logger.info(f"Recovery attempt with {strategy_name}: {result.message}")
                    return result

                except Exception as recovery_error:
                    self.recovery_stats[strategy_name]["failures"] += 1
                    self.logger.error(f"Recovery strategy {strategy_name} failed: {recovery_error}")

        return RecoveryResult(
            success=False,
            message=f"No recovery strategy available for {type(error).__name__}",
        )

    def get_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
            )
        return self.circuit_breakers[name]

    def execute_with_resilience(
        self,
        func: Callable[..., Any],
        circuit_breaker_name: str | None = None,
        retry_strategy: str = "exponential",
        max_retries: int = 3,
        exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> Any:
        """Execute function with full resilience features."""

        def protected_func() -> Any:
            if circuit_breaker_name:
                circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)
                return circuit_breaker.call(func)
            else:
                return func()

        return self.retry_manager.retry_with_strategy(
            func=protected_func,
            strategy=retry_strategy,
            max_retries=max_retries,
            exceptions=exceptions,
            recovery_strategies=self.recovery_strategies,
        )

    def add_recovery_strategy(self, strategy: ErrorRecoveryStrategy) -> None:
        """Add a custom recovery strategy."""
        self.recovery_strategies.append(strategy)

    def get_recovery_statistics(self) -> dict[str, dict[str, Any]]:
        """Get recovery statistics for monitoring."""
        return dict(self.recovery_stats)

    def reset_circuit_breaker(self, name: str) -> None:
        """Manually reset a circuit breaker."""
        if name in self.circuit_breakers:
            self.circuit_breakers[name].reset()
        else:
            raise ValueError(f"Circuit breaker '{name}' not found")


# Global recovery manager instance
_recovery_manager = ErrorRecoveryManager()


def get_recovery_manager() -> ErrorRecoveryManager:
    """Get the global recovery manager instance."""
    return _recovery_manager


def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> Callable[[F], F]:
    """Decorator to add circuit breaker protection to a function."""

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            circuit_breaker = _recovery_manager.get_circuit_breaker(
                name, failure_threshold, recovery_timeout
            )
            return circuit_breaker.call(func, *args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def with_retry(
    strategy: str = "exponential",
    max_retries: int = 3,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator to add retry capability to a function."""

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return _recovery_manager.retry_manager.retry_with_strategy(
                lambda: func(*args, **kwargs),
                strategy=strategy,
                max_retries=max_retries,
                exceptions=exceptions,
                recovery_strategies=_recovery_manager.recovery_strategies,
            )

        return wrapper  # type: ignore[return-value]

    return decorator


def with_resilience(
    circuit_breaker_name: str | None = None,
    retry_strategy: str = "exponential",
    max_retries: int = 3,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator to add full resilience features to a function."""

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return _recovery_manager.execute_with_resilience(
                lambda: func(*args, **kwargs),
                circuit_breaker_name=circuit_breaker_name,
                retry_strategy=retry_strategy,
                max_retries=max_retries,
                exceptions=exceptions,
            )

        return wrapper  # type: ignore[return-value]

    return decorator
