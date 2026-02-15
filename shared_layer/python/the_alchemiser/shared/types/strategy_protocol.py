"""Business Unit: shared | Status: current.

Strategy engine protocol definition.

Defines the interface that strategy engines must implement.

Protocol Version: 1.0.0

This protocol defines the core contract for strategy engines in the trading system.
Implementations should:
- Generate signals based on market data analysis
- Validate signals before execution
- Handle timezone-aware timestamps (UTC)
- Support idempotent operations for event replay
- Be thread-safe for concurrent execution

Evolution Strategy:
- Breaking changes require major version bump
- New optional methods/parameters require minor version bump
- Documentation updates require patch version bump

Note: Initialization is not part of the protocol contract. Implementations
may define their own __init__ signatures with required dependencies.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from the_alchemiser.shared.schemas.strategy_signal import StrategySignal


@runtime_checkable
class StrategyEngine(Protocol):
    """Protocol for strategy engine implementations.

    This protocol defines the interface that all strategy engines must implement
    to participate in the trading system's event-driven architecture.

    Thread Safety:
        Implementations should be thread-safe as generate_signals may be called
        concurrently for different timestamps.

    Idempotency:
        generate_signals should be idempotent - calling it multiple times with
        the same timestamp should produce equivalent results (accounting for
        market data updates).

    Initialization:
        Implementations define their own __init__ signatures. Common pattern:
        ```python
        def __init__(self, market_data_port: MarketDataPort, **kwargs) -> None:
            ...
        ```

    Examples:
        >>> class MyStrategy:
        ...     def __init__(self, market_data_port: MarketDataPort) -> None:
        ...         self.market_data = market_data_port
        ...
        ...     def generate_signals(self, timestamp: datetime) -> list[StrategySignal]:
        ...         # Ensure timestamp is timezone-aware
        ...         if timestamp.tzinfo is None:
        ...             raise ValueError("Timestamp must be timezone-aware (UTC)")
        ...         return [StrategySignal(symbol="SPY", action="BUY", timestamp=timestamp)]
        ...
        ...     def validate_signals(self, signals: list[StrategySignal]) -> None:
        ...         if not signals:
        ...             raise ValueError("Must generate at least one signal")
        ...         for sig in signals:
        ...             if not sig.symbol:
        ...                 raise ValueError("Signal must have a symbol")

    """

    def generate_signals(self, timestamp: datetime) -> list[StrategySignal]:
        """Generate strategy signals for the given timestamp.

        This method analyzes market conditions at the specified timestamp and
        produces trading signals (BUY/SELL/HOLD) with target allocations.

        Args:
            timestamp: Timezone-aware datetime (UTC) for signal generation.
                      Must include tzinfo (e.g., datetime.now(timezone.utc)).
                      Naive datetime objects will cause undefined behavior.

        Returns:
            List of StrategySignal objects representing trading recommendations.
            May return empty list if no actionable signals are generated.
            Signals should have valid symbols, actions, and timestamps.

        Raises:
            ValueError: If timestamp is naive (missing timezone info)
            ConfigurationError: If strategy configuration is invalid
            StrategyExecutionError: If signal generation fails due to errors
            DataProviderError: If required market data is unavailable

        Thread Safety:
            This method should be thread-safe and may be called concurrently.

        Idempotency:
            Calling this method multiple times with the same timestamp should
            produce equivalent results (modulo market data updates).

        Examples:
            >>> from datetime import datetime, timezone
            >>> engine = MyStrategyEngine(market_data_port)
            >>> ts = datetime.now(timezone.utc)
            >>> signals = engine.generate_signals(ts)
            >>> assert all(isinstance(s, StrategySignal) for s in signals)
            >>> assert all(s.timestamp.tzinfo is not None for s in signals)

        Note:
            Implementations should validate timestamp timezone and raise
            ValueError if a naive datetime is provided.

        """
        ...

    def validate_signals(self, signals: list[StrategySignal]) -> None:
        """Validate generated signals before execution.

        Performs sanity checks on signals to ensure they meet minimum
        requirements for execution. This is a defensive check to catch
        bugs in signal generation logic.

        Args:
            signals: List of StrategySignal objects to validate

        Raises:
            ValueError: If signals fail validation. Common validation failures:
                       - Empty signal list (if strategy requires signals)
                       - Signal missing required fields (symbol, action, timestamp)
                       - Invalid action (not in BUY/SELL/HOLD)
                       - Invalid target_allocation (negative or > 1.0)
                       - Naive timestamp in signal
            TypeError: If signals is not a list or contains non-StrategySignal objects
            ConfigurationError: If validation rules are misconfigured

        Thread Safety:
            This method should be thread-safe and may be called concurrently.

        Examples:
            >>> signals = [
            ...     StrategySignal(symbol="SPY", action="BUY", timestamp=datetime.now(timezone.utc)),
            ...     StrategySignal(symbol="QQQ", action="HOLD", timestamp=datetime.now(timezone.utc))
            ... ]
            >>> engine.validate_signals(signals)  # Should not raise
            >>>
            >>> bad_signals = [StrategySignal(symbol="", action="INVALID", timestamp=None)]
            >>> engine.validate_signals(bad_signals)  # Raises ValueError

        Note:
            Implementations should define what constitutes "valid" signals
            based on their strategy requirements. Validation should be strict
            to catch errors early.

        """
        ...
