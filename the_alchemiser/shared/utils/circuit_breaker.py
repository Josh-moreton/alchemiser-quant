"""Business Unit: shared | Status: current.

Circuit Breaker Pattern for WebSocket Connections.

Prevents rapid reconnection attempts that can overwhelm the Alpaca API
and cause connection limit exceeded errors.
"""

import time
from enum import Enum
from typing import NamedTuple

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, connections allowed
    OPEN = "open"  # Circuit is open, connections blocked
    HALF_OPEN = "half_open"  # Testing phase, limited connections allowed


class CircuitBreakerConfig(NamedTuple):
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening circuit
    timeout_seconds: float = 60.0  # Time to wait before trying half-open
    success_threshold: int = 3  # Successful attempts needed to close circuit


class ConnectionCircuitBreaker:
    """Circuit breaker for WebSocket connections.

    Prevents rapid reconnection attempts that can cause connection
    limit exceeded errors by implementing a circuit breaker pattern.
    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        """Initialize the circuit breaker.

        Args:
            config: Circuit breaker configuration

        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self.last_attempt_time: float = 0

        logger.info(f"🔧 Circuit breaker initialized: {self.config}")

    def can_attempt_connection(self) -> bool:
        """Check if a connection attempt is allowed.

        Returns:
            True if connection attempt is allowed, False otherwise

        """
        current_time = time.time()

        # Prevent too frequent attempts regardless of state
        if current_time - self.last_attempt_time < 1.0:
            logger.debug("🔧 Connection attempt rate-limited")
            return False

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and current_time - self.last_failure_time > self.config.timeout_seconds
            ):
                self._transition_to_half_open()
                return True
            logger.info("🔧 Circuit breaker OPEN - blocking connection attempt")
            return False

        # HALF_OPEN state
        return True

    def record_success(self) -> None:
        """Record a successful connection attempt."""
        self.last_attempt_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"🔧 Circuit breaker success {self.success_count}/{self.config.success_threshold}"
            )

            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on successful connection in closed state
            self.failure_count = 0

    def record_failure(self, error_msg: str = "") -> None:
        """Record a failed connection attempt.

        Args:
            error_msg: Optional error message for logging

        """
        self.last_attempt_time = time.time()
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            logger.warning(
                f"🔧 Circuit breaker failure {self.failure_count}/{self.config.failure_threshold}: {error_msg}"
            )

            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()

        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(f"🔧 Circuit breaker half-open test failed: {error_msg}")
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.success_count = 0
        logger.warning(
            f"🔧 Circuit breaker OPENED - blocking connections for {self.config.timeout_seconds}s"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info("🔧 Circuit breaker HALF_OPEN - testing connection")

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("🔧 Circuit breaker CLOSED - normal operation resumed")

    def get_state_info(self) -> dict[str, str | int | float]:
        """Get current circuit breaker state information.

        Returns:
            Dictionary with state information

        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.config.failure_threshold,
            "success_threshold": self.config.success_threshold,
            "timeout_seconds": self.config.timeout_seconds,
            "last_failure_time": self.last_failure_time or 0,
            "last_attempt_time": self.last_attempt_time,
        }

    def reset(self) -> None:
        """Reset the circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_attempt_time = 0
        logger.info("🔧 Circuit breaker reset to initial state")
