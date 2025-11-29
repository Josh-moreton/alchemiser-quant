"""Business Unit: shared | Status: current.

Circuit Breaker Pattern Implementation for API Resilience.

Prevents cascading failures by temporarily disabling calls to a failing service.
The circuit breaker has three states:
- CLOSED: Normal operation, requests pass through
- OPEN: Requests fail immediately without calling the service
- HALF_OPEN: Limited requests allowed to test if service recovered

This is critical for live trading to prevent runaway execution during Alpaca outages.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar

from the_alchemiser.shared.errors.exceptions import TradingClientError
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast, not calling service
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(TradingClientError):
    """Raised when circuit breaker is open and blocking requests."""

    def __init__(
        self,
        message: str,
        circuit_name: str,
        state: CircuitState,
        failure_count: int,
        time_until_reset: float | None = None,
    ) -> None:
        """Initialize circuit breaker error.

        Args:
            message: Error message
            circuit_name: Name of the circuit breaker
            state: Current circuit state
            failure_count: Number of consecutive failures
            time_until_reset: Seconds until circuit might reset (if OPEN)

        """
        super().__init__(message)
        self.circuit_name = circuit_name
        self.state = state
        self.failure_count = failure_count
        self.time_until_reset = time_until_reset
        self.context["circuit_name"] = circuit_name
        self.context["circuit_state"] = state.value
        self.context["failure_count"] = failure_count
        if time_until_reset is not None:
            self.context["time_until_reset"] = time_until_reset


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior.

    Attributes:
        failure_threshold: Number of failures to trip the circuit
        success_threshold: Number of successes in HALF_OPEN to close circuit
        timeout_seconds: How long circuit stays OPEN before testing recovery
        half_open_max_calls: Max concurrent calls allowed in HALF_OPEN state

    """

    failure_threshold: int = 3
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 1


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring.

    Attributes:
        state: Current circuit state
        failure_count: Consecutive failure count
        success_count: Consecutive success count in HALF_OPEN
        last_failure_time: Timestamp of last failure
        total_failures: Total failures since creation
        total_successes: Total successes since creation
        total_rejections: Total requests rejected by open circuit

    """

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    total_failures: int = 0
    total_successes: int = 0
    total_rejections: int = 0


class CircuitBreaker:
    """Thread-safe circuit breaker for API call protection.

    Usage:
        breaker = CircuitBreaker("alpaca_api")

        try:
            result = breaker.call(lambda: api.place_order(...))
        except CircuitBreakerError as e:
            # Circuit is open, handle gracefully
            logger.error(f"API unavailable: {e}")

    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            name: Identifier for this circuit (for logging/monitoring)
            config: Configuration options (uses defaults if None)

        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._lock = threading.RLock()
        self._stats = CircuitBreakerStats()
        self._last_state_change = datetime.now(UTC)
        self._half_open_calls = 0

        logger.info(
            "Circuit breaker initialized",
            circuit_name=name,
            failure_threshold=self.config.failure_threshold,
            timeout_seconds=self.config.timeout_seconds,
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state (may transition from OPEN to HALF_OPEN)."""
        with self._lock:
            self._check_timeout_transition()
            return self._stats.state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get current statistics."""
        with self._lock:
            return CircuitBreakerStats(
                state=self._stats.state,
                failure_count=self._stats.failure_count,
                success_count=self._stats.success_count,
                last_failure_time=self._stats.last_failure_time,
                total_failures=self._stats.total_failures,
                total_successes=self._stats.total_successes,
                total_rejections=self._stats.total_rejections,
            )

    def _check_timeout_transition(self) -> None:
        """Check if OPEN circuit should transition to HALF_OPEN."""
        if self._stats.state != CircuitState.OPEN:
            return

        elapsed = (datetime.now(UTC) - self._last_state_change).total_seconds()
        if elapsed >= self.config.timeout_seconds:
            self._transition_to(CircuitState.HALF_OPEN)
            self._half_open_calls = 0

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state with logging."""
        old_state = self._stats.state
        self._stats.state = new_state
        self._last_state_change = datetime.now(UTC)

        logger.info(
            "Circuit breaker state transition",
            circuit_name=self.name,
            from_state=old_state.value,
            to_state=new_state.value,
            failure_count=self._stats.failure_count,
            success_count=self._stats.success_count,
        )

    def _record_success(self) -> None:
        """Record a successful call."""
        self._stats.total_successes += 1

        if self._stats.state == CircuitState.HALF_OPEN:
            self._stats.success_count += 1
            if self._stats.success_count >= self.config.success_threshold:
                # Service recovered, close circuit
                self._stats.failure_count = 0
                self._stats.success_count = 0
                self._transition_to(CircuitState.CLOSED)
        elif self._stats.state == CircuitState.CLOSED:
            # Reset failure count on success
            self._stats.failure_count = 0

    def _record_failure(self, error: Exception) -> None:
        """Record a failed call."""
        self._stats.total_failures += 1
        self._stats.failure_count += 1
        self._stats.last_failure_time = datetime.now(UTC)

        logger.warning(
            "Circuit breaker recorded failure",
            circuit_name=self.name,
            failure_count=self._stats.failure_count,
            threshold=self.config.failure_threshold,
            error_type=type(error).__name__,
            error=str(error),
        )

        if self._stats.state == CircuitState.HALF_OPEN:
            # Failure in HALF_OPEN means service still failing
            self._stats.success_count = 0
            self._transition_to(CircuitState.OPEN)
        elif self._stats.state == CircuitState.CLOSED:
            if self._stats.failure_count >= self.config.failure_threshold:
                # Threshold reached, open circuit
                self._transition_to(CircuitState.OPEN)

    def _can_execute(self) -> bool:
        """Check if a call can be executed."""
        self._check_timeout_transition()

        if self._stats.state == CircuitState.CLOSED:
            return True

        if self._stats.state == CircuitState.OPEN:
            return False

        # HALF_OPEN: allow limited calls
        if self._half_open_calls < self.config.half_open_max_calls:
            self._half_open_calls += 1
            return True

        return False

    def _time_until_reset(self) -> float | None:
        """Calculate time until circuit might reset from OPEN state."""
        if self._stats.state != CircuitState.OPEN:
            return None

        elapsed = (datetime.now(UTC) - self._last_state_change).total_seconds()
        remaining = self.config.timeout_seconds - elapsed
        return max(0.0, remaining)

    def call(self, func: Callable[[], T], *args: Any, **kwargs: Any) -> T:  # noqa: ANN401
        """Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerError: If circuit is OPEN and blocking calls
            Exception: Any exception raised by the function

        """
        with self._lock:
            if not self._can_execute():
                self._stats.total_rejections += 1
                time_until_reset = self._time_until_reset()

                logger.warning(
                    "Circuit breaker rejecting call",
                    circuit_name=self.name,
                    state=self._stats.state.value,
                    failure_count=self._stats.failure_count,
                    time_until_reset=time_until_reset,
                )

                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is {self._stats.state.value}. "
                    f"Service calls are temporarily blocked after {self._stats.failure_count} failures.",
                    circuit_name=self.name,
                    state=self._stats.state,
                    failure_count=self._stats.failure_count,
                    time_until_reset=time_until_reset,
                )

        # Execute outside lock to allow concurrent calls
        try:
            result = func(*args, **kwargs)
            with self._lock:
                self._record_success()
            return result
        except Exception as e:
            with self._lock:
                self._record_failure(e)
            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state.

        Use with caution - only call this if you have reason to believe
        the service has recovered.
        """
        with self._lock:
            self._stats.failure_count = 0
            self._stats.success_count = 0
            self._half_open_calls = 0
            self._transition_to(CircuitState.CLOSED)

            logger.info(
                "Circuit breaker manually reset",
                circuit_name=self.name,
            )


# Global circuit breakers for shared services
_circuit_breakers: dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    config: CircuitBreakerConfig | None = None,
) -> CircuitBreaker:
    """Get or create a named circuit breaker.

    This provides singleton-like behavior for circuit breakers,
    ensuring the same breaker is used across all callers.

    Args:
        name: Circuit breaker name (e.g., "alpaca_trading", "alpaca_data")
        config: Configuration (only used on first creation)

    Returns:
        CircuitBreaker instance

    """
    with _breakers_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name, config)
        return _circuit_breakers[name]


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers to CLOSED state.

    Useful for testing or after confirmed service recovery.
    """
    with _breakers_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()


def get_all_circuit_breaker_stats() -> dict[str, CircuitBreakerStats]:
    """Get stats for all circuit breakers."""
    with _breakers_lock:
        return {name: breaker.stats for name, breaker in _circuit_breakers.items()}
